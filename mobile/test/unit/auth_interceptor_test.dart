import 'package:dio/dio.dart';
import 'package:faso_resultats_mobile/core/network/interceptors/auth_interceptor.dart';
import 'package:faso_resultats_mobile/core/storage/secure_storage.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';

/// `FlutterSecureStorage.setMockInitialValues` (utilitaire fourni par le
/// package, `@visibleForTesting`) permet de tester `AuthInterceptor` sans
/// toucher au vrai Keystore/Keychain, indisponible en environnement de test.
SecureStorage _secureStorageAvec(Map<String, String> valeurs) {
  FlutterSecureStorage.setMockInitialValues(valeurs);
  return SecureStorage(const FlutterSecureStorage());
}

void main() {
  group('AuthInterceptor', () {
    test('onRequest ajoute le header Authorization quand un token existe',
        () async {
      final secureStorage =
          _secureStorageAvec({'faso_candidat_token': 'token-abc'});
      final interceptor = AuthInterceptor(secureStorage);
      final options = RequestOptions(path: '/candidat/me');

      final dio = Dio(BaseOptions(baseUrl: 'https://api.test'))
        ..httpClientAdapter = _AdaptateurCapture((captees) {
          expect(captees.headers['Authorization'], 'Bearer token-abc');
        })
        ..interceptors.add(interceptor);

      await dio.get<void>(options.path);
    });

    test("onRequest n'ajoute rien quand aucun token n'existe", () async {
      final secureStorage = _secureStorageAvec({});
      final interceptor = AuthInterceptor(secureStorage);

      final dio = Dio(BaseOptions(baseUrl: 'https://api.test'))
        ..httpClientAdapter = _AdaptateurCapture((captees) {
          expect(captees.headers.containsKey('Authorization'), isFalse);
        })
        ..interceptors.add(interceptor);

      await dio.get<void>('/public/administrations');
    });

    test('onError sur 401 supprime le token et notifie onNonAutorise',
        () async {
      final secureStorage =
          _secureStorageAvec({'faso_candidat_token': 'token-abc'});
      var notifiee = false;
      final interceptor = AuthInterceptor(
        secureStorage,
        onNonAutorise: () async => notifiee = true,
      );

      final dio = Dio(BaseOptions(baseUrl: 'https://api.test'))
        ..httpClientAdapter = _FakeHttpClientAdapter(
            (options) => ResponseBody.fromString('{}', 401))
        ..interceptors.add(interceptor);

      await expectLater(
          dio.get<void>('/candidat/me'), throwsA(isA<DioException>()));

      expect(notifiee, isTrue);
      expect(await secureStorage.lireToken(), isNull);
    });

    test('onError sur une erreur non-401 ne touche pas au token', () async {
      final secureStorage =
          _secureStorageAvec({'faso_candidat_token': 'token-abc'});
      var notifiee = false;
      final interceptor = AuthInterceptor(
        secureStorage,
        onNonAutorise: () async => notifiee = true,
      );

      final dio = Dio(BaseOptions(baseUrl: 'https://api.test'))
        ..httpClientAdapter = _FakeHttpClientAdapter(
            (options) => ResponseBody.fromString('{}', 500))
        ..interceptors.add(interceptor);

      await expectLater(
          dio.get<void>('/candidat/me'), throwsA(isA<DioException>()));

      expect(notifiee, isFalse);
      expect(await secureStorage.lireToken(), 'token-abc');
    });
  });
}

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

class _AdaptateurCapture implements HttpClientAdapter {
  _AdaptateurCapture(this._verifier);

  final void Function(RequestOptions options) _verifier;

  @override
  Future<ResponseBody> fetch(RequestOptions options,
      Stream<List<int>>? requestStream, Future<void>? cancelFuture) async {
    _verifier(options);
    return ResponseBody.fromString('{}', 200);
  }

  @override
  void close({bool force = false}) {}
}
