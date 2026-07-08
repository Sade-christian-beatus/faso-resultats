import 'package:dio/dio.dart';
import 'package:faso_resultats_mobile/core/network/interceptors/retry_interceptor.dart';
import 'package:flutter_test/flutter_test.dart';

class _FakeHttpClientAdapter implements HttpClientAdapter {
  _FakeHttpClientAdapter(this._repondre);

  final ResponseBody Function(RequestOptions options) _repondre;
  int appels = 0;

  @override
  Future<ResponseBody> fetch(RequestOptions options,
      Stream<List<int>>? requestStream, Future<void>? cancelFuture) async {
    appels++;
    return _repondre(options);
  }

  @override
  void close({bool force = false}) {}
}

void main() {
  group('RetryInterceptor', () {
    test('retente une seule fois sur une erreur de connexion transitoire',
        () async {
      var appels = 0;
      final dio = Dio(BaseOptions(baseUrl: 'https://api.test'))
        ..httpClientAdapter = _AdaptateurConnexionPuisSucces(() => appels++);
      dio.interceptors.add(RetryInterceptor(dio));

      final reponse = await dio.get<String>('/public/administrations');

      expect(reponse.statusCode, 200);
      expect(appels, 2); // 1er appel (échec) + 1 nouvelle tentative (succès).
    });

    test(
        'ne retente pas une deuxième fois si la nouvelle tentative échoue '
        'aussi', () async {
      final adaptateur = _FakeHttpClientAdapter(
        (options) => throw DioException.connectionError(
          requestOptions: options,
          reason: 'connexion perdue',
        ),
      );
      final dio = Dio(BaseOptions(baseUrl: 'https://api.test'))
        ..httpClientAdapter = adaptateur;
      dio.interceptors.add(RetryInterceptor(dio));

      await expectLater(
        dio.get<void>('/public/administrations'),
        throwsA(isA<DioException>()),
      );
      expect(adaptateur.appels, 2); // 1er appel + 1 seule nouvelle tentative.
    });

    test('ne retente jamais sur une erreur serveur (réponse 500 reçue)',
        () async {
      final adaptateur =
          _FakeHttpClientAdapter((options) => ResponseBody.fromString(
                '{"detail":"panne"}',
                500,
                headers: {
                  Headers.contentTypeHeader: [Headers.jsonContentType],
                },
              ));
      final dio = Dio(BaseOptions(baseUrl: 'https://api.test'))
        ..httpClientAdapter = adaptateur;
      dio.interceptors.add(RetryInterceptor(dio));

      await expectLater(
        dio.get<void>('/public/administrations'),
        throwsA(isA<DioException>()),
      );
      expect(adaptateur.appels, 1);
    });
  });
}

/// Simule une première tentative qui échoue par timeout, puis une seconde
/// (la nouvelle tentative de `RetryInterceptor`) qui réussit.
class _AdaptateurConnexionPuisSucces implements HttpClientAdapter {
  _AdaptateurConnexionPuisSucces(this._surAppel);

  final void Function() _surAppel;
  int _appels = 0;

  @override
  Future<ResponseBody> fetch(RequestOptions options,
      Stream<List<int>>? requestStream, Future<void>? cancelFuture) async {
    _surAppel();
    _appels++;
    if (_appels == 1) {
      throw DioException.connectionError(
        requestOptions: options,
        reason: 'connexion perdue',
      );
    }
    return ResponseBody.fromString(
      '[]',
      200,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}
