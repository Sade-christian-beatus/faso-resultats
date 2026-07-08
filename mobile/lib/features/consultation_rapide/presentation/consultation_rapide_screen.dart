import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../config/theme.dart';
import '../../../core/errors/failures.dart';
import '../../../core/widgets/empty_view.dart';
import '../../../core/widgets/error_view.dart';
import '../../../core/widgets/loading_indicator.dart';
import '../../../core/widgets/primary_button.dart';
import '../domain/administration.dart';
import '../domain/examen.dart';
import '../domain/resultat.dart';
import 'consultation_providers.dart';
import 'resultat_card.dart';

class ConsultationRapideScreen extends ConsumerStatefulWidget {
  const ConsultationRapideScreen({super.key});

  @override
  ConsumerState<ConsultationRapideScreen> createState() =>
      _ConsultationRapideScreenState();
}

class _ConsultationRapideScreenState
    extends ConsumerState<ConsultationRapideScreen> {
  final _formKey = GlobalKey<FormState>();
  final _numeroPvController = TextEditingController();
  final _juryController = TextEditingController();

  String? _administrationId;
  String? _examenId;

  @override
  void dispose() {
    _numeroPvController.dispose();
    _juryController.dispose();
    super.dispose();
  }

  void _rechercher() {
    if (!_formKey.currentState!.validate() || _examenId == null) return;
    ref.read(rechercheResultatProvider.notifier).rechercher(
          examenId: _examenId!,
          numeroPv: _numeroPvController.text.trim(),
          jury: _juryController.text.trim(),
        );
  }

  @override
  Widget build(BuildContext context) {
    final administrations = ref.watch(administrationsPubliquesProvider);
    final examens = ref.watch(examensPublicsProvider);
    final recherche = ref.watch(rechercheResultatProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Consulter mon résultat')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Administration',
                    style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                  ),
                  const SizedBox(height: 6),
                  administrations.when(
                    loading: () => const _ChampChargement(),
                    error: (erreur, _) => _ChampErreur(
                      onRetry: () =>
                          ref.invalidate(administrationsPubliquesProvider),
                    ),
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
                    error: (erreur, _) => _ChampErreur(
                        onRetry: () => ref.invalidate(examensPublicsProvider)),
                    data: (liste) {
                      final filtres = _administrationId == null
                          ? <Examen>[]
                          : liste
                              .where((e) =>
                                  e.administrationId == _administrationId)
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
                    controller: _numeroPvController,
                    decoration: const InputDecoration(
                        labelText: 'Numéro de récépissé / PV'),
                    validator: (valeur) =>
                        (valeur == null || valeur.trim().isEmpty)
                            ? 'Le numéro de récépissé est obligatoire'
                            : null,
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: _juryController,
                    decoration: const InputDecoration(
                      labelText: 'Jury / centre (optionnel)',
                    ),
                  ),
                  const SizedBox(height: 20),
                  PrimaryButton(
                    label: 'Rechercher',
                    enCours: recherche?.isLoading ?? false,
                    onPressed: _examenId == null ? null : _rechercher,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            _ZoneResultats(recherche: recherche),
          ],
        ),
      ),
    );
  }
}

class _ZoneResultats extends StatelessWidget {
  const _ZoneResultats({required this.recherche});

  final AsyncValue<List<Resultat>>? recherche;

  @override
  Widget build(BuildContext context) {
    if (recherche == null) return const SizedBox.shrink();

    return recherche!.when(
      loading: () => const LoadingIndicator(),
      error: (erreur, _) => ErrorView(
        message: erreur is Failure
            ? erreur.message
            : 'Une erreur est survenue. Veuillez réessayer.',
      ),
      data: (resultats) {
        if (resultats.isEmpty) {
          return const EmptyView(
            message:
                'Aucun résultat trouvé pour ce récépissé. Vérifiez le numéro saisi.',
            icon: Icons.search_off,
          );
        }
        return Column(
          children: resultats.map((r) => ResultatCard(resultat: r)).toList(),
        );
      },
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
  const _ChampErreur({required this.onRetry});

  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const Expanded(
          child: Text(
            'Impossible de charger. Vérifiez votre connexion.',
            style: TextStyle(color: AppColors.erreur, fontSize: 13),
          ),
        ),
        TextButton(onPressed: onRetry, child: const Text('Réessayer')),
      ],
    );
  }
}
