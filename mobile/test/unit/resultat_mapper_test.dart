import 'package:faso_resultats_mobile/features/consultation_rapide/data/resultat_mapper.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/resultat.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('ResultatMapper', () {
    test('convertit un JSON complet (concours à phases)', () {
      final json = {
        'numero_pv': '000015',
        'jury': '03',
        'nom': 'BAYALA',
        'prenom': 'Jean-Claude',
        'decision': 'ADMISSIBLE',
        'moyenne': null,
        'etablissement': null,
        'rang_numerique': 1,
        'rang_affiche': '1°',
        'phase': 'ADMISSIBILITE',
        'phase_suivante_attendue': 'ADMISSION_DEFINITIVE',
        'date_publication_phase': '2026-07-01T10:00:00Z',
      };

      final resultat = json.versResultat();

      expect(resultat.numeroPv, '000015');
      expect(resultat.rangAffiche, '1°');
      expect(resultat.phase, PhasePublication.admissibilite);
      expect(
          resultat.phaseSuivanteAttendue, PhasePublication.admissionDefinitive);
      expect(resultat.estPositif, isTrue);
    });

    test('convertit un JSON minimal (examen scolaire simple)', () {
      final json = {
        'numero_pv': '000201',
        'jury': 'Ouaga 1',
        'nom': 'OUEDRAOGO',
        'prenom': 'Fatou',
        'decision': 'AJOURNE',
        'moyenne': 8.5,
        'etablissement': null,
        'rang_numerique': null,
        'rang_affiche': null,
        'phase': 'RESULTAT_UNIQUE',
        'phase_suivante_attendue': null,
        'date_publication_phase': null,
      };

      final resultat = json.versResultat();

      expect(resultat.phase, PhasePublication.resultatUnique);
      expect(resultat.phaseSuivanteAttendue, isNull);
      expect(resultat.rangAffiche, isNull);
      expect(resultat.moyenne, 8.5);
      expect(resultat.estPositif, isFalse);
    });
  });
}
