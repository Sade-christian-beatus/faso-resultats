import 'package:dio/dio.dart';

import '../../../config/constants.dart';
import '../../../core/errors/exceptions.dart';
import '../domain/candidature.dart';
import '../domain/candidatures_repository.dart';
import 'candidature_mapper.dart';

class CandidaturesRepositoryImpl implements CandidaturesRepository {
  CandidaturesRepositoryImpl(this._dio);

  final Dio _dio;

  @override
  Future<List<Candidature>> lister() async {
    try {
      final reponse =
          await _dio.get<List<dynamic>>(ApiPaths.candidatCandidatures);
      return reponse.data!
          .cast<Map<String, dynamic>>()
          .map((json) => json.versCandidature())
          .toList();
    } on DioException catch (erreur) {
      _lancerExceptionAdaptee(erreur);
    }
  }

  @override
  Future<void> retirer(String candidatureId) async {
    try {
      await _dio.delete<void>(ApiPaths.candidature(candidatureId));
    } on DioException catch (erreur) {
      _lancerExceptionAdaptee(erreur);
    }
  }

  Never _lancerExceptionAdaptee(DioException erreur) {
    final estReseau = erreur.type == DioExceptionType.connectionTimeout ||
        erreur.type == DioExceptionType.receiveTimeout ||
        erreur.type == DioExceptionType.connectionError;
    if (estReseau) {
      throw const ReseauException(
        'Connexion impossible. Vérifiez votre accès internet et réessayez.',
      );
    }
    throw ServerException(
      'Une erreur est survenue. Veuillez réessayer.',
      statusCode: erreur.response?.statusCode,
    );
  }
}
