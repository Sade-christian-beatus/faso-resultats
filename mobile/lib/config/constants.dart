/// Constantes partagées, pour éviter les valeurs magiques dispersées dans les
/// features (docs/API.md référence chaque route consommée ici).
class ApiPaths {
  const ApiPaths._();

  static const String publicAdministrations = '/api/v1/public/administrations';
  static const String publicExams = '/api/v1/public/exams';
  static const String publicResults = '/api/v1/public/results';
  static const String publicDroitsCandidat = '/api/v1/public/droits-candidat';

  static const String candidatInscription = '/api/v1/candidat/inscription';
  static const String candidatLogin = '/api/v1/candidat/login';
  static const String candidatOtpVerify = '/api/v1/candidat/otp/verify';
  static const String candidatMe = '/api/v1/candidat/me';
  static const String candidatMeExport = '/api/v1/candidat/me/export';
  static const String candidatCandidatures = '/api/v1/candidat/candidatures';

  static String candidatureConfirmerOtp(String candidatureId) =>
      '/api/v1/candidat/candidatures/$candidatureId/confirmer-otp';

  static String candidature(String candidatureId) =>
      '/api/v1/candidat/candidatures/$candidatureId';
}

class StorageKeys {
  const StorageKeys._();

  static const String tokenCandidat = 'faso_candidat_token';
  static const String langueChoisie = 'faso_langue';
  static const String consentementVersion = 'faso_consentement_version';
}

class AppDurations {
  const AppDurations._();

  static const Duration timeoutReseau = Duration(seconds: 15);

  /// Durée de mise en cache local des résultats déjà consultés (jour 9,
  /// docs/PROFIL_CANDIDAT_UNIFIE.md § usage hors-ligne).
  static const Duration cacheResultats = Duration(hours: 24);
}
