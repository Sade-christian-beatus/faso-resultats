class Administration {
  const Administration({
    required this.id,
    required this.code,
    required this.nomOfficiel,
    required this.sigle,
    this.logoUrl,
    this.couleurPrimaire,
  });

  final String id;
  final String code;
  final String nomOfficiel;
  final String sigle;
  final String? logoUrl;
  final String? couleurPrimaire;
}
