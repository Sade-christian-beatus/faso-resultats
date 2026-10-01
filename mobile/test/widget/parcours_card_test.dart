import 'package:faso_resultats_mobile/features/consultation_rapide/domain/parcours.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/resultat.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/presentation/parcours_card.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:intl/date_symbol_data_local.dart';

ParcoursCandidat _parcours(List<EtapeParcours> etapes) =>
    ParcoursCandidat(numeroPv: '000015', jury: '03', etapes: etapes);

final _apte = Resultat(
  numeroPv: '000015',
  jury: '03',
  nom: 'BAYALA',
  prenom: 'Jean-Claude',
  decision: 'APTE',
  phase: PhasePublication.epreuvesSportives,
  rangAffiche: '12e',
  phaseSuivanteAttendue: PhasePublication.admissibilite,
  datePublicationPhase: DateTime(2026, 7),
);

Future<void> _afficher(WidgetTester tester, ParcoursCandidat parcours) async {
  await tester.pumpWidget(MaterialApp(
    home: Scaffold(
        body: SingleChildScrollView(child: ParcoursCard(parcours: parcours))),
  ));
}

void main() {
  setUpAll(() => initializeDateFormatting('fr_FR'));

  testWidgets('affiche chaque phase et sa situation', (tester) async {
    await _afficher(
      tester,
      _parcours([
        EtapeParcours(
          phase: PhasePublication.epreuvesSportives,
          statutPhase: StatutPhase.cloturee,
          situation: SituationCandidat.resultat,
          resultat: _apte,
        ),
        const EtapeParcours(
          phase: PhasePublication.admissibilite,
          statutPhase: StatutPhase.enCours,
          situation: SituationCandidat.enAttente,
        ),
        const EtapeParcours(
          phase: PhasePublication.admissionDefinitive,
          statutPhase: StatutPhase.aVenir,
          situation: SituationCandidat.aVenir,
        ),
      ]),
    );

    expect(find.text('Jean-Claude BAYALA'), findsOneWidget);
    expect(find.text('Récépissé n° 000015 — Jury 03'), findsOneWidget);
    expect(find.text('Épreuves sportives'), findsOneWidget);
    expect(find.text('APTE'), findsOneWidget);
    expect(find.text('Rang : 12e'), findsOneWidget);
    expect(find.text('Publié le 01/07/2026'), findsOneWidget);
    expect(find.text('Prochaine étape : Admissibilité'), findsOneWidget);
    expect(find.textContaining('Publication en cours'), findsOneWidget);
    expect(find.text('Pas encore publiée'), findsOneWidget);
    // Never "absent" while a phase is still open.
    expect(find.textContaining('vous n’y figurez pas'), findsNothing);
  });

  testWidgets('« ne figure pas » seulement pour une phase clôturée',
      (tester) async {
    await _afficher(
      tester,
      _parcours([
        EtapeParcours(
          phase: PhasePublication.epreuvesSportives,
          statutPhase: StatutPhase.cloturee,
          situation: SituationCandidat.resultat,
          resultat: _apte,
        ),
        const EtapeParcours(
          phase: PhasePublication.admissibilite,
          statutPhase: StatutPhase.cloturee,
          situation: SituationCandidat.neFigurePas,
        ),
        const EtapeParcours(
          phase: PhasePublication.admissionDefinitive,
          statutPhase: StatutPhase.aVenir,
          situation: SituationCandidat.nonConcerne,
        ),
      ]),
    );

    expect(find.textContaining('vous n’y figurez pas'), findsOneWidget);
    expect(find.textContaining("rapprochez-vous de l'organisateur"),
        findsOneWidget);
    expect(find.text('Non concerné'), findsOneWidget);
  });
}
