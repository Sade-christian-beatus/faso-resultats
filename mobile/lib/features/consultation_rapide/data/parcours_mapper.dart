import '../domain/parcours.dart';
import '../domain/resultat.dart';
import 'resultat_mapper.dart';

/// Matches `ParcoursCandidatOut` / `EtapeParcoursOut` (backend
/// app/schemas/public.py), returned by GET /api/v1/public/results/progress.
extension ParcoursMapper on Map<String, dynamic> {
  ParcoursCandidat versParcours() {
    return ParcoursCandidat(
      numeroPv: this['numero_pv'] as String,
      jury: this['jury'] as String,
      etapes: (this['etapes'] as List<dynamic>)
          .cast<Map<String, dynamic>>()
          .map((etape) => etape._versEtape())
          .toList(),
    );
  }

  EtapeParcours _versEtape() {
    final resultat = this['resultat'] as Map<String, dynamic>?;
    return EtapeParcours(
      phase: PhasePublication.depuisApi(this['phase'] as String),
      statutPhase: StatutPhase.depuisApi(this['statut_phase'] as String),
      situation: SituationCandidat.depuisApi(this['situation'] as String),
      resultat: resultat?.versResultat(),
    );
  }
}
