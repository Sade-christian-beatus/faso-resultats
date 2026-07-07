import 'package:dio/dio.dart';

/// Une seule tentative de nouvelle requête sur erreur réseau transitoire
/// (timeout, connexion perdue) — pertinent sur la 3G instable visée par ce
/// projet (CLAUDE.md § 3). Ne retente jamais sur une erreur serveur (4xx/5xx
/// avec réponse reçue) : ce n'est pas transitoire, retenter n'aiderait pas.
class RetryInterceptor extends Interceptor {
  RetryInterceptor(this._dio);

  final Dio _dio;

  static const _cleDejaTente = 'faso_retry_tente';

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final estTransitoire = err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.receiveTimeout ||
        err.type == DioExceptionType.connectionError;
    final dejaTente = err.requestOptions.extra[_cleDejaTente] == true;

    if (estTransitoire && !dejaTente) {
      try {
        final options = err.requestOptions;
        options.extra[_cleDejaTente] = true;
        final reponse = await _dio.fetch<dynamic>(options);
        return handler.resolve(reponse);
      } on DioException catch (nouvelleErreur) {
        return handler.next(nouvelleErreur);
      }
    }
    handler.next(err);
  }
}
