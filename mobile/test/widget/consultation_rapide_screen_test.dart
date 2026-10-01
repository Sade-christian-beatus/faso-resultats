import 'package:faso_resultats_mobile/features/consultation_rapide/domain/administration.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/categorie_examen.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/consultation_repository.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/examen.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/parcours.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/resultat.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/presentation/consultation_providers.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/presentation/consultation_rapide_screen.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/presentation/parcours_card.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/presentation/resultat_card.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _FakeConsultationRepository implements ConsultationRepository {
  _FakeConsultationRepository({this.parcours = const []});

  final List<ParcoursCandidat> parcours;

  @override
  Future<List<Administration>> listerAdministrations() async => [
        const Administration(
            id: 'admin-1',
            code: 'ocecos',
            nomOfficiel: 'OCECOS',
            sigle: 'OCECOS'),
      ];

  @override
  Future<List<Examen>> listerExamens() async => [
        const Examen(
          id: 'examen-1',
          administrationId: 'admin-1',
          typeExamen: 'BAC',
          annee: 2026,
          libelle: 'BAC 2026',
        ),
      ];

  @override
  Future<List<ParcoursCandidat>> rechercherParcours({
    required String examenId,
    required String numeroPv,
    String? jury,
  }) async =>
      parcours;
}

Widget construireApp(ConsultationRepository repository) {
  return ProviderScope(
    overrides: [consultationRepositoryProvider.overrideWithValue(repository)],
    child: const MaterialApp(home: ConsultationRapideScreen()),
  );
}

/// Two administrations: a school exam at OCECOS, a police exam elsewhere.
class _FakeDeuxAdministrations extends _FakeConsultationRepository {
  @override
  Future<List<Administration>> listerAdministrations() async => const [
        Administration(
            id: 'admin-1',
            code: 'ocecos',
            nomOfficiel: 'OCECOS',
            sigle: 'OCECOS'),
        Administration(
            id: 'admin-2',
            code: 'police',
            nomOfficiel: 'Police nationale',
            sigle: 'PN'),
      ];

  @override
  Future<List<Examen>> listerExamens() async => [
        ...await super.listerExamens(),
        const Examen(
          id: 'examen-police',
          administrationId: 'admin-2',
          typeExamen: 'POLICE',
          annee: 2026,
          libelle: 'Élèves assistants de police',
        ),
      ];
}

Widget construireAppAvec(ConsultationRapideScreen ecran) {
  return ProviderScope(
    overrides: [
      consultationRepositoryProvider
          .overrideWithValue(_FakeDeuxAdministrations()),
    ],
    child: MaterialApp(home: ecran),
  );
}

const _admis = Resultat(
  numeroPv: '000123',
  jury: 'Ouaga 1',
  nom: 'TRAORE',
  prenom: 'Awa',
  decision: 'ADMIS',
  phase: PhasePublication.resultatUnique,
);

Future<void> _rechercherBac(
    WidgetTester tester, List<ParcoursCandidat> parcours) async {
  await tester.pumpWidget(ProviderScope(
    overrides: [
      consultationRepositoryProvider
          .overrideWithValue(_FakeConsultationRepository(parcours: parcours)),
    ],
    child:
        const MaterialApp(home: ConsultationRapideScreen(examenId: 'examen-1')),
  ));
  await tester.pumpAndSettle();
  await tester.enterText(find.byType(TextFormField).first, '000123');
  await tester.tap(find.text('Rechercher'));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('examen à liste unique : la carte résultat habituelle',
      (tester) async {
    await _rechercherBac(tester, [
      const ParcoursCandidat(numeroPv: '000123', jury: 'Ouaga 1', etapes: [
        EtapeParcours(
          phase: PhasePublication.resultatUnique,
          statutPhase: StatutPhase.cloturee,
          situation: SituationCandidat.resultat,
          resultat: _admis,
        ),
      ]),
    ]);

    expect(find.byType(ResultatCard), findsOneWidget);
    expect(find.byType(ParcoursCard), findsNothing);
    expect(find.text('Awa TRAORE'), findsOneWidget);
  });

  testWidgets('concours à phases : la frise phase par phase', (tester) async {
    await _rechercherBac(tester, [
      const ParcoursCandidat(numeroPv: '000123', jury: 'Ouaga 1', etapes: [
        EtapeParcours(
          phase: PhasePublication.epreuvesSportives,
          statutPhase: StatutPhase.cloturee,
          situation: SituationCandidat.resultat,
          resultat: _admis,
        ),
        EtapeParcours(
          phase: PhasePublication.admissibilite,
          statutPhase: StatutPhase.enCours,
          situation: SituationCandidat.enAttente,
        ),
      ]),
    ]);

    expect(find.byType(ParcoursCard), findsOneWidget);
    expect(find.byType(ResultatCard), findsNothing);
    expect(find.text('Admissibilité'), findsOneWidget);
  });

  testWidgets(
      'un examen présélectionné (résultats récents) est prêt à chercher',
      (tester) async {
    await tester.pumpWidget(construireAppAvec(
        const ConsultationRapideScreen(examenId: 'examen-police')));
    await tester.pumpAndSettle();

    expect(find.text('Police nationale'), findsOneWidget);
    expect(find.text('2026 — Élèves assistants de police'), findsOneWidget);
    final bouton = tester.widget<ElevatedButton>(find.byType(ElevatedButton));
    expect(bouton.onPressed, isNotNull);
  });

  testWidgets('une catégorie ne propose que ses administrations',
      (tester) async {
    await tester.pumpWidget(construireAppAvec(const ConsultationRapideScreen(
        categorie: CategorieExamen.paramilitaires)));
    await tester.pumpAndSettle();

    expect(find.text('Catégorie : Paramilitaires'), findsOneWidget);
    await tester.tap(find.byType(DropdownButtonFormField<String>).first);
    await tester.pumpAndSettle();
    expect(find.text('Police nationale'), findsWidgets);
    expect(find.text('OCECOS'), findsNothing);
  });

  testWidgets('retirer la catégorie propose de nouveau tout', (tester) async {
    await tester.pumpWidget(construireAppAvec(const ConsultationRapideScreen(
        categorie: CategorieExamen.paramilitaires)));
    await tester.pumpAndSettle();

    await tester.tap(find.byTooltip('Toutes les catégories'));
    await tester.pumpAndSettle();
    expect(find.text('Catégorie : Paramilitaires'), findsNothing);

    await tester.tap(find.byType(DropdownButtonFormField<String>).first);
    await tester.pumpAndSettle();
    expect(find.text('OCECOS'), findsWidgets);
  });

  testWidgets('affiche le formulaire et charge les administrations',
      (tester) async {
    await tester.pumpWidget(construireApp(_FakeConsultationRepository()));
    await tester.pumpAndSettle();

    expect(find.text('Consulter mon résultat'), findsOneWidget);
    expect(find.byType(DropdownButtonFormField<String>), findsWidgets);
  });

  testWidgets(
    'sélectionner une administration puis un examen active le bouton rechercher',
    (tester) async {
      await tester.pumpWidget(construireApp(_FakeConsultationRepository()));
      await tester.pumpAndSettle();

      await tester.tap(find.byType(DropdownButtonFormField<String>).first);
      await tester.pumpAndSettle();
      await tester.tap(find.text('OCECOS').last);
      await tester.pumpAndSettle();

      await tester.tap(find.byType(DropdownButtonFormField<String>).last);
      await tester.pumpAndSettle();
      await tester.tap(find.text('2026 — BAC 2026').last);
      await tester.pumpAndSettle();

      final bouton = tester.widget<ElevatedButton>(find.byType(ElevatedButton));
      expect(bouton.onPressed, isNotNull);
    },
  );

  testWidgets('affiche "aucun résultat" quand la recherche ne trouve rien',
      (tester) async {
    await tester.pumpWidget(construireApp(_FakeConsultationRepository()));
    await tester.pumpAndSettle();

    await tester.tap(find.byType(DropdownButtonFormField<String>).first);
    await tester.pumpAndSettle();
    await tester.tap(find.text('OCECOS').last);
    await tester.pumpAndSettle();
    await tester.tap(find.byType(DropdownButtonFormField<String>).last);
    await tester.pumpAndSettle();
    await tester.tap(find.text('2026 — BAC 2026').last);
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextFormField).first, '000123');
    await tester.tap(find.text('Rechercher'));
    await tester.pumpAndSettle();

    expect(find.textContaining('Aucun résultat trouvé'), findsOneWidget);
  });
}
