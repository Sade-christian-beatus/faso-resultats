import 'package:dio/dio.dart';
import 'package:faso_resultats_mobile/config/constants.dart';
import 'package:faso_resultats_mobile/core/errors/exceptions.dart';
import 'package:faso_resultats_mobile/features/candidatures/data/candidatures_repository_impl.dart';
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

const _candidatureJson = '''
{
  "id": "c-1",
  "administration_id": "admin-1",
  "examen_id": "examen-1",
  "numero_recepisse": "000123",
  "statut_verification": "VERIFIE_AUTO",
  "methode_verification": "CNIB_MATCH_AUTO",
  "notifications_activees": true,
  "dernier_resultat_statut": "ADMIS",
  "dernier_resultat_phase": "RESULTAT_UNIQUE",
  "dernier_resultat_publie_at": null
}
''';

void main() {
  group('CandidaturesRepositoryImpl', () {
    test('lister convertit la liste JSON', () async {
      final dio = _dioAvec((options) {
        expect(options.path, ApiPaths.candidatCandidatures);
        return _reponseJson('[$_candidatureJson]', 200);
      });
      final repository = CandidaturesRepositoryImpl(dio);

      final candidatures = await repository.lister();

      expect(candidatures, hasLength(1));
      expect(candidatures.single.numeroRecepisse, '000123');
    });

    test(
        'creer envoie administration/examen/récépissé et convertit la '
        'réponse', () async {
      final dio = _dioAvec((options) {
        expect(options.path, ApiPaths.candidatCandidatures);
        expect(options.method, 'POST');
        expect(options.data, {
          'administration_id': 'admin-1',
          'examen_id': 'examen-1',
          'numero_recepisse': '000123',
        });
        return _reponseJson(_candidatureJson, 201);
      });
      final repository = CandidaturesRepositoryImpl(dio);

      final candidature = await repository.creer(
        administrationId: 'admin-1',
        examenId: 'examen-1',
        numeroRecepisse: '000123',
      );

      expect(candidature.id, 'c-1');
    });

    test('confirmerOtp appelle le bon endpoint avec le code', () async {
      final dio = _dioAvec((options) {
        expect(options.path, ApiPaths.candidatureConfirmerOtp('c-1'));
        expect(options.data, {'code': '123456'});
        return _reponseJson(_candidatureJson, 200);
      });
      final repository = CandidaturesRepositoryImpl(dio);

      await repository.confirmerOtp(candidatureId: 'c-1', code: '123456');
    });

    test('un récépissé rejeté (422) propage le message backend', () async {
      final dio = _dioAvec((options) => _reponseJson(
          '{"detail":"Ce récépissé ne correspond pas à votre identité."}',
          422));
      final repository = CandidaturesRepositoryImpl(dio);

      expect(
        () => repository.creer(
          administrationId: 'admin-1',
          examenId: 'examen-1',
          numeroRecepisse: '000999',
        ),
        throwsA(isA<ServerException>().having(
          (e) => e.message,
          'message',
          contains('ne correspond pas'),
        )),
      );
    });

    test('un récépissé déjà rattaché (409) propage le message backend',
        () async {
      final dio = _dioAvec((options) => _reponseJson(
          '{"detail":"Ce récépissé est déjà rattaché à un compte candidat"}',
          409));
      final repository = CandidaturesRepositoryImpl(dio);

      expect(
        () => repository.creer(
          administrationId: 'admin-1',
          examenId: 'examen-1',
          numeroRecepisse: '000123',
        ),
        throwsA(isA<ServerException>().having(
          (e) => e.statusCode,
          'statusCode',
          409,
        )),
      );
    });

    test('retirer appelle DELETE sur la candidature', () async {
      final dio = _dioAvec((options) {
        expect(options.path, ApiPaths.candidature('c-1'));
        expect(options.method, 'DELETE');
        return _reponseJson('', 204);
      });
      final repository = CandidaturesRepositoryImpl(dio);

      await repository.retirer('c-1');
    });
  });
}
