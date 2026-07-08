/// Validateurs alignés sur les contraintes réelles du backend (voir
/// backend/app/schemas/candidat.py) — ne pas être plus strict que l'API elle-
/// même, au risque de rejeter côté client des saisies que le serveur
/// accepterait.
class Validators {
  const Validators._();

  static final _regexTelephoneBf = RegExp(r'^\+226\d{8}$');

  static String? telephone(String? valeur) {
    if (valeur == null || valeur.trim().isEmpty) {
      return 'Le numéro de téléphone est obligatoire';
    }
    if (!_regexTelephoneBf.hasMatch(valeur.trim())) {
      return 'Format attendu : +226 suivi de 8 chiffres';
    }
    return null;
  }

  static String? cnib(String? valeur) {
    if (valeur == null || valeur.trim().isEmpty) {
      return 'Le numéro CNIB est obligatoire';
    }
    if (valeur.trim().length > 20) {
      return 'Numéro CNIB trop long';
    }
    return null;
  }

  static String? numeroRecepisse(String? valeur) {
    if (valeur == null || valeur.trim().isEmpty) {
      return 'Le numéro de récépissé est obligatoire';
    }
    if (valeur.trim().length > 20) {
      return 'Numéro de récépissé trop long';
    }
    return null;
  }

  static String? codeOtp(String? valeur) {
    if (valeur == null || valeur.trim().length != 6) {
      return 'Le code doit contenir 6 chiffres';
    }
    if (!RegExp(r'^\d{6}$').hasMatch(valeur.trim())) {
      return 'Le code ne doit contenir que des chiffres';
    }
    return null;
  }

  static String? nomComplet(String? valeur) {
    if (valeur == null || valeur.trim().isEmpty) {
      return 'Le nom complet est obligatoire';
    }
    return null;
  }
}
