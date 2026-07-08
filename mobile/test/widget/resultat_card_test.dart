import 'package:faso_resultats_mobile/features/consultation_rapide/domain/resultat.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/presentation/resultat_card.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

const _resultatAdmis = Resultat(
  numeroPv: '000123',
  jury: 'Ouagadougou 1',
  nom: 'TRAORE',
  prenom: 'Awa',
  decision: 'ADMIS',
  phase: PhasePublication.resultatUnique,
  moyenne: 14.5,
  etablissement: 'Lycée Philippe Zinda Kaboré',
  rangAffiche: '3e',
);

const _resultatAjourne = Resultat(
  numeroPv: '000124',
  jury: 'Bobo-Dioulasso',
  nom: 'OUEDRAOGO',
  prenom: 'Issa',
  decision: 'AJOURNÉ',
  phase: PhasePublication.admissibilite,
  phaseSuivanteAttendue: PhasePublication.admissionDefinitive,
);

void main() {
  testWidgets('affiche le nom, le récépissé et la décision positive',
      (tester) async {
    await tester.pumpWidget(const MaterialApp(
      home: Scaffold(body: ResultatCard(resultat: _resultatAdmis)),
    ));

    expect(find.text('Awa TRAORE'), findsOneWidget);
    expect(
        find.text('Récépissé n° 000123 — Jury Ouagadougou 1'), findsOneWidget);
    expect(find.text('ADMIS'), findsOneWidget);
    expect(find.text('14.50'), findsOneWidget);
    expect(find.text('Lycée Philippe Zinda Kaboré'), findsOneWidget);
    expect(find.text('3e'), findsOneWidget);
  });

  testWidgets('affiche la phase suivante attendue quand fournie',
      (tester) async {
    await tester.pumpWidget(const MaterialApp(
      home: Scaffold(body: ResultatCard(resultat: _resultatAjourne)),
    ));

    expect(find.text('Admissibilité'), findsOneWidget);
    expect(find.text('Admission définitive'), findsOneWidget);
  });

  testWidgets('le bouton Recevoir par SMS affiche « Bientôt disponible »',
      (tester) async {
    await tester.pumpWidget(const MaterialApp(
      home: Scaffold(body: ResultatCard(resultat: _resultatAdmis)),
    ));

    await tester.tap(find.text('Recevoir par SMS'));
    await tester.pump();

    expect(find.text('Bientôt disponible.'), findsOneWidget);
  });

  testWidgets('le bouton Partager ne fait pas planter la carte',
      (tester) async {
    await tester.pumpWidget(const MaterialApp(
      home: Scaffold(body: ResultatCard(resultat: _resultatAdmis)),
    ));

    await tester.tap(find.text('Partager'));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
  });
}
