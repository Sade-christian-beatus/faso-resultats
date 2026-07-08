import 'package:dio/dio.dart';
import 'package:faso_resultats_mobile/config/constants.dart';
import 'package:faso_resultats_mobile/core/errors/exceptions.dart';
import 'package:faso_resultats_mobile/core/storage/secure_storage.dart';
import 'package:faso_resultats_mobile/features/auth_candidat/data/auth_candidat_repository_impl.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';

class _FakeHttpClientAdapter implements HttpClientAdapter {
  _FakeHttpClientAdapter(this._repondre);

  final ResponseBody Function(RequestOptions options) _repondre;

  @override
  Future<ResponseBody> fetch(RequestOptions options,
          Stream<List<int>>? requestStream, Future<void>? cancelFuture) async =>
      _repondre(options);

  @override
  void close({bool force = false}) {}
}

ResponseBody _reponseJson(String jsonTexte, int statusCode) =>
    ResponseBody.fromString(
      jsonTexte,
      statusCode,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );

Dio _dioAvec(ResponseBody Function(RequestOptions options) repondre) {
  return Dio(BaseOptions(baseUrl: 'https://api.test'))
    ..httpClientAdapter = _FakeHttpClientAdapter(repondre);
}

SecureStorage _secureStorageVide() {
  FlutterSecureStorage.setMockInitialValues({});
  return SecureStorage(const FlutterSecureStorage());
}

void main() {
  group('AuthCandidatRepositoryImpl', () {
    test('inscrire renvoie le code de debug hors production', () async {
      final dio = _dioAvec((options) {
        expect(options.path, ApiPaths.candidatInscription);
        final data = options.data as Map<String, dynamic>;
        expect(data['numero_cnib'], 'B14863543');
        expect(data['date_naissance'], '2000-01-01');
        return _reponseJson('{"code_otp_debug":"123456"}', 201);
      });
      final repository = AuthCandidatRepositoryImpl(dio, _secureStorageVide());

      final code = await repository.inscrire(
        numeroCnib: 'B14863543',
        nomComplet: 'TRAORE Awa',
        dateNaissance: DateTime(2000),
        telephone: '+22670000001',
        consentementApdpVersion: 'v1',
      );

      expect(code, '123456');
    });

    test('demanderConnexion appelle le bon endpoint', () async {
      final dio = _dioAvec((options) {
        expect(options.path, ApiPaths.candidatLogin);
        return _reponseJson('{"code_otp_debug":null}', 200);
      });
      final repository = AuthCandidatRepositoryImpl(dio, _secureStorageVide());

      final code = await repository.demanderConnexion('+22670000001');

      expect(code, isNull);
    });

    test('validerOtp stocke le token reçu dans le stockage sécurisé', () async {
      final dio = _dioAvec((options) =>
          _reponseJson('{"access_token":"jwt-abc","compte_cree":false}', 200));
      final secureStorage = _secureStorageVide();
      final repository = AuthCandidatRepositoryImpl(dio, secureStorage);

      final session = await repository.validerOtp(
          telephone: '+22670000001', code: '123456');

      expect(session.accessToken, 'jwt-abc');
      expect(await secureStorage.lireToken(), 'jwt-abc');
    });

    test('validerOtp sur 401 lève AuthentificationException', () async {
      final dio = _dioAvec((options) =>
          _reponseJson('{"detail":"Code invalide ou expiré"}', 401));
      final repository = AuthCandidatRepositoryImpl(dio, _secureStorageVide());

      expect(
        () => repository.validerOtp(telephone: '+22670000001', code: '000000'),
        throwsA(isA<AuthentificationException>()),
      );
    });

    test('une erreur 429 lève ServerException avec un message de patience',
        () async {
      final dio = _dioAvec((options) => _reponseJson('{"detail":"trop"}', 429));
      final repository = AuthCandidatRepositoryImpl(dio, _secureStorageVide());

      expect(
        () => repository.demanderConnexion('+22670000001'),
        throwsA(isA<ServerException>().having(
            (e) => e.message, 'message', contains('Trop de tentatives'))),
      );
    });

    test('estConnecte reflète la présence du token', () async {
      final secureStorage = _secureStorageVide();
      final dio = _dioAvec((options) => _reponseJson('{}', 200));
      final repository = AuthCandidatRepositoryImpl(dio, secureStorage);

      expect(await repository.estConnecte(), isFalse);

      await secureStorage.ecrireToken('jwt-abc');
      expect(await repository.estConnecte(), isTrue);
    });

    test('deconnecter supprime le token stocké', () async {
      final secureStorage = _secureStorageVide();
      await secureStorage.ecrireToken('jwt-abc');
      final dio = _dioAvec((options) => _reponseJson('{}', 200));
      final repository = AuthCandidatRepositoryImpl(dio, secureStorage);

      await repository.deconnecter();

      expect(await secureStorage.lireToken(), isNull);
    });
  });
}
