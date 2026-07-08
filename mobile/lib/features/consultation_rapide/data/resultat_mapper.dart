import '../domain/resultat.dart';

/// Correspond à `ResultatPublicOut` côté backend (backend/app/schemas/public.py).
extension ResultatMapper on Map<String, dynamic> {
  Resultat versResultat() {
    final phaseSuivante = this['phase_suivante_attendue'] as String?;
    return Resultat(
      numeroPv: this['numero_pv'] as String,
      jury: this['jury'] as String,
      nom: this['nom'] as String,
      prenom: this['prenom'] as String,
      decision: this['decision'] as String,
      moyenne: (this['moyenne'] as num?)?.toDouble(),
      etablissement: this['etablissement'] as String?,
      rangNumerique: this['rang_numerique'] as int?,
      rangAffiche: this['rang_affiche'] as String?,
      phase: PhasePublication.depuisApi(this['phase'] as String),
      phaseSuivanteAttendue: phaseSuivante == null
          ? null
          : PhasePublication.depuisApi(phaseSuivante),
    );
  }
}
