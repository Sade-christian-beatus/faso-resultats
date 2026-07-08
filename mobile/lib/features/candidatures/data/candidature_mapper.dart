import '../domain/candidature.dart';

/// Correspond à `CandidatureOut` côté backend (backend/app/schemas/candidat.py).
extension CandidatureMapper on Map<String, dynamic> {
  Candidature versCandidature() {
    final publieAt = this['dernier_resultat_publie_at'] as String?;
    return Candidature(
      id: this['id'] as String,
      administrationId: this['administration_id'] as String,
      examenId: this['examen_id'] as String,
      numeroRecepisse: this['numero_recepisse'] as String,
      statutVerification: StatutVerificationCandidature.depuisApi(
        this['statut_verification'] as String,
      ),
      methodeVerification: this['methode_verification'] as String?,
      dernierResultatStatut: this['dernier_resultat_statut'] as String?,
      dernierResultatPhase: this['dernier_resultat_phase'] as String?,
      dernierResultatPublieAt:
          publieAt == null ? null : DateTime.parse(publieAt),
    );
  }
}
