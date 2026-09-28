import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../config/theme.dart';
import '../../../core/errors/exceptions.dart';
import '../../../core/utils/date_formatter.dart';
import '../../../core/utils/operateur_detector.dart';
import '../../../core/utils/validators.dart';
import '../../../core/widgets/primary_button.dart';
import 'auth_candidat_providers.dart';
import 'otp_verify_screen.dart';

const _versionConsentementApdp = 'v1';

class AuthCandidatScreen extends ConsumerStatefulWidget {
  const AuthCandidatScreen({super.key});

  @override
  ConsumerState<AuthCandidatScreen> createState() => _AuthCandidatScreenState();
}

class _AuthCandidatScreenState extends ConsumerState<AuthCandidatScreen> {
  bool _ongletInscription = false;
  String? _telephoneEnAttente;

  void _envoyerConnexion(String telephone) {
    _telephoneEnAttente = telephone;
    ref.read(otpEnvoiProvider.notifier).demanderConnexion(telephone);
  }

  void _envoyerInscription({
    required String numeroCnib,
    required String nomComplet,
    required DateTime dateNaissance,
    required String telephone,
  }) {
    _telephoneEnAttente = telephone;
    ref.read(otpEnvoiProvider.notifier).inscrire(
          numeroCnib: numeroCnib,
          nomComplet: nomComplet,
          dateNaissance: dateNaissance,
          telephone: telephone,
          consentementApdpVersion: _versionConsentementApdp,
        );
  }

  @override
  Widget build(BuildContext context) {
    final envoi = ref.watch(otpEnvoiProvider);

    ref.listen(otpEnvoiProvider, (previous, next) {
      final telephone = _telephoneEnAttente;
      if (next != null && next.hasValue && telephone != null) {
        ref.read(otpEnvoiProvider.notifier).reinitialiser();
        Navigator.of(context).push(
          MaterialPageRoute<void>(
            builder: (_) =>
                OtpVerifyScreen(telephone: telephone, codeDebug: next.value),
          ),
        );
      }
    });

    return Scaffold(
      appBar: AppBar(title: const Text('Espace candidat')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _SelecteurOnglet(
                inscriptionActive: _ongletInscription,
                onChanged: (v) => setState(() => _ongletInscription = v),
              ),
              const SizedBox(height: 20),
              if (envoi != null && envoi.hasError)
                Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: Text(
                    envoi.error is AppException
                        ? (envoi.error! as AppException).message
                        : 'Une erreur est survenue. Veuillez réessayer.',
                    style:
                        const TextStyle(color: AppColors.erreur, fontSize: 13),
                  ),
                ),
              if (_ongletInscription)
                _InscriptionForm(
                    enCours: envoi?.isLoading ?? false,
                    onSoumettre: _envoyerInscription)
              else
                _ConnexionForm(
                    enCours: envoi?.isLoading ?? false,
                    onSoumettre: _envoyerConnexion),
            ],
          ),
        ),
      ),
    );
  }
}

class _SelecteurOnglet extends StatelessWidget {
  const _SelecteurOnglet(
      {required this.inscriptionActive, required this.onChanged});

  final bool inscriptionActive;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _Onglet(
            label: 'Connexion',
            actif: !inscriptionActive,
            onTap: () => onChanged(false),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _Onglet(
            label: 'Inscription',
            actif: inscriptionActive,
            onTap: () => onChanged(true),
          ),
        ),
      ],
    );
  }
}

class _Onglet extends StatelessWidget {
  const _Onglet(
      {required this.label, required this.actif, required this.onTap});

  final String label;
  final bool actif;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return OutlinedButton(
      onPressed: onTap,
      style: OutlinedButton.styleFrom(
        backgroundColor: actif ? AppColors.vertFonce : null,
        foregroundColor: actif ? Colors.white : AppColors.vertFonce,
      ),
      child: Text(label),
    );
  }
}

class _ConnexionForm extends StatefulWidget {
  const _ConnexionForm({required this.enCours, required this.onSoumettre});

  final bool enCours;
  final ValueChanged<String> onSoumettre;

  @override
  State<_ConnexionForm> createState() => _ConnexionFormState();
}

class _ConnexionFormState extends State<_ConnexionForm> {
  final _formKey = GlobalKey<FormState>();
  final _telephoneController = TextEditingController();

  @override
  void dispose() {
    _telephoneController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextFormField(
            controller: _telephoneController,
            keyboardType: TextInputType.phone,
            decoration: const InputDecoration(
              labelText: 'Numéro de téléphone',
              hintText: '+22670000000',
            ),
            validator: Validators.telephone,
          ),
          const SizedBox(height: 20),
          PrimaryButton(
            label: 'Recevoir un code',
            enCours: widget.enCours,
            onPressed: () {
              if (!_formKey.currentState!.validate()) return;
              widget.onSoumettre(_telephoneController.text.trim());
            },
          ),
        ],
      ),
    );
  }
}

class _InscriptionForm extends StatefulWidget {
  const _InscriptionForm({required this.enCours, required this.onSoumettre});

  final bool enCours;
  final void Function({
    required String numeroCnib,
    required String nomComplet,
    required DateTime dateNaissance,
    required String telephone,
  }) onSoumettre;

  @override
  State<_InscriptionForm> createState() => _InscriptionFormState();
}

class _InscriptionFormState extends State<_InscriptionForm> {
  final _formKey = GlobalKey<FormState>();
  final _cnibController = TextEditingController();
  final _nomController = TextEditingController();
  final _telephoneController = TextEditingController();
  DateTime? _dateNaissance;
  bool _consentement = false;
  bool _formSoumis = false;

  @override
  void dispose() {
    _cnibController.dispose();
    _nomController.dispose();
    _telephoneController.dispose();
    super.dispose();
  }

  Future<void> _choisirDateNaissance() async {
    final maintenant = DateTime.now();
    final choix = await showDatePicker(
      context: context,
      initialDate: DateTime(maintenant.year - 18),
      firstDate: DateTime(maintenant.year - 100),
      lastDate: maintenant,
    );
    if (choix != null) setState(() => _dateNaissance = choix);
  }

  void _soumettre() {
    setState(() => _formSoumis = true);
    if (!_formKey.currentState!.validate() ||
        _dateNaissance == null ||
        !_consentement) {
      return;
    }
    widget.onSoumettre(
      numeroCnib: _cnibController.text.trim(),
      nomComplet: _nomController.text.trim(),
      dateNaissance: _dateNaissance!,
      telephone: _telephoneController.text.trim(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final telephone = _telephoneController.text.trim();
    final operateur =
        telephone.isEmpty ? null : OperateurDetector.detecter(telephone);

    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextFormField(
            controller: _cnibController,
            decoration: const InputDecoration(labelText: 'Numéro CNIB'),
            validator: Validators.cnib,
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _nomController,
            decoration: const InputDecoration(labelText: 'Nom complet'),
            validator: Validators.nomComplet,
          ),
          const SizedBox(height: 12),
          InkWell(
            onTap: _choisirDateNaissance,
            child: InputDecorator(
              decoration: InputDecoration(
                labelText: 'Date de naissance',
                errorText: (_dateNaissance == null && _formSoumis)
                    ? 'Champ obligatoire'
                    : null,
              ),
              child: Text(
                _dateNaissance == null
                    ? 'Sélectionner'
                    : DateFormatter.pourAffichage(_dateNaissance!),
              ),
            ),
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _telephoneController,
            keyboardType: TextInputType.phone,
            decoration: InputDecoration(
              labelText: 'Numéro de téléphone',
              hintText: '+22670000000',
              helperText:
                  operateur != null && operateur != OperateurTelephone.inconnu
                      ? 'Opérateur détecté : ${_libelleOperateur(operateur)}'
                      : null,
            ),
            validator: Validators.telephone,
            onChanged: (_) => setState(() {}),
          ),
          const SizedBox(height: 12),
          CheckboxListTile(
            value: _consentement,
            onChanged: (v) => setState(() => _consentement = v ?? false),
            controlAffinity: ListTileControlAffinity.leading,
            contentPadding: EdgeInsets.zero,
            title: const Text(
              "J'accepte que Faso Résultats conserve mes données pour créer mon "
              "espace candidat et m'informer de mes résultats.",
              style: TextStyle(fontSize: 13),
            ),
          ),
          if (!_consentement && _formSoumis)
            const Padding(
              padding: EdgeInsets.only(bottom: 8),
              child: Text(
                'Le consentement est nécessaire pour créer votre espace.',
                style: TextStyle(color: AppColors.erreur, fontSize: 12),
              ),
            ),
          const SizedBox(height: 12),
          PrimaryButton(
              label: 'Créer mon espace',
              enCours: widget.enCours,
              onPressed: _soumettre),
        ],
      ),
    );
  }

  String _libelleOperateur(OperateurTelephone operateur) => switch (operateur) {
        OperateurTelephone.orange => 'Orange',
        OperateurTelephone.moov => 'Moov Africa',
        OperateurTelephone.telecel => 'Telecel Faso',
        OperateurTelephone.inconnu => '',
      };
}
