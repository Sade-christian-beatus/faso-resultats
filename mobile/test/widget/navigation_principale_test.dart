import 'package:faso_resultats_mobile/config/routes.dart';
import 'package:faso_resultats_mobile/core/storage/secure_storage.dart';
import 'package:faso_resultats_mobile/features/accueil/presentation/navigation_principale.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

Widget construireApp({String? token, String initial = AppRoutes.accueil}) {
  FlutterSecureStorage.setMockInitialValues(
      token == null ? {} : {'faso_candidat_token': token});
  final router = GoRouter(
    initialLocation: initial,
    routes: [
      ShellRoute(
        builder: (context, state, child) =>
            NavigationPrincipale(cheminCourant: state.uri.path, child: child),
        routes: [
          for (final chemin in [
            AppRoutes.accueil,
            AppRoutes.consultationRapide,
            AppRoutes.dashboard,
            AppRoutes.notifications,
            AppRoutes.profil,
          ])
            GoRoute(
              path: chemin,
              builder: (context, state) => Text('Page $chemin'),
            ),
        ],
      ),
      GoRoute(
        path: AppRoutes.authCandidat,
        builder: (context, state) => const Text('Page /auth'),
      ),
    ],
  );
  return ProviderScope(
    overrides: [
      secureStorageProvider
          .overrideWithValue(SecureStorage(const FlutterSecureStorage())),
    ],
    child: MaterialApp.router(routerConfig: router),
  );
}

void main() {
  testWidgets('affiche les 5 onglets de la maquette', (tester) async {
    await tester.pumpWidget(construireApp());
    await tester.pumpAndSettle();

    for (final libelle in [
      'Accueil',
      'Rechercher',
      'Mes résultats',
      'Notifications',
      'Mon compte',
    ]) {
      expect(find.text(libelle), findsOneWidget, reason: libelle);
    }
    final barre = tester.widget<NavigationBar>(find.byType(NavigationBar));
    expect(barre.selectedIndex, 0);
  });

  testWidgets('Rechercher ouvre la recherche et devient actif', (tester) async {
    await tester.pumpWidget(construireApp());
    await tester.pumpAndSettle();

    await tester.tap(find.text('Rechercher'));
    await tester.pumpAndSettle();

    expect(find.text('Page ${AppRoutes.consultationRapide}'), findsOneWidget);
    final barre = tester.widget<NavigationBar>(find.byType(NavigationBar));
    expect(barre.selectedIndex, 1);
  });

  testWidgets('Mon compte sans session ouvre la connexion', (tester) async {
    await tester.pumpWidget(construireApp());
    await tester.pumpAndSettle();

    await tester.tap(find.text('Mon compte'));
    await tester.pumpAndSettle();

    expect(find.text('Page /auth'), findsOneWidget);
  });

  testWidgets('Mon compte avec session ouvre le profil', (tester) async {
    await tester.pumpWidget(construireApp(token: 'jwt'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Mon compte'));
    await tester.pumpAndSettle();

    expect(find.text('Page ${AppRoutes.profil}'), findsOneWidget);
  });

  testWidgets('Notifications reste accessible sans compte', (tester) async {
    await tester.pumpWidget(construireApp());
    await tester.pumpAndSettle();

    await tester.tap(find.text('Notifications'));
    await tester.pumpAndSettle();

    expect(find.text('Page ${AppRoutes.notifications}'), findsOneWidget);
    final barre = tester.widget<NavigationBar>(find.byType(NavigationBar));
    expect(barre.selectedIndex, 3);
  });
}
