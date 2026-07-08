import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../config/routes.dart';
import '../../../core/errors/exceptions.dart';
import '../../../core/widgets/empty_view.dart';
import '../../../core/widgets/error_view.dart';
import '../../../core/widgets/loading_indicator.dart';
import '../../consultation_rapide/domain/administration.dart';
import '../../consultation_rapide/domain/examen.dart';
import '../../consultation_rapide/presentation/consultation_providers.dart';
import '../domain/candidature.dart';
import 'candidature_card.dart';
import 'candidature_detail_sheet.dart';
import 'candidatures_providers.dart';

class DashboardScreen extends ConsumerStatefulWidget {
  const DashboardScreen({super.key});

  @override
  ConsumerState<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends ConsumerState<DashboardScreen> {
  int? _filtreAnnee;
  StatutVerificationCandidature? _filtreStatut;
  String? _filtreAdministrationId;

  @override
  Widget build(BuildContext context) {
    final candidatures = ref.watch(candidaturesProvider);
    final administrations =
        ref.watch(administrationsPubliquesProvider).valueOrNull ?? [];
    final examens = ref.watch(examensPublicsProvider).valueOrNull ?? [];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Mes candidatures'),
        actions: [
          IconButton(
            icon: const Icon(Icons.person_outline),
            onPressed: () => context.push(AppRoutes.profil),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push(AppRoutes.ajoutCandidature),
        icon: const Icon(Icons.add),
        label: const Text('Ajouter'),
      ),
      body: candidatures.when(
        loading: () => const LoadingIndicator(),
        error: (erreur, _) => ErrorView(
          message: erreur is AppException
              ? erreur.message
              : 'Une erreur est survenue.',
          onRetry: () => ref.read(candidaturesProvider.notifier).rafraichir(),
        ),
        data: (liste) {
          final filtrees = _appliquerFiltres(liste, examens);
          return RefreshIndicator(
            onRefresh: () =>
                ref.read(candidaturesProvider.notifier).rafraichir(),
            child: Column(
              children: [
                _BarreFiltres(
                  administrations: administrations,
                  examens: examens,
                  annee: _filtreAnnee,
                  statut: _filtreStatut,
                  administrationId: _filtreAdministrationId,
                  onChanged: (annee, statut, administrationId) => setState(() {
                    _filtreAnnee = annee;
                    _filtreStatut = statut;
                    _filtreAdministrationId = administrationId;
                  }),
                ),
                Expanded(
                  child: filtrees.isEmpty
                      ? ListView(
                          children: const [
                            SizedBox(height: 80),
                            EmptyView(
                              message: 'Aucune candidature pour le moment.',
                              icon: Icons.folder_open_outlined,
                            ),
                          ],
                        )
                      : ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: filtrees.length,
                          itemBuilder: (context, index) {
                            final candidature = filtrees[index];
                            final administration = _trouver(
                              administrations,
                              candidature.administrationId,
                            );
                            final examen =
                                _trouverExamen(examens, candidature.examenId);
                            return Padding(
                              padding: const EdgeInsets.only(bottom: 12),
                              child: CandidatureCard(
                                candidature: candidature,
                                administration: administration,
                                examen: examen,
                                onTap: () => ouvrirDetailCandidature(
                                  context,
                                  candidature: candidature,
                                  administration: administration,
                                  examen: examen,
                                ),
                                onRetirer: () => _confirmerRetrait(candidature),
                              ),
                            );
                          },
                        ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  List<Candidature> _appliquerFiltres(
      List<Candidature> liste, List<Examen> examens) {
    return liste.where((c) {
      if (_filtreStatut != null && c.statutVerification != _filtreStatut) {
        return false;
      }
      if (_filtreAdministrationId != null &&
          c.administrationId != _filtreAdministrationId) {
        return false;
      }
      if (_filtreAnnee != null) {
        final examen = _trouverExamen(examens, c.examenId);
        if (examen == null || examen.annee != _filtreAnnee) return false;
      }
      return true;
    }).toList();
  }

  Administration? _trouver(List<Administration> liste, String id) {
    for (final a in liste) {
      if (a.id == id) return a;
    }
    return null;
  }

  Examen? _trouverExamen(List<Examen> liste, String id) {
    for (final e in liste) {
      if (e.id == id) return e;
    }
    return null;
  }

  Future<void> _confirmerRetrait(Candidature candidature) async {
    final confirme = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Retirer cette candidature ?'),
        content: Text('Récépissé n° ${candidature.numeroRecepisse}'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Annuler')),
          TextButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Retirer')),
        ],
      ),
    );
    if (confirme ?? false) {
      await ref.read(candidaturesProvider.notifier).retirer(candidature.id);
    }
  }
}

class _BarreFiltres extends StatelessWidget {
  const _BarreFiltres({
    required this.administrations,
    required this.examens,
    required this.annee,
    required this.statut,
    required this.administrationId,
    required this.onChanged,
  });

  final List<Administration> administrations;
  final List<Examen> examens;
  final int? annee;
  final StatutVerificationCandidature? statut;
  final String? administrationId;
  final void Function(int?, StatutVerificationCandidature?, String?) onChanged;

  @override
  Widget build(BuildContext context) {
    final annees = examens.map((e) => e.annee).toSet().toList()
      ..sort((a, b) => b.compareTo(a));

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          _FiltreDropdown<int>(
            label: 'Année',
            valeur: annee,
            options: {for (final a in annees) a: a.toString()},
            onChanged: (v) => onChanged(v, statut, administrationId),
          ),
          const SizedBox(width: 8),
          _FiltreDropdown<StatutVerificationCandidature>(
            label: 'Statut',
            valeur: statut,
            options: {
              for (final s in StatutVerificationCandidature.values)
                s: s.libelle,
            },
            onChanged: (v) => onChanged(annee, v, administrationId),
          ),
          const SizedBox(width: 8),
          _FiltreDropdown<String>(
            label: 'Administration',
            valeur: administrationId,
            options: {for (final a in administrations) a.id: a.nomOfficiel},
            onChanged: (v) => onChanged(annee, statut, v),
          ),
        ],
      ),
    );
  }
}

class _FiltreDropdown<T> extends StatelessWidget {
  const _FiltreDropdown({
    required this.label,
    required this.valeur,
    required this.options,
    required this.onChanged,
  });

  final String label;
  final T? valeur;
  final Map<T, String> options;
  final ValueChanged<T?> onChanged;

  @override
  Widget build(BuildContext context) {
    return DropdownButton<T?>(
      value: valeur,
      hint: Text(label),
      underline: const SizedBox.shrink(),
      items: [
        DropdownMenuItem<T?>(child: Text('Tous — $label')),
        ...options.entries.map(
            (e) => DropdownMenuItem<T?>(value: e.key, child: Text(e.value))),
      ],
      onChanged: onChanged,
    );
  }
}
