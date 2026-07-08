import '../domain/examen.dart';

/// Correspond à `ExamenPublicOut` côté backend (backend/app/schemas/public.py).
extension ExamenMapper on Map<String, dynamic> {
  Examen versExamen() {
    return Examen(
      id: this['id'] as String,
      administrationId: this['administration_id'] as String,
      typeExamen: this['type_examen'] as String,
      annee: this['annee'] as int,
      libelle: this['libelle'] as String,
    );
  }
}
