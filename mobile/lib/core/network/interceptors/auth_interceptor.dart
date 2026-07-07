import 'package:dio/dio.dart';

import '../../storage/secure_storage.dart';

/// Ajoute le token de session candidat à chaque requête, et notifie
/// [onNonAutorise] sur un 401 pour que la couche presentation puisse
/// déconnecter l'utilisateur (le client HTTP ne doit pas naviguer lui-même —
/// séparation des couches).
class AuthInterceptor extends Interceptor {
  AuthInterceptor(this._secureStorage, {this.onNonAutorise});

  final SecureStorage _secureStorage;
  final Future<void> Function()? onNonAutorise;

  @override
  Future<void> onRequest(
      RequestOptions options, RequestInterceptorHandler handler) async {
    final token = await _secureStorage.lireToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  Future<void> onError(
      DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      await _secureStorage.supprimerToken();
      await onNonAutorise?.call();
    }
    handler.next(err);
  }
}
