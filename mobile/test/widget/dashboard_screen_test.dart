import 'package:faso_resultats_mobile/features/candidatures/domain/candidature.dart';
import 'package:faso_resultats_mobile/features/candidatures/domain/candidatures_repository.dart';
import 'package:faso_resultats_mobile/features/candidatures/presentation/candidatures_providers.dart';
import 'package:faso_resultats_mobile/features/candidatures/presentation/dashboard_screen.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/administration.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/consultation_repository.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/examen.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/parcours.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/presentation/consultation_providers.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _FakeConsultationRepository implements ConsultationRepository {
  @override
  Future<List<Administration>> listerAdministrations() async => [
        const Administration(
            id: 'admin-1',
            code: 'ocecos',
            nomOfficiel: 'OCECOS',
            sigle: 'OCECOS'),
      ];

  @override
  Future<List<Examen>> listerExamens() async => [
        const Examen(
          id: 'examen-1',
          administrationId: 'admin-1',
          typeExamen: 'BAC',
          annee: 2026,
          libelle: 'BAC 2026',
        ),
      ];

  @override
  Future<List<ParcoursCandidat>> rechercherParcours({
    required String examenId,
    required String numeroPv,
    String? jury,
  }) async =>
      [];
}

class _FakeCandidaturesRepository implements CandidaturesRepository {
  _FakeCandidaturesRepository(this.candidatures);

  List<Candidature> candidatures;
  bool retireeAppelee = false;

  @override
  Future<List<Candidature>> lister() async => candidatures;

  @override
  Future<Candidature> creer({
    required String administrationId,
    required String examenId,
    required String numeroRecepisse,
  }) async =>
      throw UnimplementedError();

  @override
  Future<Candidature> confirmerOtp({
    required String candidatureId,
    required String code,
  }) async =>
      throw UnimplementedError();

  @override
  Future<void> retirer(String candidatureId) async {
    retireeAppelee = true;
    candidatures = candidatures.where((c) => c.id != candidatureId).toList();
  }
}

const _candidatureVerifiee = Candidature(
  id: 'c-1',
  administrationId: 'admin-1',
  examenId: 'examen-1',
  numeroRecepisse: '000123',
  statutVerification: StatutVerificationCandidature.verifieAuto,
  dernierResultatStatut: 'ADMIS',
);

Widget construireApp(CandidaturesRepository candidaturesRepository) {
  return ProviderScope(
    overrides: [
      candidaturesRepositoryProvider.overrideWithValue(candidaturesRepository),
      consultationRepositoryProvider
          .overrideWithValue(_FakeConsultationRepository()),
    ],
    child: MaterialApp(
      home: const DashboardScreen(),
      routes: {'/profil': (_) => const Scaffold(body: Text('Profil'))},
    ),
  );
}

void main() {
  testWidgets(
      "affiche une candidature avec le nom de l'administration et de l'examen",
      (
    tester,
  ) async {
    await tester.pumpWidget(
        construireApp(_FakeCandidaturesRepository([_candidatureVerifiee])));
    await tester.pumpAndSettle();

    expect(find.text('OCECOS'), findsOneWidget);
    expect(find.text('BAC 2026'), findsOneWidget);
    expect(find.text('ADMIS'), findsOneWidget);
  });

  testWidgets('affiche un message quand aucune candidature', (tester) async {
    await tester.pumpWidget(construireApp(_FakeCandidaturesRepository([])));
    await tester.pumpAndSettle();

    expect(find.text('Aucune candidature pour le moment.'), findsOneWidget);
  });

  testWidgets(
      'retirer une candidature après confirmation appelle le repository',
      (tester) async {
    final repository = _FakeCandidaturesRepository([_candidatureVerifiee]);
    await tester.pumpWidget(construireApp(repository));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Retirer'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Retirer').last);
    await tester.pumpAndSettle();

    expect(repository.retireeAppelee, isTrue);
  });
}
