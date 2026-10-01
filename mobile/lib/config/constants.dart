/// Constantes partagées, pour éviter les valeurs magiques dispersées dans les
/// features (docs/API.md référence chaque route consommée ici).
class ApiPaths {
  const ApiPaths._();

  static const String publicAdministrations = '/api/v1/public/administrations';
  static const String publicExams = '/api/v1/public/exams';

  /// Phase-by-phase progress (also works for single-list exams): the only
  /// result lookup used by the app since 2026-10-01.
  static const String publicResultsProgress = '/api/v1/public/results/progress';
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

class AppInfo {
  const AppInfo._();

  /// Doit rester synchronisé manuellement avec `version:` dans pubspec.yaml.
  /// Pas de dépendance `package_info_plus` pour une seule valeur statique
  /// affichée à l'écran « À propos » (pas de sur-ingénierie, CLAUDE.md).
  static const String version = '1.0.0+1';

  /// Version du bandeau d'information affiché à la première ouverture
  /// (jour 8) — distincte de celle du consentement à l'inscription candidat
  /// (`_versionConsentementApdp`, auth_candidat_screen.dart) : ce bandeau
  /// informe tout visiteur, y compris ceux qui ne créent jamais de compte.
  static const String versionConsentementApp = 'v1';
}

/// Faso Résultats support line, shown on the home screen ("Assistance") and
/// the help screen. Same numbers as the web site footer.
class ContactSupport {
  const ContactSupport._();

  /// Local 8-digit numbers, as Burkinabè users write them.
  static const List<String> telephones = ['56121818', '62291818'];

  /// "56 12 18 18".
  static String formater(String numero) => [
        for (var i = 0; i < numero.length; i += 2)
          numero.substring(i, i + 2 > numero.length ? numero.length : i + 2),
      ].join(' ');

  static Uri uriAppel(String numero) => Uri(scheme: 'tel', path: '+226$numero');
}
