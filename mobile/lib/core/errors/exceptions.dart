/// Exceptions levées par la couche data (repositories, clients HTTP) et
/// remontées telles quelles jusqu'à la couche presentation via
/// `AsyncValue.error` (les notifiers Riverpod codegen font ce travail sans
/// try/catch explicite) : pas besoin d'un type Either/Result générique pour
/// ce projet. `AppException` donne à la presentation un point d'accès commun
/// au message déjà en français, prêt à afficher.
abstract interface class AppException implements Exception {
  String get message;
}

class ServerException implements AppException {
  const ServerException(this.message, {this.statusCode});

  @override
  final String message;
  final int? statusCode;
}

class ReseauException implements AppException {
  const ReseauException(this.message);

  @override
  final String message;
}

class CacheException implements AppException {
  const CacheException(this.message);

  @override
  final String message;
}

class AuthentificationException implements AppException {
  const AuthentificationException(this.message);

  @override
  final String message;
}
