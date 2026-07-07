import 'package:intl/intl.dart';

class DateFormatter {
  const DateFormatter._();

  static final _formatAffichage = DateFormat('dd/MM/yyyy', 'fr_FR');
  static final _formatIso = DateFormat('yyyy-MM-dd');

  static String pourAffichage(DateTime date) => _formatAffichage.format(date);

  /// Format attendu par l'API (`date` Pydantic, ISO 8601).
  static String pourApi(DateTime date) => _formatIso.format(date);

  static DateTime? depuisApi(String? valeur) {
    if (valeur == null || valeur.isEmpty) return null;
    return DateTime.tryParse(valeur);
  }
}
