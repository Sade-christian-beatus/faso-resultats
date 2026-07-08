import 'package:dio/dio.dart';
import 'package:faso_resultats_mobile/config/constants.dart';
import 'package:faso_resultats_mobile/core/errors/exceptions.dart';
import 'package:faso_resultats_mobile/core/storage/secure_storage.dart';
import 'package:faso_resultats_mobile/features/profil_candidat/data/profil_candidat_repository_impl.dart';
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

const _profilJson = '''
{
  "id": "p-1",
  "nom_complet": "TRAORE Awa",
  "telephone_verifie": true,
  "email": "awa@example.bf",
  "email_verifie": false,
  "notifications_sms": true,
  "notifications_push": false,
  "notifications_email": false,
  "statut": "ACTIF",
  "derniere_connexion": null
}
''';

SecureStorage _secureStorageAvecToken() {
  FlutterSecureStorage.setMockInitialValues({'faso_candidat_token': 'jwt-abc'});
  return SecureStorage(const FlutterSecureStorage());
}

void main() {
  group('ProfilCandidatRepositoryImpl', () {
    test('obtenir convertit la réponse JSON', () async {
      final dio = Dio(BaseOptions(baseUrl: 'https://api.test'))
        ..httpClientAdapter = _FakeHttpClientAdapter((options) {
          expect(options.path, ApiPaths.candidatMe);
          return _reponseJson(_profilJson, 200);
        });
      final repository =
          ProfilCandidatRepositoryImpl(dio, _secureStorageAvecToken());

      final profil = await repository.obtenir();

      expect(profil.nomComplet, 'TRAORE Awa');
      expect(profil.telephoneVerifie, isTrue);
    });

    test("mettreAJour n'envoie que les champs fournis", () async {
      final dio = Dio(BaseOptions(baseUrl: 'https://api.test'))
        ..httpClientAdapter = _FakeHttpClientAdapter((options) {
          expect(options.method, 'PATCH');
          expect(options.data, {'notifications_sms': false});
          return _reponseJson(_profilJson, 200);
        });
      final repository =
          ProfilCandidatRepositoryImpl(dio, _secureStorageAvecToken());

      await repository.mettreAJour(notificationsSms: false);
    });

    test('exporter convertit candidatures et journal', () async {
      final dio = Dio(BaseOptions(baseUrl: 'https://api.test'))
        ..httpClientAdapter = _FakeHttpClientAdapter((options) {
          expect(options.path, ApiPaths.candidatMeExport);
          return _reponseJson('''
          {
            "numero_cnib": "B14863543",
            "nom_complet": "TRAORE Awa",
            "date_naissance": "2000-01-01",
            "telephone": "+22670000001",
            "consentement_apdp_date": "2026-01-01T00:00:00Z",
            "consentement_apdp_version": "v1",
            "created_at": "2026-01-01T00:00:00Z",
            "candidatures": [
              {"numero_recepisse": "000123", "statut_verification": "VERIFIE_AUTO", "created_at": "2026-01-02T00:00:00Z"}
            ],
            "journal": [
              {"action": "LOGIN", "ip": "1.2.3.4", "timestamp": "2026-01-03T00:00:00Z"}
            ]
          }
          ''', 200);
        });
      final repository =
          ProfilCandidatRepositoryImpl(dio, _secureStorageAvecToken());

      final export = await repository.exporter();

      expect(export.candidatures, hasLength(1));
      expect(export.candidatures.single.numeroRecepisse, '000123');
      expect(export.journal.single.action, 'LOGIN');
    });

    test('supprimerCompte efface le token stocké', () async {
      final secureStorage = _secureStorageAvecToken();
      final dio = Dio(BaseOptions(baseUrl: 'https://api.test'))
        ..httpClientAdapter =
            _FakeHttpClientAdapter((options) => _reponseJson('', 204));
      final repository = ProfilCandidatRepositoryImpl(dio, secureStorage);

      await repository.supprimerCompte();

      expect(await secureStorage.lireToken(), isNull);
    });

    test('une erreur réseau lève ReseauException', () async {
      final dio = Dio(BaseOptions(baseUrl: 'https://api.test'))
        ..httpClientAdapter = _FakeHttpClientAdapter((options) {
          throw DioException.connectionError(
              requestOptions: options, reason: 'perdu');
        });
      final repository =
          ProfilCandidatRepositoryImpl(dio, _secureStorageAvecToken());

      expect(repository.obtenir, throwsA(isA<ReseauException>()));
    });
  });
}
