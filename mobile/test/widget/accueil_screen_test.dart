import 'package:faso_resultats_mobile/config/constants.dart';
import 'package:faso_resultats_mobile/config/routes.dart';
import 'package:faso_resultats_mobile/core/storage/prefs_storage.dart';
import 'package:faso_resultats_mobile/features/accueil/presentation/accueil_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';

Future<Widget> construireApp({bool consentementDejaAccepte = true}) async {
  SharedPreferences.setMockInitialValues(consentementDejaAccepte
      ? {'faso_consentement_version': AppInfo.versionConsentementApp}
      : {});
  final prefs = await SharedPreferences.getInstance();

  final router = GoRouter(
    initialLocation: AppRoutes.accueil,
    routes: [
      GoRoute(
        path: AppRoutes.accueil,
        builder: (context, state) => const AccueilScreen(),
      ),
      GoRoute(
        path: AppRoutes.consultationRapide,
        builder: (context, state) => const Scaffold(body: Text('Consultation')),
      ),
      GoRoute(
        path: AppRoutes.authCandidat,
        builder: (context, state) => const Scaffold(body: Text('Auth')),
      ),
      GoRoute(
        path: AppRoutes.consultationSms,
        builder: (context, state) =>
            const Scaffold(body: Text('ConsultationSms')),
      ),
      GoRoute(
        path: AppRoutes.politiqueConfidentialite,
        builder: (context, state) => const Scaffold(body: Text('Politique')),
      ),
    ],
  );
  return ProviderScope(
    overrides: [sharedPreferencesProvider.overrideWithValue(prefs)],
    child: MaterialApp.router(routerConfig: router),
  );
}

void main() {
  testWidgets('affiche les deux CTA attendus', (tester) async {
    await tester.pumpWidget(await construireApp());
    await tester.pumpAndSettle();

    expect(find.text('Consulter mon résultat'), findsOneWidget);
    expect(find.text('Créer ou accéder à mon espace candidat'), findsOneWidget);
  });

  testWidgets('le CTA consultation navigue vers /consultation-rapide',
      (tester) async {
    await tester.pumpWidget(await construireApp());
    await tester.pumpAndSettle();

    await tester.tap(find.text('Consulter mon résultat'));
    await tester.pumpAndSettle();

    expect(find.text('Consultation'), findsOneWidget);
  });

  testWidgets('le CTA espace candidat navigue vers /auth', (tester) async {
    await tester.pumpWidget(await construireApp());
    await tester.pumpAndSettle();

    await tester.tap(find.text('Créer ou accéder à mon espace candidat'));
    await tester.pumpAndSettle();

    expect(find.text('Auth'), findsOneWidget);
  });

  testWidgets('le CTA SMS navigue vers /consultation-sms', (tester) async {
    await tester.pumpWidget(await construireApp());
    await tester.pumpAndSettle();

    await tester.tap(find.text('Pas de connexion ? Consulter par SMS'));
    await tester.pumpAndSettle();

    expect(find.text('ConsultationSms'), findsOneWidget);
  });

  testWidgets('premier lancement affiche le bandeau de consentement',
      (tester) async {
    await tester
        .pumpWidget(await construireApp(consentementDejaAccepte: false));
    await tester.pumpAndSettle();

    expect(find.text('Avant de continuer'), findsOneWidget);
  });

  testWidgets("J'ai compris enregistre le consentement et ferme le bandeau",
      (tester) async {
    await tester
        .pumpWidget(await construireApp(consentementDejaAccepte: false));
    await tester.pumpAndSettle();

    await tester.tap(find.text("J'ai compris"));
    await tester.pumpAndSettle();

    expect(find.text('Avant de continuer'), findsNothing);
  });

  testWidgets('consentement déjà accepté ne réaffiche pas le bandeau',
      (tester) async {
    await tester.pumpWidget(await construireApp());
    await tester.pumpAndSettle();

    expect(find.text('Avant de continuer'), findsNothing);
  });
}
