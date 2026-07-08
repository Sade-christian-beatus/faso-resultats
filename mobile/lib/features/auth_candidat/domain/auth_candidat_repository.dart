import 'session_candidat.dart';

abstract class AuthCandidatRepository {
  /// Envoie un OTP pour démarrer une inscription. Renvoie le code de debug
  /// (non nul uniquement hors production, voir backend
  /// `InscriptionResponse.code_otp_debug`).
  Future<String?> inscrire({
    required String numeroCnib,
    required String nomComplet,
    required DateTime dateNaissance,
    required String telephone,
    required String consentementApdpVersion,
  });

  /// Envoie un OTP pour se connecter à un compte existant. Réponse
  /// volontairement identique que le compte existe ou non (anti-énumération,
  /// voir backend) — le code de debug est simplement absent si aucun compte.
  Future<String?> demanderConnexion(String telephone);

  /// Valide le code reçu, termine l'inscription ou la connexion en cours, et
  /// persiste le token de session en stockage sécurisé.
  Future<SessionCandidat> validerOtp(
      {required String telephone, required String code});

  Future<bool> estConnecte();

  Future<void> deconnecter();
}
