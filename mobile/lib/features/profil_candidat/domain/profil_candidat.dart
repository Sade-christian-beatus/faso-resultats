class ProfilCandidat {
  const ProfilCandidat({
    required this.id,
    required this.nomComplet,
    required this.telephoneVerifie,
    required this.emailVerifie,
    required this.notificationsSms,
    required this.notificationsPush,
    required this.notificationsEmail,
    required this.statut,
    this.email,
    this.derniereConnexion,
  });

  final String id;
  final String nomComplet;
  final bool telephoneVerifie;
  final String? email;
  final bool emailVerifie;
  final bool notificationsSms;
  final bool notificationsPush;
  final bool notificationsEmail;
  final String statut;
  final DateTime? derniereConnexion;
}
