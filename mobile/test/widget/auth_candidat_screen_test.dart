import 'package:faso_resultats_mobile/features/auth_candidat/domain/auth_candidat_repository.dart';
import 'package:faso_resultats_mobile/features/auth_candidat/domain/session_candidat.dart';
import 'package:faso_resultats_mobile/features/auth_candidat/presentation/auth_candidat_providers.dart';
import 'package:faso_resultats_mobile/features/auth_candidat/presentation/auth_candidat_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _FakeAuthCandidatRepository implements AuthCandidatRepository {
  static const codeDebug = '123456';

  bool inscriptionAppelee = false;
  bool connexionAppelee = false;

  @override
  Future<String?> inscrire({
    required String numeroCnib,
    required String nomComplet,
    required DateTime dateNaissance,
    required String telephone,
    required String consentementApdpVersion,
  }) async {
    inscriptionAppelee = true;
    return codeDebug;
  }

  @override
  Future<String?> demanderConnexion(String telephone) async {
    connexionAppelee = true;
    return codeDebug;
  }

  @override
  Future<SessionCandidat> validerOtp(
      {required String telephone, required String code}) async {
    return const SessionCandidat(
        accessToken: 'token-factice', compteCree: true);
  }

  @override
  Future<bool> estConnecte() async => false;

  @override
  Future<void> deconnecter() async {}
}

Widget construireApp(AuthCandidatRepository repository) {
  return ProviderScope(
    overrides: [authCandidatRepositoryProvider.overrideWithValue(repository)],
    child: const MaterialApp(home: AuthCandidatScreen()),
  );
}

void main() {
  testWidgets("l'onglet connexion est actif par défaut", (tester) async {
    await tester.pumpWidget(construireApp(_FakeAuthCandidatRepository()));

    expect(find.text('Numéro de téléphone'), findsOneWidget);
    expect(find.text('Numéro CNIB'), findsNothing);
  });

  testWidgets(
      "basculer vers l'onglet inscription affiche le formulaire complet", (
    tester,
  ) async {
    await tester.pumpWidget(construireApp(_FakeAuthCandidatRepository()));

    await tester.tap(find.text('Inscription'));
    await tester.pumpAndSettle();

    expect(find.text('Numéro CNIB'), findsOneWidget);
    expect(find.text('Nom complet'), findsOneWidget);
  });

  testWidgets(
      "connexion : soumettre un téléphone valide navigue vers l'écran OTP", (
    tester,
  ) async {
    final repository = _FakeAuthCandidatRepository();
    await tester.pumpWidget(construireApp(repository));

    await tester.enterText(find.byType(TextFormField), '+22670000001');
    await tester.tap(find.text('Recevoir un code'));
    await tester.pumpAndSettle();

    expect(repository.connexionAppelee, isTrue);
    expect(find.text('Vérification'), findsOneWidget);
    expect(find.textContaining('+22670000001'), findsOneWidget);
  });

  testWidgets('connexion : téléphone invalide ne déclenche pas la requête',
      (tester) async {
    final repository = _FakeAuthCandidatRepository();
    await tester.pumpWidget(construireApp(repository));

    await tester.enterText(find.byType(TextFormField), '123');
    await tester.tap(find.text('Recevoir un code'));
    await tester.pumpAndSettle();

    expect(repository.connexionAppelee, isFalse);
    expect(find.text('Vérification'), findsNothing);
  });

  testWidgets(
      'inscription sans consentement affiche un message et ne soumet pas', (
    tester,
  ) async {
    final repository = _FakeAuthCandidatRepository();
    await tester.pumpWidget(construireApp(repository));
    await tester.tap(find.text('Inscription'));
    await tester.pumpAndSettle();

    await tester.enterText(
        find.widgetWithText(TextFormField, 'Numéro CNIB'), 'B14863543');
    await tester.enterText(
        find.widgetWithText(TextFormField, 'Nom complet'), 'TRAORE Awa');
    await tester.enterText(
      find.widgetWithText(TextFormField, 'Numéro de téléphone'),
      '+22670000001',
    );
    await tester.tap(find.text('Créer mon espace'));
    await tester.pumpAndSettle();

    expect(repository.inscriptionAppelee, isFalse);
    expect(find.text('Le consentement est nécessaire pour créer votre espace.'),
        findsOneWidget);
  });
}
