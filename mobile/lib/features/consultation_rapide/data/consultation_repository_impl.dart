import 'package:dio/dio.dart';

import '../../../config/constants.dart';
import '../../../core/errors/exceptions.dart';
import '../domain/administration.dart';
import '../domain/consultation_repository.dart';
import '../domain/examen.dart';
import '../domain/resultat.dart';
import 'administration_mapper.dart';
import 'examen_mapper.dart';
import 'resultat_mapper.dart';

class ConsultationRepositoryImpl implements ConsultationRepository {
  ConsultationRepositoryImpl(this._dio);

  final Dio _dio;

  @override
  Future<List<Administration>> listerAdministrations() async {
    try {
      final reponse =
          await _dio.get<List<dynamic>>(ApiPaths.publicAdministrations);
      return reponse.data!
          .cast<Map<String, dynamic>>()
          .map((json) => json.versAdministration())
          .toList();
    } on DioException catch (erreur) {
      _lancerExceptionAdaptee(erreur);
    }
  }

  @override
  Future<List<Examen>> listerExamens() async {
    try {
      final reponse = await _dio.get<List<dynamic>>(ApiPaths.publicExams);
      return reponse.data!
          .cast<Map<String, dynamic>>()
          .map((json) => json.versExamen())
          .toList();
    } on DioException catch (erreur) {
      _lancerExceptionAdaptee(erreur);
    }
  }

  @override
  Future<List<Resultat>> rechercherResultats({
    required String examenId,
    required String numeroPv,
    String? jury,
  }) async {
    try {
      final reponse = await _dio.get<List<dynamic>>(
        ApiPaths.publicResults,
        queryParameters: {
          'examen_id': examenId,
          'numero_pv': numeroPv,
          if (jury != null && jury.isNotEmpty) 'jury': jury,
        },
      );
      return reponse.data!
          .cast<Map<String, dynamic>>()
          .map((json) => json.versResultat())
          .toList();
    } on DioException catch (erreur) {
      if (erreur.response?.statusCode == 404) {
        return [];
      }
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
