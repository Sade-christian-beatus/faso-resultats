import 'package:faso_resultats_mobile/features/consultation_rapide/domain/resultat.dart';
import 'package:flutter_test/flutter_test.dart';

Resultat _avecDecision(String decision) => Resultat(
      numeroPv: '1',
      jury: 'J',
      nom: 'N',
      prenom: 'P',
      decision: decision,
      phase: PhasePublication.resultatUnique,
    );

void main() {
  group('Resultat.tonalite (mêmes règles que le backend)', () {
    test('les formes négatives ne passent jamais pour une réussite', () {
      // Regression: "NON ADMIS" contains "ADMIS" and was shown in green.
      for (final decision in [
        'NON ADMIS',
        'non admissible',
        'NON-ADMIS',
        'INAPTE',
        'AJOURNÉ',
        'AJOURNE',
        'ÉLIMINÉ',
        'ABSENT',
        'REFUSÉ',
      ]) {
        expect(_avecDecision(decision).tonalite, TonaliteDecision.negative,
            reason: decision);
        expect(_avecDecision(decision).estPositif, isFalse, reason: decision);
      }
    });

    test('les décisions favorables', () {
      for (final decision in [
        'ADMIS',
        'ADMISSIBLE',
        'APTE',
        'Admis (non boursier)',
        'REÇU',
      ]) {
        expect(_avecDecision(decision).tonalite, TonaliteDecision.positive,
            reason: decision);
      }
    });

    test('une décision inconnue reste neutre', () {
      expect(
          _avecDecision('EN DÉLIBÉRATION').tonalite, TonaliteDecision.neutre);
    });
  });
}
