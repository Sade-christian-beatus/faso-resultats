import 'package:faso_resultats_mobile/config/routes.dart';
import 'package:faso_resultats_mobile/features/accueil/presentation/accueil_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

void main() {
  Widget construireApp() {
    final router = GoRouter(
      initialLocation: AppRoutes.accueil,
      routes: [
        GoRoute(
          path: AppRoutes.accueil,
          builder: (context, state) => const AccueilScreen(),
        ),
        GoRoute(
          path: AppRoutes.consultationRapide,
          builder: (context, state) =>
              const Scaffold(body: Text('Consultation')),
        ),
        GoRoute(
          path: AppRoutes.authCandidat,
          builder: (context, state) => const Scaffold(body: Text('Auth')),
        ),
      ],
    );
    return MaterialApp.router(routerConfig: router);
  }

  testWidgets('affiche les deux CTA attendus', (tester) async {
    await tester.pumpWidget(construireApp());

    expect(find.text('Consulter mon résultat'), findsOneWidget);
    expect(find.text('Créer ou accéder à mon espace candidat'), findsOneWidget);
  });

  testWidgets('le CTA consultation navigue vers /consultation-rapide',
      (tester) async {
    await tester.pumpWidget(construireApp());

    await tester.tap(find.text('Consulter mon résultat'));
    await tester.pumpAndSettle();

    expect(find.text('Consultation'), findsOneWidget);
  });

  testWidgets('le CTA espace candidat navigue vers /auth', (tester) async {
    await tester.pumpWidget(construireApp());

    await tester.tap(find.text('Créer ou accéder à mon espace candidat'));
    await tester.pumpAndSettle();

    expect(find.text('Auth'), findsOneWidget);
  });
}
