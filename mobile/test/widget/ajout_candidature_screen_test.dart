import 'package:faso_resultats_mobile/features/candidatures/domain/candidature.dart';
import 'package:faso_resultats_mobile/features/candidatures/domain/candidatures_repository.dart';
import 'package:faso_resultats_mobile/features/candidatures/presentation/ajout_candidature_screen.dart';
import 'package:faso_resultats_mobile/features/candidatures/presentation/candidatures_providers.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/administration.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/consultation_repository.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/examen.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/resultat.dart';
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
  Future<List<Resultat>> rechercherResultats({
    required String examenId,
    required String numeroPv,
    String? jury,
  }) async =>
      [];
}

/// Le récépissé saisi pilote la décision de vérification renvoyée, pour
/// exercer les trois chemins possibles côté écran sans dépendre du réseau.
class _FakeCandidaturesRepository implements CandidaturesRepository {
  bool confirmerOtpAppelee = false;

  @override
  Future<List<Candidature>> lister() async => [];

  @override
  Future<Candidature> creer({
    required String administrationId,
    required String examenId,
    required String numeroRecepisse,
  }) async {
    if (numeroRecepisse == 'OTP') {
      return const Candidature(
        id: 'c-otp',
        administrationId: 'admin-1',
        examenId: 'examen-1',
        numeroRecepisse: 'OTP',
        statutVerification: StatutVerificationCandidature.enAttente,
        methodeVerification: 'OTP_SMS',
        codeOtpDebug: '654321',
      );
    }
    return const Candidature(
      id: 'c-auto',
      administrationId: 'admin-1',
      examenId: 'examen-1',
      numeroRecepisse: '000123',
      statutVerification: StatutVerificationCandidature.verifieAuto,
      methodeVerification: 'CNIB_MATCH_AUTO',
      dernierResultatStatut: 'ADMIS',
    );
  }

  @override
  Future<Candidature> confirmerOtp({
    required String candidatureId,
    required String code,
  }) async {
    confirmerOtpAppelee = true;
    return const Candidature(
      id: 'c-otp',
      administrationId: 'admin-1',
      examenId: 'examen-1',
      numeroRecepisse: 'OTP',
      statutVerification: StatutVerificationCandidature.verifieManuel,
      methodeVerification: 'VALIDATION_MANUELLE',
    );
  }

  @override
  Future<void> retirer(String candidatureId) async {}
}

Widget construireApp(CandidaturesRepository candidaturesRepository) {
  return ProviderScope(
    overrides: [
      candidaturesRepositoryProvider.overrideWithValue(candidaturesRepository),
      consultationRepositoryProvider
          .overrideWithValue(_FakeConsultationRepository()),
    ],
    child: MaterialApp(
      home: Builder(
        builder: (context) => Scaffold(
          body: Center(
            child: ElevatedButton(
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute<void>(
                    builder: (_) => const AjoutCandidatureScreen()),
              ),
              child: const Text('Ouvrir'),
            ),
          ),
        ),
      ),
    ),
  );
}

Future<void> _remplirEtSoumettre(
    WidgetTester tester, String numeroRecepisse) async {
  await tester.tap(find.text('Ouvrir'));
  await tester.pumpAndSettle();

  await tester.tap(find.byType(DropdownButtonFormField<String>).first);
  await tester.pumpAndSettle();
  await tester.tap(find.text('OCECOS').last);
  await tester.pumpAndSettle();

  await tester.tap(find.byType(DropdownButtonFormField<String>).at(1));
  await tester.pumpAndSettle();
  await tester.tap(find.text('2026 — BAC 2026').last);
  await tester.pumpAndSettle();

  await tester.enterText(
      find.widgetWithText(TextFormField, 'Numéro de récépissé'),
      numeroRecepisse);
  await tester.tap(find.text('Ajouter'));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets(
      "une candidature vérifiée automatiquement ferme l'écran avec un message de succès",
      (tester) async {
    await tester.pumpWidget(construireApp(_FakeCandidaturesRepository()));

    await _remplirEtSoumettre(tester, '000123');

    expect(find.text('Candidature vérifiée avec succès.'), findsOneWidget);
    expect(find.text('Ouvrir'), findsOneWidget);
  });

  testWidgets(
      'une candidature nécessitant le mécanisme 3 navigue vers la confirmation OTP',
      (tester) async {
    await tester.pumpWidget(construireApp(_FakeCandidaturesRepository()));

    await _remplirEtSoumettre(tester, 'OTP');

    expect(find.text('Confirmer la candidature'), findsOneWidget);
    final champ = tester.widget<TextFormField>(find.byType(TextFormField));
    expect(champ.controller!.text, '654321');
  });
}
