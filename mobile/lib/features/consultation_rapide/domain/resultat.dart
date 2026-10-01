/// Miroir de `app.models.resultat.PhasePublication` côté backend.
enum PhasePublication {
  resultatUnique,
  epreuvesSportives,
  admissibilite,
  admissionDefinitive,
  secondTour;

  static PhasePublication depuisApi(String valeur) {
    return switch (valeur) {
      'EPREUVES_SPORTIVES' => PhasePublication.epreuvesSportives,
      'ADMISSIBILITE' => PhasePublication.admissibilite,
      'ADMISSION_DEFINITIVE' => PhasePublication.admissionDefinitive,
      'SECOND_TOUR' => PhasePublication.secondTour,
      _ => PhasePublication.resultatUnique,
    };
  }

  String get libelle => switch (this) {
        PhasePublication.resultatUnique => 'Résultat',
        PhasePublication.epreuvesSportives => 'Épreuves sportives',
        PhasePublication.admissibilite => 'Admissibilité',
        PhasePublication.admissionDefinitive => 'Admission définitive',
        PhasePublication.secondTour => 'Second tour',
      };
}

/// How a decision reads to the candidate: drives the badge colour.
enum TonaliteDecision { positive, negative, neutre }

// Same rules as the backend (app/services/phases.py, `decision_negative`):
// decisions are free text from official files, negative forms are tested
// first so that "NON ADMIS" or "INAPTE" never read as a success.
const _prefixesNegatifs = ['NON ', 'NON-'];
const _marqueursNegatifs = [
  'AJOURN',
  'INAPTE',
  'ELIMIN',
  'ÉLIMIN',
  'ABSENT',
  'REFUS',
];
const _marqueursPositifs = ['ADMIS', 'APTE', 'REÇU', 'RECU'];

class Resultat {
  const Resultat({
    required this.numeroPv,
    required this.jury,
    required this.nom,
    required this.prenom,
    required this.decision,
    required this.phase,
    this.moyenne,
    this.etablissement,
    this.rangNumerique,
    this.rangAffiche,
    this.phaseSuivanteAttendue,
  });

  final String numeroPv;
  final String jury;
  final String nom;
  final String prenom;
  final String decision;
  final double? moyenne;
  final String? etablissement;
  final int? rangNumerique;
  final String? rangAffiche;
  final PhasePublication phase;
  final PhasePublication? phaseSuivanteAttendue;

  /// Negative forms first ("NON ADMIS" contains "ADMIS", "INAPTE" contains
  /// "APTE"); a decision matching no rule is neutral, never shown as a
  /// success.
  TonaliteDecision get tonalite {
    final valeur = decision.trim().toUpperCase();
    if (_prefixesNegatifs.any(valeur.startsWith) ||
        _marqueursNegatifs.any(valeur.contains)) {
      return TonaliteDecision.negative;
    }
    if (_marqueursPositifs.any(valeur.contains)) {
      return TonaliteDecision.positive;
    }
    return TonaliteDecision.neutre;
  }

  bool get estPositif => tonalite == TonaliteDecision.positive;
}
