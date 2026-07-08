import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../config/theme.dart';
import '../../../core/errors/exceptions.dart';
import '../../../core/utils/validators.dart';
import '../../../core/widgets/primary_button.dart';
import 'candidatures_providers.dart';

/// Confirmation du mécanisme 3 (fallback OTP) pour une candidature qui vient
/// d'être créée : ni le CNIB ni la date de naissance ne figuraient dans le
/// résultat publié (docs/PROFIL_CANDIDAT_UNIFIE.md § 5).
class CandidatureOtpScreen extends ConsumerStatefulWidget {
  const CandidatureOtpScreen({
    required this.candidatureId,
    this.codeDebug,
    super.key,
  });

  final String candidatureId;
  final String? codeDebug;

  @override
  ConsumerState<CandidatureOtpScreen> createState() =>
      _CandidatureOtpScreenState();
}

class _CandidatureOtpScreenState extends ConsumerState<CandidatureOtpScreen> {
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
    ref.read(ajoutCandidatureProvider.notifier).confirmerOtp(
          candidatureId: widget.candidatureId,
          code: _codeController.text.trim(),
        );
  }

  @override
  Widget build(BuildContext context) {
    final confirmation = ref.watch(ajoutCandidatureProvider);

    ref.listen(ajoutCandidatureProvider, (previous, next) {
      if (next != null && next.hasValue) {
        ref.read(ajoutCandidatureProvider.notifier).reinitialiser();
        Navigator.of(context)
          ..pop()
          ..pop();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Candidature confirmée.')),
        );
      }
    });

    return Scaffold(
      appBar: AppBar(title: const Text('Confirmer la candidature')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Ce récépissé ne peut pas être vérifié automatiquement. '
                  'Un code vous a été envoyé par SMS : saisissez-le pour '
                  'confirmer que cette candidature vous appartient.',
                ),
                if (widget.codeDebug != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    '(mode développement : code pré-rempli)',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
                const SizedBox(height: 20),
                TextFormField(
                  controller: _codeController,
                  keyboardType: TextInputType.number,
                  maxLength: 6,
                  decoration: const InputDecoration(labelText: 'Code reçu'),
                  validator: Validators.codeOtp,
                ),
                if (confirmation != null && confirmation.hasError)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(
                      confirmation.error is AppException
                          ? (confirmation.error! as AppException).message
                          : 'Code invalide ou expiré. Veuillez réessayer.',
                      style: const TextStyle(
                          color: AppColors.erreur, fontSize: 13),
                    ),
                  ),
                const SizedBox(height: 24),
                PrimaryButton(
                  label: 'Confirmer',
                  enCours: confirmation?.isLoading ?? false,
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
