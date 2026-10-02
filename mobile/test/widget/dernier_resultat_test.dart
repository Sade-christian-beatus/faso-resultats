import 'package:faso_resultats_mobile/config/theme.dart';
import 'package:faso_resultats_mobile/features/candidatures/domain/candidature.dart';
import 'package:faso_resultats_mobile/features/candidatures/presentation/dernier_resultat.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

Candidature _candidature({String? statut, String? phase}) => Candidature(
      id: 'c1',
      administrationId: 'a1',
      examenId: 'e1',
      numeroRecepisse: '000123',
      statutVerification: StatutVerificationCandidature.verifieAuto,
      dernierResultatStatut: statut,
      dernierResultatPhase: phase,
    );

Future<void> _afficher(WidgetTester tester, Candidature candidature) =>
    tester.pumpWidget(MaterialApp(
      home: Scaffold(body: DernierResultat(candidature: candidature)),
    ));

Color? _couleur(WidgetTester tester, String texte) =>
    tester.widget<Text>(find.text(texte)).style?.color;

void main() {
  testWidgets('sans résultat : pas encore publié', (tester) async {
    await _afficher(tester, _candidature());
    expect(find.text('Résultat pas encore publié'), findsOneWidget);
  });

  testWidgets('« NON ADMIS » en couleur d’échec, jamais de réussite',
      (tester) async {
    await _afficher(tester, _candidature(statut: 'NON ADMIS'));
    expect(_couleur(tester, 'NON ADMIS'), AppColors.erreur);
  });

  testWidgets('« ADMIS » en couleur de réussite', (tester) async {
    await _afficher(tester, _candidature(statut: 'ADMIS'));
    expect(_couleur(tester, 'ADMIS'), AppColors.succes);
  });

  testWidgets('phase en clair et phrase d’absence au lieu des codes API',
      (tester) async {
    await _afficher(
      tester,
      _candidature(statut: statutAbsentDeLaListe, phase: 'ADMISSIBILITE'),
    );
    expect(find.text('Admissibilité'), findsOneWidget);
    expect(find.text('ADMISSIBILITE'), findsNothing);
    expect(find.textContaining('vous n’y figurez pas'), findsOneWidget);
    expect(find.text(statutAbsentDeLaListe), findsNothing);
  });

  test('méthodes de vérification en clair', () {
    expect(libelleMethodeVerification('OTP_SMS'), 'Code reçu par SMS');
    expect(libelleMethodeVerification('CNIB_MATCH_AUTO'), 'Numéro CNIB');
    expect(libelleMethodeVerification('INCONNU'), 'INCONNU');
  });
}
