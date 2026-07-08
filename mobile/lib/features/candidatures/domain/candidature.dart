enum StatutVerificationCandidature {
  enAttente,
  verifieAuto,
  verifieManuel,
  rejete,
  administrationResiliee;

  static StatutVerificationCandidature depuisApi(String valeur) {
    return switch (valeur) {
      'VERIFIE_AUTO' => StatutVerificationCandidature.verifieAuto,
      'VERIFIE_MANUEL' => StatutVerificationCandidature.verifieManuel,
      'REJETE' => StatutVerificationCandidature.rejete,
      'ADMINISTRATION_RESILIEE' =>
        StatutVerificationCandidature.administrationResiliee,
      _ => StatutVerificationCandidature.enAttente,
    };
  }

  String get libelle => switch (this) {
        StatutVerificationCandidature.verifieAuto => 'Vérifiée',
        StatutVerificationCandidature.verifieManuel => 'Vérifiée',
        StatutVerificationCandidature.enAttente => 'En attente de publication',
        StatutVerificationCandidature.rejete => 'Non vérifiée',
        StatutVerificationCandidature.administrationResiliee =>
          'Administration résiliée',
      };
}

class Candidature {
  const Candidature({
    required this.id,
    required this.administrationId,
    required this.examenId,
    required this.numeroRecepisse,
    required this.statutVerification,
    this.methodeVerification,
    this.dernierResultatStatut,
    this.dernierResultatPhase,
    this.dernierResultatPublieAt,
  });

  final String id;
  final String administrationId;
  final String examenId;
  final String numeroRecepisse;
  final StatutVerificationCandidature statutVerification;
  final String? methodeVerification;
  final String? dernierResultatStatut;
  final String? dernierResultatPhase;
  final DateTime? dernierResultatPublieAt;

  /// Le mécanisme 3 (fallback OTP) est en attente de confirmation : voir
  /// backend `create_candidature` — statut EN_ATTENTE + méthode OTP_SMS.
  bool get attenteConfirmationOtp =>
      statutVerification == StatutVerificationCandidature.enAttente &&
      methodeVerification == 'OTP_SMS';
}
