import 'package:dio/dio.dart';

import '../../../config/constants.dart';
import '../../../core/errors/exceptions.dart';
import '../../../core/storage/secure_storage.dart';
import '../domain/profil_candidat.dart';
import '../domain/profil_candidat_export.dart';
import '../domain/profil_candidat_repository.dart';
import 'profil_candidat_mapper.dart';

class ProfilCandidatRepositoryImpl implements ProfilCandidatRepository {
  ProfilCandidatRepositoryImpl(this._dio, this._secureStorage);

  final Dio _dio;
  final SecureStorage _secureStorage;

  @override
  Future<ProfilCandidat> obtenir() async {
    try {
      final reponse = await _dio.get<Map<String, dynamic>>(ApiPaths.candidatMe);
      return reponse.data!.versProfilCandidat();
    } on DioException catch (erreur) {
      _lancerExceptionAdaptee(erreur);
    }
  }

  @override
  Future<ProfilCandidat> mettreAJour({
    String? email,
    bool? notificationsSms,
    bool? notificationsPush,
    bool? notificationsEmail,
  }) async {
    try {
      final reponse = await _dio.patch<Map<String, dynamic>>(
        ApiPaths.candidatMe,
        data: {
          if (email != null) 'email': email,
          if (notificationsSms != null) 'notifications_sms': notificationsSms,
          if (notificationsPush != null)
            'notifications_push': notificationsPush,
          if (notificationsEmail != null)
            'notifications_email': notificationsEmail,
        },
      );
      return reponse.data!.versProfilCandidat();
    } on DioException catch (erreur) {
      _lancerExceptionAdaptee(erreur);
    }
  }

  @override
  Future<ProfilCandidatExport> exporter() async {
    try {
      final reponse =
          await _dio.get<Map<String, dynamic>>(ApiPaths.candidatMeExport);
      return reponse.data!.versProfilCandidatExport();
    } on DioException catch (erreur) {
      _lancerExceptionAdaptee(erreur);
    }
  }

  @override
  Future<void> supprimerCompte() async {
    try {
      await _dio.delete<void>(ApiPaths.candidatMe);
      await _secureStorage.supprimerToken();
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
