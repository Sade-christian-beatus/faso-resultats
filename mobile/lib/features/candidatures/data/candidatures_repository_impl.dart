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
  Future<Candidature> creer({
    required String administrationId,
    required String examenId,
    required String numeroRecepisse,
  }) async {
    try {
      final reponse = await _dio.post<Map<String, dynamic>>(
        ApiPaths.candidatCandidatures,
        data: {
          'administration_id': administrationId,
          'examen_id': examenId,
          'numero_recepisse': numeroRecepisse,
        },
      );
      return reponse.data!.versCandidature();
    } on DioException catch (erreur) {
      _lancerExceptionAdaptee(erreur);
    }
  }

  @override
  Future<Candidature> confirmerOtp({
    required String candidatureId,
    required String code,
  }) async {
    try {
      final reponse = await _dio.post<Map<String, dynamic>>(
        ApiPaths.candidatureConfirmerOtp(candidatureId),
        data: {'code': code},
      );
      return reponse.data!.versCandidature();
    } on DioException catch (erreur) {
      if (erreur.response?.statusCode == 401) {
        throw const AuthentificationException(
            'Code invalide ou expiré. Veuillez réessayer.');
      }
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
    final detail = erreur.response?.data is Map
        ? (erreur.response!.data as Map)['detail'] as String?
        : null;
    throw ServerException(
      detail ?? 'Une erreur est survenue. Veuillez réessayer.',
      statusCode: erreur.response?.statusCode,
    );
  }
}
