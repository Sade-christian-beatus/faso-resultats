import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Préférences non sensibles (langue, préférences UI) — jamais de données
/// personnelles ici, voir secure_storage.dart pour le token.
class PrefsStorage {
  PrefsStorage(this._prefs);

  final SharedPreferences _prefs;

  static const _cleLangue = 'faso_langue';
  static const _cleConsentementVersion = 'faso_consentement_version';

  String? get langue => _prefs.getString(_cleLangue);

  Future<void> ecrireLangue(String code) => _prefs.setString(_cleLangue, code);

  String? get versionConsentementAcceptee =>
      _prefs.getString(_cleConsentementVersion);

  Future<void> ecrireVersionConsentement(String version) =>
      _prefs.setString(_cleConsentementVersion, version);
}

final sharedPreferencesProvider = Provider<SharedPreferences>((ref) {
  throw UnimplementedError(
    'Doit être surchargé dans main() via overrideWithValue',
  );
});

final prefsStorageProvider = Provider<PrefsStorage>((ref) {
  return PrefsStorage(ref.watch(sharedPreferencesProvider));
});
