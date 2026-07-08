import 'package:faso_resultats_mobile/features/consultation_rapide/domain/administration.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/consultation_repository.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/examen.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/resultat.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/presentation/consultation_providers.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/presentation/consultation_rapide_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _FakeConsultationRepository implements ConsultationRepository {
  _FakeConsultationRepository({this.resultats = const []});

  final List<Resultat> resultats;

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
  Future<List<Resultat>> rechercherResultats({
    required String examenId,
    required String numeroPv,
    String? jury,
  }) async =>
      resultats;
}

Widget construireApp(ConsultationRepository repository) {
  return ProviderScope(
    overrides: [consultationRepositoryProvider.overrideWithValue(repository)],
    child: const MaterialApp(home: ConsultationRapideScreen()),
  );
}

void main() {
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
    await tester
        .pumpWidget(construireApp(_FakeConsultationRepository(resultats: [])));
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
