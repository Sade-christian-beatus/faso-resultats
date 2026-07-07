/// Exceptions levées par la couche data (repositories, clients HTTP) — jamais
/// vues par la couche presentation, qui ne connaît que les `Failure` (voir
/// failures.dart). Garde la séparation Clean Architecture sans complexité
/// excessive : un simple try/catch au niveau repository suffit, pas besoin
/// d'un type Either/Result générique pour ce projet.
class ServerException implements Exception {
  const ServerException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;
}

class ReseauException implements Exception {
  const ReseauException(this.message);

  final String message;
}

class CacheException implements Exception {
  const CacheException(this.message);

  final String message;
}

class AuthentificationException implements Exception {
  const AuthentificationException(this.message);

  final String message;
}
