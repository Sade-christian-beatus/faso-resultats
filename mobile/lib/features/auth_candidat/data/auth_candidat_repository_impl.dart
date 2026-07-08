import 'package:dio/dio.dart';

import '../../../config/constants.dart';
import '../../../core/errors/exceptions.dart';
import '../../../core/storage/secure_storage.dart';
import '../../../core/utils/date_formatter.dart';
import '../domain/auth_candidat_repository.dart';
import '../domain/session_candidat.dart';

class AuthCandidatRepositoryImpl implements AuthCandidatRepository {
  AuthCandidatRepositoryImpl(this._dio, this._secureStorage);

  final Dio _dio;
  final SecureStorage _secureStorage;

  @override
  Future<String?> inscrire({
    required String numeroCnib,
    required String nomComplet,
    required DateTime dateNaissance,
    required String telephone,
    required String consentementApdpVersion,
  }) async {
    try {
      final reponse = await _dio.post<Map<String, dynamic>>(
        ApiPaths.candidatInscription,
        data: {
          'numero_cnib': numeroCnib,
          'nom_complet': nomComplet,
          'date_naissance': DateFormatter.pourApi(dateNaissance),
          'telephone': telephone,
          'consentement_apdp': true,
          'consentement_apdp_version': consentementApdpVersion,
        },
      );
      return reponse.data!['code_otp_debug'] as String?;
    } on DioException catch (erreur) {
      _lancerExceptionAdaptee(erreur);
    }
  }

  @override
  Future<String?> demanderConnexion(String telephone) async {
    try {
      final reponse = await _dio.post<Map<String, dynamic>>(
        ApiPaths.candidatLogin,
        data: {'telephone': telephone},
      );
      return reponse.data!['code_otp_debug'] as String?;
    } on DioException catch (erreur) {
      _lancerExceptionAdaptee(erreur);
    }
  }

  @override
  Future<SessionCandidat> validerOtp(
      {required String telephone, required String code}) async {
    try {
      final reponse = await _dio.post<Map<String, dynamic>>(
        ApiPaths.candidatOtpVerify,
        data: {'telephone': telephone, 'code': code},
      );
      final session = SessionCandidat(
        accessToken: reponse.data!['access_token'] as String,
        compteCree: reponse.data!['compte_cree'] as bool,
      );
      await _secureStorage.ecrireToken(session.accessToken);
      return session;
    } on DioException catch (erreur) {
      if (erreur.response?.statusCode == 401) {
        throw const AuthentificationException(
            'Code invalide ou expiré. Veuillez réessayer.');
      }
      _lancerExceptionAdaptee(erreur);
    }
  }

  @override
  Future<bool> estConnecte() async {
    return await _secureStorage.lireToken() != null;
  }

  @override
  Future<void> deconnecter() => _secureStorage.supprimerToken();

  Never _lancerExceptionAdaptee(DioException erreur) {
    final estReseau = erreur.type == DioExceptionType.connectionTimeout ||
        erreur.type == DioExceptionType.receiveTimeout ||
        erreur.type == DioExceptionType.connectionError;
    if (estReseau) {
      throw const ReseauException(
        'Connexion impossible. Vérifiez votre accès internet et réessayez.',
      );
    }
    if (erreur.response?.statusCode == 429) {
      throw const ServerException(
        'Trop de tentatives. Merci de patienter avant de réessayer.',
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
