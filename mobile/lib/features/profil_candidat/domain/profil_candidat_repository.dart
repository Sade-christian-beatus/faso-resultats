import 'profil_candidat.dart';
import 'profil_candidat_export.dart';

abstract class ProfilCandidatRepository {
  Future<ProfilCandidat> obtenir();

  /// Seuls email et préférences de notification sont modifiables — l'identité
  /// (CNIB, nom, date de naissance) ne l'est volontairement pas, y compris
  /// côté backend (voir docs/APDP_PROFIL_CANDIDAT.md § 8).
  Future<ProfilCandidat> mettreAJour({
    String? email,
    bool? notificationsSms,
    bool? notificationsPush,
    bool? notificationsEmail,
  });

  Future<ProfilCandidatExport> exporter();

  Future<void> supprimerCompte();
}
