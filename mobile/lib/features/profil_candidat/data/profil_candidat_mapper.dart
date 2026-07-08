import '../domain/profil_candidat.dart';
import '../domain/profil_candidat_export.dart';

/// Correspond à `ProfilCandidatOut` côté backend.
extension ProfilCandidatMapper on Map<String, dynamic> {
  ProfilCandidat versProfilCandidat() {
    final derniereConnexion = this['derniere_connexion'] as String?;
    return ProfilCandidat(
      id: this['id'] as String,
      nomComplet: this['nom_complet'] as String,
      telephoneVerifie: this['telephone_verifie'] as bool,
      email: this['email'] as String?,
      emailVerifie: this['email_verifie'] as bool,
      notificationsSms: this['notifications_sms'] as bool,
      notificationsPush: this['notifications_push'] as bool,
      notificationsEmail: this['notifications_email'] as bool,
      statut: this['statut'] as String,
      derniereConnexion:
          derniereConnexion == null ? null : DateTime.parse(derniereConnexion),
    );
  }

  /// Correspond à `ProfilCandidatExport` côté backend.
  ProfilCandidatExport versProfilCandidatExport() {
    return ProfilCandidatExport(
      numeroCnib: this['numero_cnib'] as String,
      nomComplet: this['nom_complet'] as String,
      dateNaissance: this['date_naissance'] as String,
      telephone: this['telephone'] as String,
      email: this['email'] as String?,
      consentementApdpDate:
          DateTime.parse(this['consentement_apdp_date'] as String),
      consentementApdpVersion: this['consentement_apdp_version'] as String,
      createdAt: DateTime.parse(this['created_at'] as String),
      candidatures: (this['candidatures'] as List<dynamic>)
          .cast<Map<String, dynamic>>()
          .map(
            (json) => CandidatureExportEntree(
              numeroRecepisse: json['numero_recepisse'] as String,
              statutVerification: json['statut_verification'] as String,
              createdAt: DateTime.parse(json['created_at'] as String),
            ),
          )
          .toList(),
      journal: (this['journal'] as List<dynamic>)
          .cast<Map<String, dynamic>>()
          .map(
            (json) => JournalEntree(
              action: json['action'] as String,
              ip: json['ip'] as String?,
              timestamp: DateTime.parse(json['timestamp'] as String),
            ),
          )
          .toList(),
    );
  }
}
