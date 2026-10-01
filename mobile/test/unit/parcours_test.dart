import 'package:faso_resultats_mobile/features/consultation_rapide/domain/parcours.dart';
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
  group('SituationCandidat.depuisApi', () {
    test('une valeur inconnue ne déclare jamais une absence', () {
      expect(SituationCandidat.depuisApi('NOUVELLE_VALEUR'),
          SituationCandidat.aVenir);
      expect(SituationCandidat.depuisApi('NE_FIGURE_PAS'),
          SituationCandidat.neFigurePas);
    });
  });

  group('ParcoursCandidat', () {
    test('un examen à liste unique est affiché comme un résultat simple', () {
      final parcours = ParcoursCandidat(numeroPv: '1', jury: 'J', etapes: [
        EtapeParcours(
          phase: PhasePublication.resultatUnique,
          statutPhase: StatutPhase.cloturee,
          situation: SituationCandidat.resultat,
          resultat: _avecDecision('ADMIS'),
        ),
      ]);
      expect(parcours.estPublicationUnique, isTrue);
    });

    test("l'identité vient de n'importe quelle phase où figure le candidat",
        () {
      final parcours = ParcoursCandidat(numeroPv: '1', jury: 'J', etapes: [
        const EtapeParcours(
          phase: PhasePublication.epreuvesSportives,
          statutPhase: StatutPhase.enCours,
          situation: SituationCandidat.enAttente,
        ),
        EtapeParcours(
          phase: PhasePublication.admissibilite,
          statutPhase: StatutPhase.enCours,
          situation: SituationCandidat.resultat,
          resultat: _avecDecision('ADMISSIBLE'),
        ),
      ]);
      expect(parcours.estPublicationUnique, isFalse);
      expect(parcours.identite!.decision, 'ADMISSIBLE');
    });
  });
}
