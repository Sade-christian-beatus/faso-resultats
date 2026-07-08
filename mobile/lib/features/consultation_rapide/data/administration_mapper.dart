import '../domain/administration.dart';

/// Correspond à `AdministrationPublicOut` côté backend
/// (backend/app/schemas/public.py).
extension AdministrationMapper on Map<String, dynamic> {
  Administration versAdministration() {
    return Administration(
      id: this['id'] as String,
      code: this['code'] as String,
      nomOfficiel: this['nom_officiel'] as String,
      sigle: this['sigle'] as String,
      logoUrl: this['logo_url'] as String?,
      couleurPrimaire: this['couleur_primaire'] as String?,
    );
  }
}
