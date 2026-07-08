import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Stockage chiffré (Keystore Android / Keychain iOS) — exclusivement pour le
/// token de session candidat. Jamais dans `shared_preferences` (prompt §
/// Sécurité : "Tokens JWT chiffrés, jamais en shared_preferences").
class SecureStorage {
  SecureStorage(this._storage);

  final FlutterSecureStorage _storage;

  Future<void> ecrireToken(String token) =>
      _storage.write(key: _cleToken, value: token);

  Future<String?> lireToken() => _storage.read(key: _cleToken);

  Future<void> supprimerToken() => _storage.delete(key: _cleToken);

  static const _cleToken = 'faso_candidat_token';
}

final secureStorageProvider = Provider<SecureStorage>((ref) {
  return SecureStorage(const FlutterSecureStorage());
});
