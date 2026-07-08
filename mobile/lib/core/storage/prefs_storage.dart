import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Préférences non sensibles (langue, préférences UI) — jamais de données
/// personnelles ici, voir secure_storage.dart pour le token.
class PrefsStorage {
  PrefsStorage(this._prefs);

  final SharedPreferences _prefs;

  static const _cleLangue = 'faso_langue';
  static const _cleConsentementVersion = 'faso_consentement_version';
  static const _cleConsentementDate = 'faso_consentement_date';

  String? get langue => _prefs.getString(_cleLangue);

  Future<void> ecrireLangue(String code) => _prefs.setString(_cleLangue, code);

  String? get versionConsentementAcceptee =>
      _prefs.getString(_cleConsentementVersion);

  DateTime? get dateConsentementAcceptee {
    final valeur = _prefs.getString(_cleConsentementDate);
    return valeur == null ? null : DateTime.tryParse(valeur);
  }

  /// Bandeau d'information affiché à la première ouverture (jour 8) :
  /// version et horodatage enregistrés ensemble pour ne jamais avoir l'un
  /// sans l'autre.
  Future<void> enregistrerConsentement(String version) async {
    await _prefs.setString(_cleConsentementVersion, version);
    await _prefs.setString(
        _cleConsentementDate, DateTime.now().toIso8601String());
  }
}

final sharedPreferencesProvider = Provider<SharedPreferences>((ref) {
  throw UnimplementedError(
    'Doit être surchargé dans main() via overrideWithValue',
  );
});

final prefsStorageProvider = Provider<PrefsStorage>((ref) {
  return PrefsStorage(ref.watch(sharedPreferencesProvider));
});
