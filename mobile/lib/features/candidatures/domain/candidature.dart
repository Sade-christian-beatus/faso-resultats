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
    this.codeOtpDebug,
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

  /// Non persisté côté backend : renvoyé uniquement sur la réponse de
  /// création, et seulement hors production (comme
  /// `InscriptionResponse.codeOtpDebug`).
  final String? codeOtpDebug;

  /// Le mécanisme 3 (fallback OTP) est en attente de confirmation : voir
  /// backend `create_candidature` — statut EN_ATTENTE + méthode OTP_SMS.
  bool get attenteConfirmationOtp =>
      statutVerification == StatutVerificationCandidature.enAttente &&
      methodeVerification == 'OTP_SMS';
}

/// Value of `dernier_resultat_statut` when the candidate is on none of the
/// lists of a closed phase (backend app/services/candidat/matching_service.py).
const statutAbsentDeLaListe = 'NE FIGURE PAS SUR LA LISTE';

/// Candidate-facing labels for the backend `MethodeVerification` codes.
String libelleMethodeVerification(String code) => switch (code) {
      'CNIB_MATCH_AUTO' => 'Numéro CNIB',
      'DATE_NAISSANCE' => 'Date de naissance',
      'OTP_SMS' => 'Code reçu par SMS',
      'VALIDATION_MANUELLE' => 'Validation par l’administration',
      _ => code,
    };
