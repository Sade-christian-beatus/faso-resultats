import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../config/routes.dart';
import '../../../core/errors/failures.dart';
import '../../../core/utils/validators.dart';
import '../../../core/widgets/primary_button.dart';
import 'auth_candidat_providers.dart';

class OtpVerifyScreen extends ConsumerStatefulWidget {
  const OtpVerifyScreen({required this.telephone, this.codeDebug, super.key});

  final String telephone;
  final String? codeDebug;

  @override
  ConsumerState<OtpVerifyScreen> createState() => _OtpVerifyScreenState();
}

class _OtpVerifyScreenState extends ConsumerState<OtpVerifyScreen> {
  final _formKey = GlobalKey<FormState>();
  late final _codeController =
      TextEditingController(text: widget.codeDebug ?? '');

  @override
  void dispose() {
    _codeController.dispose();
    super.dispose();
  }

  void _valider() {
    if (!_formKey.currentState!.validate()) return;
    ref.read(otpValidationProvider.notifier).valider(
        telephone: widget.telephone, code: _codeController.text.trim());
  }

  @override
  Widget build(BuildContext context) {
    final validation = ref.watch(otpValidationProvider);

    ref.listen(otpValidationProvider, (previous, next) {
      if (next != null && next.hasValue) {
        // Remplace toute la pile de navigation : impossible de revenir aux
        // écrans d'auth avec le bouton retour une fois connecté.
        context.go(AppRoutes.dashboard);
      }
    });

    return Scaffold(
      appBar: AppBar(title: const Text('Vérification')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Un code à 6 chiffres a été envoyé par SMS au ${widget.telephone}.',
                  style: const TextStyle(fontSize: 15),
                ),
                const SizedBox(height: 20),
                TextFormField(
                  controller: _codeController,
                  keyboardType: TextInputType.number,
                  maxLength: 6,
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 24, letterSpacing: 8),
                  decoration: const InputDecoration(counterText: ''),
                  validator: Validators.codeOtp,
                ),
                if (validation != null && validation.hasError) ...[
                  const SizedBox(height: 8),
                  Text(
                    validation.error is Failure
                        ? (validation.error! as Failure).message
                        : 'Code invalide ou expiré. Veuillez réessayer.',
                    style: const TextStyle(color: Colors.red, fontSize: 13),
                  ),
                ],
                const SizedBox(height: 24),
                PrimaryButton(
                  label: 'Valider',
                  enCours: validation?.isLoading ?? false,
                  onPressed: _valider,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
