class Examen {
  const Examen({
    required this.id,
    required this.administrationId,
    required this.typeExamen,
    required this.annee,
    required this.libelle,
  });

  final String id;
  final String administrationId;
  final String typeExamen;
  final int annee;
  final String libelle;
}
