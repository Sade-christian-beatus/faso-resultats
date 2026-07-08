import 'package:faso_resultats_mobile/features/candidatures/domain/candidature.dart';
import 'package:faso_resultats_mobile/features/candidatures/domain/candidatures_repository.dart';
import 'package:faso_resultats_mobile/features/candidatures/presentation/candidature_otp_screen.dart';
import 'package:faso_resultats_mobile/features/candidatures/presentation/candidatures_providers.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _FakeCandidaturesRepository implements CandidaturesRepository {
  _FakeCandidaturesRepository({this.echec = false});

  final bool echec;
  bool confirmerOtpAppelee = false;

  @override
  Future<List<Candidature>> lister() async => [];

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
  }) async {
    confirmerOtpAppelee = true;
    if (echec) throw StateError('code invalide');
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

Widget construireApp(CandidaturesRepository repository) {
  return ProviderScope(
    overrides: [candidaturesRepositoryProvider.overrideWithValue(repository)],
    child: MaterialApp(
      home: Builder(
        builder: (context) => Scaffold(
          body: Center(
            child: ElevatedButton(
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (context) => Scaffold(
                    body: Center(
                      child: ElevatedButton(
                        onPressed: () => Navigator.of(context).push(
                          MaterialPageRoute<void>(
                            builder: (_) => const CandidatureOtpScreen(
                              candidatureId: 'c-otp',
                              codeDebug: '123456',
                            ),
                          ),
                        ),
                        child: const Text('Ouvrir OTP'),
                      ),
                    ),
                  ),
                ),
              ),
              child: const Text('Ajout'),
            ),
          ),
        ),
      ),
    ),
  );
}

Future<void> _ouvrirEcranOtp(WidgetTester tester) async {
  await tester.tap(find.text('Ajout'));
  await tester.pumpAndSettle();
  await tester.tap(find.text('Ouvrir OTP'));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('préremplit le code de debug quand fourni', (tester) async {
    await tester.pumpWidget(construireApp(_FakeCandidaturesRepository()));
    await _ouvrirEcranOtp(tester);

    final champ = tester.widget<TextFormField>(find.byType(TextFormField));
    expect(champ.controller!.text, '123456');
  });

  testWidgets(
      'une confirmation réussie appelle le repository et revient au premier '
      'écran', (tester) async {
    final repository = _FakeCandidaturesRepository();
    await tester.pumpWidget(construireApp(repository));
    await _ouvrirEcranOtp(tester);

    await tester.tap(find.text('Confirmer'));
    await tester.pumpAndSettle();

    expect(repository.confirmerOtpAppelee, isTrue);
    expect(find.text('Ajout'), findsOneWidget);
    expect(find.text('Candidature confirmée.'), findsOneWidget);
  });

  testWidgets(
      "un échec de confirmation affiche un message d'erreur et "
      "reste sur l'écran", (tester) async {
    await tester
        .pumpWidget(construireApp(_FakeCandidaturesRepository(echec: true)));
    await _ouvrirEcranOtp(tester);

    await tester.tap(find.text('Confirmer'));
    await tester.pumpAndSettle();

    expect(find.text('Confirmer la candidature'), findsOneWidget);
    expect(find.textContaining('Code invalide ou expiré'), findsOneWidget);
  });

  testWidgets('un code au mauvais format empêche la soumission',
      (tester) async {
    final repository = _FakeCandidaturesRepository();
    await tester.pumpWidget(construireApp(repository));
    await _ouvrirEcranOtp(tester);

    await tester.enterText(find.byType(TextFormField), '123');
    await tester.tap(find.text('Confirmer'));
    await tester.pumpAndSettle();

    expect(repository.confirmerOtpAppelee, isFalse);
    expect(find.text('Le code doit contenir 6 chiffres'), findsOneWidget);
  });
}
