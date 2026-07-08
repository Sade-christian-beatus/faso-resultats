import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../config/theme.dart';
import '../../../core/errors/exceptions.dart';
import '../../../core/widgets/primary_button.dart';
import '../../consultation_rapide/domain/administration.dart';
import '../../consultation_rapide/domain/examen.dart';
import '../../consultation_rapide/presentation/consultation_providers.dart';
import '../domain/candidature.dart';
import 'candidature_otp_screen.dart';
import 'candidatures_providers.dart';

/// Ajout d'une candidature (jour 5) : sélection administration → examen →
/// saisie du récépissé, puis vérification via les mécanismes 1/2/3
/// (docs/PROFIL_CANDIDAT_UNIFIE.md § 5). Le formulaire réutilise les
/// providers publics administrations/examens de la consultation rapide —
/// mêmes listes, pas besoin d'une source dédiée.
class AjoutCandidatureScreen extends ConsumerStatefulWidget {
  const AjoutCandidatureScreen({super.key});

  @override
  ConsumerState<AjoutCandidatureScreen> createState() =>
      _AjoutCandidatureScreenState();
}

class _AjoutCandidatureScreenState
    extends ConsumerState<AjoutCandidatureScreen> {
  final _formKey = GlobalKey<FormState>();
  final _numeroRecepisseController = TextEditingController();

  String? _administrationId;
  String? _examenId;

  @override
  void dispose() {
    _numeroRecepisseController.dispose();
    super.dispose();
  }

  void _soumettre() {
    if (!_formKey.currentState!.validate() || _examenId == null) return;
    ref.read(ajoutCandidatureProvider.notifier).creer(
          administrationId: _administrationId!,
          examenId: _examenId!,
          numeroRecepisse: _numeroRecepisseController.text.trim(),
        );
  }

  void _traiterResultat(Candidature candidature) {
    ref.read(ajoutCandidatureProvider.notifier).reinitialiser();
    if (candidature.attenteConfirmationOtp) {
      Navigator.of(context).push(
        MaterialPageRoute<void>(
          builder: (_) => CandidatureOtpScreen(
            candidatureId: candidature.id,
            codeDebug: candidature.codeOtpDebug,
          ),
        ),
      );
      return;
    }
    Navigator.of(context).pop();
    // Un récépissé rejeté (statut REJETE) ne peut jamais arriver ici : le
    // backend renvoie une erreur 422 dans ce cas plutôt qu'une candidature
    // créée (voir create_candidature). Seuls VERIFIE_AUTO et EN_ATTENTE (avec
    // ou sans fallback OTP, déjà traité ci-dessus) sont possibles ici.
    final message = candidature.statutVerification ==
            StatutVerificationCandidature.enAttente
        ? 'Candidature enregistrée. Elle sera vérifiée automatiquement '
            'à la publication des résultats.'
        : 'Candidature vérifiée avec succès.';
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    final administrations = ref.watch(administrationsPubliquesProvider);
    final examens = ref.watch(examensPublicsProvider);
    final ajout = ref.watch(ajoutCandidatureProvider);

    ref.listen(ajoutCandidatureProvider, (previous, next) {
      if (next != null && next.hasValue) _traiterResultat(next.value!);
    });

    return Scaffold(
      appBar: AppBar(title: const Text('Ajouter une candidature')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Administration',
                  style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                ),
                const SizedBox(height: 6),
                administrations.when(
                  loading: () => const _ChampChargement(),
                  error: (erreur, _) => const _ChampErreur(),
                  data: (liste) => _SelecteurAdministration(
                    administrations: liste,
                    valeur: _administrationId,
                    onChanged: (id) {
                      setState(() {
                        _administrationId = id;
                        _examenId = null;
                      });
                    },
                  ),
                ),
                const SizedBox(height: 16),
                const Text('Examen',
                    style:
                        TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                const SizedBox(height: 6),
                examens.when(
                  loading: () => const _ChampChargement(),
                  error: (erreur, _) => const _ChampErreur(),
                  data: (liste) {
                    final filtres = _administrationId == null
                        ? <Examen>[]
                        : liste
                            .where(
                                (e) => e.administrationId == _administrationId)
                            .toList();
                    return _SelecteurExamen(
                      examens: filtres,
                      valeur: _examenId,
                      active: _administrationId != null,
                      onChanged: (id) => setState(() => _examenId = id),
                    );
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _numeroRecepisseController,
                  decoration:
                      const InputDecoration(labelText: 'Numéro de récépissé'),
                  validator: (valeur) =>
                      (valeur == null || valeur.trim().isEmpty)
                          ? 'Le numéro de récépissé est obligatoire'
                          : null,
                ),
                if (ajout != null && ajout.hasError)
                  Padding(
                    padding: const EdgeInsets.only(top: 12),
                    child: Text(
                      ajout.error is AppException
                          ? (ajout.error! as AppException).message
                          : 'Une erreur est survenue. Veuillez réessayer.',
                      style: const TextStyle(
                          color: AppColors.erreur, fontSize: 13),
                    ),
                  ),
                const SizedBox(height: 20),
                PrimaryButton(
                  label: 'Ajouter',
                  enCours: ajout?.isLoading ?? false,
                  onPressed: _examenId == null ? null : _soumettre,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _SelecteurAdministration extends StatelessWidget {
  const _SelecteurAdministration({
    required this.administrations,
    required this.valeur,
    required this.onChanged,
  });

  final List<Administration> administrations;
  final String? valeur;
  final ValueChanged<String?> onChanged;

  @override
  Widget build(BuildContext context) {
    return DropdownButtonFormField<String>(
      initialValue: valeur,
      items: administrations
          .map((a) => DropdownMenuItem(value: a.id, child: Text(a.nomOfficiel)))
          .toList(),
      onChanged: onChanged,
      validator: (v) => v == null ? 'Sélectionnez une administration' : null,
      hint: const Text('Choisir une administration'),
    );
  }
}

class _SelecteurExamen extends StatelessWidget {
  const _SelecteurExamen({
    required this.examens,
    required this.valeur,
    required this.active,
    required this.onChanged,
  });

  final List<Examen> examens;
  final String? valeur;
  final bool active;
  final ValueChanged<String?> onChanged;

  @override
  Widget build(BuildContext context) {
    if (!active) {
      return const InputDecorator(
        decoration: InputDecoration(enabled: false),
        child: Text("Choisissez d'abord une administration"),
      );
    }
    if (examens.isEmpty) {
      return const InputDecorator(
        decoration: InputDecoration(enabled: false),
        child: Text('Aucun examen publié pour cette administration'),
      );
    }
    return DropdownButtonFormField<String>(
      initialValue: valeur,
      items: examens
          .map((e) => DropdownMenuItem(
              value: e.id, child: Text('${e.annee} — ${e.libelle}')))
          .toList(),
      onChanged: onChanged,
      validator: (v) => v == null ? 'Sélectionnez un examen' : null,
      hint: const Text('Choisir un examen'),
    );
  }
}

class _ChampChargement extends StatelessWidget {
  const _ChampChargement();

  @override
  Widget build(BuildContext context) {
    return const SizedBox(
      height: 52,
      child: Center(
        child: SizedBox(
            width: 20,
            height: 20,
            child: CircularProgressIndicator(strokeWidth: 2)),
      ),
    );
  }
}

class _ChampErreur extends StatelessWidget {
  const _ChampErreur();

  @override
  Widget build(BuildContext context) {
    return const Text(
      'Impossible de charger. Vérifiez votre connexion.',
      style: TextStyle(color: AppColors.erreur, fontSize: 13),
    );
  }
}
