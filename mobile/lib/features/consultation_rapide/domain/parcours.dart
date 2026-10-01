import 'resultat.dart';

/// Mirror of `app.services.phases.StatutPhase` (backend).
enum StatutPhase {
  aVenir,
  enCours,
  cloturee;

  static StatutPhase depuisApi(String valeur) => switch (valeur) {
        'EN_COURS' => StatutPhase.enCours,
        'CLOTUREE' => StatutPhase.cloturee,
        _ => StatutPhase.aVenir,
      };
}

/// Mirror of `app.services.phases.SituationCandidat` (backend): where the
/// candidate stands for one phase. Computed server-side (GET
/// /results/progress) so that web, mobile, and later SMS/USSD say the same
/// thing.
enum SituationCandidat {
  /// The candidate is on a published list of this phase.
  resultat,

  /// Not on the lists published so far; the phase is still open, more lists
  /// may come. Never an failure.
  enAttente,

  /// The administration closed the phase and the candidate is on none of
  /// its lists.
  neFigurePas,

  /// Nothing published for this phase yet.
  aVenir,

  /// The candidate stopped at an earlier phase.
  nonConcerne;

  /// An unknown value falls back to [aVenir] ("not published yet"): a newer
  /// backend must never make this app announce an absence it cannot vouch
  /// for.
  static SituationCandidat depuisApi(String valeur) => switch (valeur) {
        'RESULTAT' => SituationCandidat.resultat,
        'EN_ATTENTE' => SituationCandidat.enAttente,
        'NE_FIGURE_PAS' => SituationCandidat.neFigurePas,
        'NON_CONCERNE' => SituationCandidat.nonConcerne,
        _ => SituationCandidat.aVenir,
      };
}

class EtapeParcours {
  const EtapeParcours({
    required this.phase,
    required this.statutPhase,
    required this.situation,
    this.resultat,
  });

  final PhasePublication phase;
  final StatutPhase statutPhase;
  final SituationCandidat situation;

  /// Present only when [situation] is [SituationCandidat.resultat].
  final Resultat? resultat;
}

/// One candidate (numero_pv + jury) across every phase of an exam.
class ParcoursCandidat {
  const ParcoursCandidat({
    required this.numeroPv,
    required this.jury,
    required this.etapes,
  });

  final String numeroPv;
  final String jury;
  final List<EtapeParcours> etapes;

  /// Single-list exam (BAC, BEPC, most competitions): shown as a plain
  /// result card, without a timeline.
  bool get estPublicationUnique =>
      etapes.length == 1 && etapes.first.resultat != null;

  /// Name and first name come from any phase the candidate appears in (the
  /// API only returns a candidate found on at least one list).
  Resultat? get identite {
    for (final etape in etapes) {
      if (etape.resultat != null) return etape.resultat;
    }
    return null;
  }
}
