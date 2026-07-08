class SessionCandidat {
  const SessionCandidat({required this.accessToken, required this.compteCree});

  final String accessToken;

  /// true si l'OTP validé vient de créer un nouveau compte (inscription),
  /// false s'il s'agit d'une connexion à un compte existant.
  final bool compteCree;
}
