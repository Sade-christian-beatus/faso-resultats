import 'package:faso_resultats_mobile/features/auth_candidat/domain/auth_candidat_repository.dart';
import 'package:faso_resultats_mobile/features/auth_candidat/domain/session_candidat.dart';
import 'package:faso_resultats_mobile/features/auth_candidat/presentation/auth_candidat_providers.dart';
import 'package:faso_resultats_mobile/features/auth_candidat/presentation/otp_verify_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _FakeAuthCandidatRepository implements AuthCandidatRepository {
  _FakeAuthCandidatRepository({this.echec = false});

  final bool echec;

  @override
  Future<SessionCandidat> validerOtp(
      {required String telephone, required String code}) async {
    if (echec) {
      throw StateError('code invalide');
    }
    return const SessionCandidat(
        accessToken: 'token-factice', compteCree: false);
  }

  @override
  Future<String?> inscrire({
    required String numeroCnib,
    required String nomComplet,
    required DateTime dateNaissance,
    required String telephone,
    required String consentementApdpVersion,
  }) async =>
      null;

  @override
  Future<String?> demanderConnexion(String telephone) async => null;

  @override
  Future<bool> estConnecte() async => false;

  @override
  Future<void> deconnecter() async {}
}

Widget construireApp(AuthCandidatRepository repository,
    {String telephone = '+22670000001'}) {
  return ProviderScope(
    overrides: [authCandidatRepositoryProvider.overrideWithValue(repository)],
    child: MaterialApp(
      home: OtpVerifyScreen(telephone: telephone, codeDebug: '123456'),
      routes: {'/dashboard': (_) => const Scaffold(body: Text('Dashboard'))},
    ),
  );
}

void main() {
  testWidgets('préremplit le code de debug quand fourni', (tester) async {
    await tester.pumpWidget(construireApp(_FakeAuthCandidatRepository()));

    final champ = tester.widget<TextFormField>(find.byType(TextFormField));
    expect(champ.controller!.text, '123456');
  });

  testWidgets('un code invalide (format) empêche la soumission',
      (tester) async {
    final repository = _FakeAuthCandidatRepository();
    await tester.pumpWidget(construireApp(repository));

    await tester.enterText(find.byType(TextFormField), '123');
    await tester.tap(find.text('Valider'));
    await tester.pumpAndSettle();

    expect(find.text('Le code doit contenir 6 chiffres'), findsOneWidget);
  });

  testWidgets("un échec de validation affiche un message d'erreur",
      (tester) async {
    final repository = _FakeAuthCandidatRepository(echec: true);
    await tester.pumpWidget(construireApp(repository));

    await tester.tap(find.text('Valider'));
    await tester.pumpAndSettle();

    expect(find.textContaining('Code invalide ou expiré'), findsOneWidget);
  });
}
