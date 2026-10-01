import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:dio_cache_interceptor/dio_cache_interceptor.dart';
import 'package:faso_resultats_mobile/config/constants.dart';
import 'package:faso_resultats_mobile/core/errors/exceptions.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/data/consultation_repository_impl.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/parcours.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/resultat.dart';
import 'package:flutter_test/flutter_test.dart';

/// Adaptateur Dio factice (jour 10) : plutôt qu'un mock généré (mockito,
/// écarté du projet — voir mobile/docs/ARCHITECTURE.md), une implémentation
/// manuelle de `HttpClientAdapter`, cohérente avec le reste des tests de ce
/// projet (fakes écrits à la main contre des interfaces).
class _FakeHttpClientAdapter implements HttpClientAdapter {
  _FakeHttpClientAdapter(this._repondre);

  final ResponseBody Function(RequestOptions options) _repondre;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async =>
      _repondre(options);

  @override
  void close({bool force = false}) {}
}

ResponseBody _reponseJson(Object data, int statusCode) =>
    ResponseBody.fromString(
      jsonEncode(data),
      statusCode,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );

Dio _dioAvec(ResponseBody Function(RequestOptions options) repondre) {
  return Dio(BaseOptions(baseUrl: 'https://api.test'))
    ..httpClientAdapter = _FakeHttpClientAdapter(repondre);
}

void main() {
  group('ConsultationRepositoryImpl', () {
    test('listerAdministrations convertit la réponse JSON', () async {
      final dio = _dioAvec((options) {
        expect(options.path, ApiPaths.publicAdministrations);
        return _reponseJson([
          {
            'id': 'admin-1',
            'code': 'ocecos',
            'nom_officiel': 'OCECOS',
            'sigle': 'OCECOS',
          },
        ], 200);
      });
      final repository = ConsultationRepositoryImpl(dio, MemCacheStore());

      final administrations = await repository.listerAdministrations();

      expect(administrations, hasLength(1));
      expect(administrations.single.nomOfficiel, 'OCECOS');
    });

    test('listerExamens convertit la réponse JSON', () async {
      final dio = _dioAvec((options) {
        expect(options.path, ApiPaths.publicExams);
        return _reponseJson([
          {
            'id': 'examen-1',
            'administration_id': 'admin-1',
            'type_examen': 'BAC',
            'annee': 2026,
            'libelle': 'BAC 2026',
          },
        ], 200);
      });
      final repository = ConsultationRepositoryImpl(dio, MemCacheStore());

      final examens = await repository.listerExamens();

      expect(examens, hasLength(1));
      expect(examens.single.annee, 2026);
    });

    test(
        'rechercherParcours interroge /results/progress et convertit les phases',
        () async {
      final dio = _dioAvec((options) {
        expect(options.path, ApiPaths.publicResultsProgress);
        expect(options.queryParameters, {
          'examen_id': 'examen-1',
          'numero_pv': '000015',
          'jury': '03',
        });
        return _reponseJson([
          {
            'numero_pv': '000015',
            'jury': '03',
            'etapes': [
              {
                'phase': 'EPREUVES_SPORTIVES',
                'statut_phase': 'CLOTUREE',
                'situation': 'RESULTAT',
                'resultat': {
                  'numero_pv': '000015',
                  'jury': '03',
                  'nom': 'BAYALA',
                  'prenom': 'Jean-Claude',
                  'decision': 'APTE',
                  'moyenne': null,
                  'etablissement': null,
                  'rang_numerique': null,
                  'rang_affiche': null,
                  'phase': 'EPREUVES_SPORTIVES',
                  'phase_suivante_attendue': 'ADMISSIBILITE',
                  'date_publication_phase': '2026-07-01T10:00:00Z',
                },
              },
              {
                'phase': 'ADMISSIBILITE',
                'statut_phase': 'EN_COURS',
                'situation': 'EN_ATTENTE',
                'resultat': null,
              },
              {
                'phase': 'ADMISSION_DEFINITIVE',
                'statut_phase': 'A_VENIR',
                'situation': 'A_VENIR',
                'resultat': null,
              },
            ],
          },
        ], 200);
      });
      final repository = ConsultationRepositoryImpl(dio, MemCacheStore());

      final liste = await repository.rechercherParcours(
          examenId: 'examen-1', numeroPv: '000015', jury: '03');

      final parcours = liste.single;
      expect(parcours.estPublicationUnique, isFalse);
      expect(parcours.identite!.nom, 'BAYALA');
      expect(parcours.etapes.map((e) => e.phase), [
        PhasePublication.epreuvesSportives,
        PhasePublication.admissibilite,
        PhasePublication.admissionDefinitive,
      ]);
      expect(parcours.etapes.map((e) => e.situation), [
        SituationCandidat.resultat,
        SituationCandidat.enAttente,
        SituationCandidat.aVenir,
      ]);
      expect(parcours.etapes[1].statutPhase, StatutPhase.enCours);
      expect(parcours.etapes.first.resultat!.datePublicationPhase,
          DateTime.utc(2026, 7, 1, 10));
    });

    test('rechercherParcours renvoie une liste vide sur 404 (aucun résultat)',
        () async {
      final dio =
          _dioAvec((options) => _reponseJson({'detail': 'introuvable'}, 404));
      final repository = ConsultationRepositoryImpl(dio, MemCacheStore());

      final parcours = await repository.rechercherParcours(
        examenId: 'examen-1',
        numeroPv: '000123',
      );

      expect(parcours, isEmpty);
    });

    test('une erreur serveur (500) lève ServerException', () async {
      final dio = _dioAvec((options) => _reponseJson({'detail': 'panne'}, 500));
      final repository = ConsultationRepositoryImpl(dio, MemCacheStore());

      expect(
        repository.listerAdministrations,
        throwsA(isA<ServerException>()),
      );
    });

    test('une erreur de connexion lève ReseauException', () async {
      final dio = Dio(BaseOptions(baseUrl: 'https://api.test'))
        ..httpClientAdapter = _FakeHttpClientAdapter((options) {
          throw DioException.connectionError(
            requestOptions: options,
            reason: 'connexion perdue',
          );
        });
      final repository = ConsultationRepositoryImpl(dio, MemCacheStore());

      expect(
        repository.listerAdministrations,
        throwsA(isA<ReseauException>()),
      );
    });
  });
}
