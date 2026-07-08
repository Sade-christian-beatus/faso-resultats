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

  /// Une décision qui contient "ADMIS" (ADMIS, ADMISSIBLE) est traitée comme
  /// positive à l'affichage — les libellés de décision varient selon le type
  /// d'examen/concours (voir docs/CONTEXTE_METIER.md), pas de liste figée
  /// côté client.
  bool get estPositif => decision.toUpperCase().contains('ADMIS');
}
