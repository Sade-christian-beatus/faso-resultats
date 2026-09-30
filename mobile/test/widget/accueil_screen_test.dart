import 'package:faso_resultats_mobile/config/constants.dart';
import 'package:faso_resultats_mobile/config/routes.dart';
import 'package:faso_resultats_mobile/core/storage/prefs_storage.dart';
import 'package:faso_resultats_mobile/core/storage/secure_storage.dart';
import 'package:faso_resultats_mobile/features/accueil/presentation/accueil_screen.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/administration.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/consultation_repository.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/examen.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/resultat.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/presentation/consultation_providers.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';

class _FakeConsultationRepository implements ConsultationRepository {
  _FakeConsultationRepository({this.examens = _examens});

  final List<Examen> examens;

  @override
  Future<List<Administration>> listerAdministrations() async => const [
        Administration(
            id: 'admin-1',
            code: 'ocecos',
            nomOfficiel: 'OCECOS',
            sigle: 'OCECOS'),
      ];

  @override
  Future<List<Examen>> listerExamens() async => examens;

  @override
  Future<List<Resultat>> rechercherResultats({
    required String examenId,
    required String numeroPv,
    String? jury,
  }) async =>
      const [];
}

const _examens = [
  Examen(
      id: 'bac',
      administrationId: 'admin-1',
      typeExamen: 'BAC',
      annee: 2026,
      libelle: 'Baccalauréat session normale'),
  Examen(
      id: 'bepc',
      administrationId: 'admin-1',
      typeExamen: 'BEPC',
      annee: 2026,
      libelle: 'BEPC session 2026'),
  Examen(
      id: 'police',
      administrationId: 'admin-1',
      typeExamen: 'POLICE',
      annee: 2026,
      libelle: 'Élèves assistants de police'),
  Examen(
      id: 'cap',
      administrationId: 'admin-1',
      typeExamen: 'CAP',
      annee: 2025,
      libelle: 'CAP session 2025'),
  Examen(
      id: 'cep',
      administrationId: 'admin-1',
      typeExamen: 'CEP',
      annee: 2025,
      libelle: 'CEP session 2025'),
];

/// Every route the home screen can open is a stub printing its location, so
/// a test only has to look for that text.
Widget _page(GoRouterState state) => Scaffold(body: Text('Page ${state.uri}'));

Future<Widget> construireApp({
  bool consentementDejaAccepte = true,
  String? token,
  ConsultationRepository? repository,
}) async {
  SharedPreferences.setMockInitialValues(consentementDejaAccepte
      ? {'faso_consentement_version': AppInfo.versionConsentementApp}
      : {});
  FlutterSecureStorage.setMockInitialValues(
      token == null ? {} : {'faso_candidat_token': token});
  final prefs = await SharedPreferences.getInstance();

  final router = GoRouter(
    initialLocation: AppRoutes.accueil,
    routes: [
      GoRoute(
        path: AppRoutes.accueil,
        builder: (context, state) => const AccueilScreen(),
      ),
      for (final chemin in [
        AppRoutes.consultationRapide,
        AppRoutes.consultationSms,
        AppRoutes.authCandidat,
        AppRoutes.dashboard,
        AppRoutes.notifications,
        AppRoutes.profil,
        AppRoutes.aide,
        AppRoutes.politiqueConfidentialite,
      ])
        GoRoute(path: chemin, builder: (context, state) => _page(state)),
    ],
  );
  return ProviderScope(
    overrides: [
      sharedPreferencesProvider.overrideWithValue(prefs),
      secureStorageProvider
          .overrideWithValue(SecureStorage(const FlutterSecureStorage())),
      consultationRepositoryProvider
          .overrideWithValue(repository ?? _FakeConsultationRepository()),
    ],
    child: MaterialApp.router(routerConfig: router),
  );
}

/// Tall phone-sized screen so the whole home page is built at once.
void _grandEcran(WidgetTester tester) {
  tester.view
    ..physicalSize = const Size(1080, 5400)
    ..devicePixelRatio = 3;
  addTearDown(tester.view.reset);
}

Future<void> _ouvrir(WidgetTester tester, Widget app) async {
  _grandEcran(tester);
  await tester.pumpWidget(app);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('affiche les sections de la maquette', (tester) async {
    await _ouvrir(tester, await construireApp());

    expect(find.text('Consultez vos résultats'), findsOneWidget);
    expect(find.text('Rechercher un résultat'), findsOneWidget);
    for (final raccourci in [
      'Examens',
      'Concours',
      'Fonction publique',
      'Recherche par numéro',
      'Mes résultats',
      'Questions fréquentes',
      'Assistance',
    ]) {
      expect(find.text(raccourci), findsOneWidget, reason: raccourci);
    }
    expect(find.text('Suivez vos concours'), findsOneWidget);
    expect(find.text('Résultats récents'), findsOneWidget);
    // "Universités" (out of scope) is deliberately absent.
    expect(find.text('Universités'), findsNothing);
  });

  testWidgets('résultats récents : les 4 derniers examens publiés',
      (tester) async {
    await _ouvrir(tester, await construireApp());

    expect(find.text('BAC 2026'), findsOneWidget);
    expect(find.text('Police 2026'), findsOneWidget);
    expect(find.text('CAP 2025'), findsOneWidget);
    expect(find.text('CEP 2025'), findsNothing);
    expect(find.text('Disponible'), findsNWidgets(4));
    expect(find.text('Baccalauréat session normale · OCECOS'), findsOneWidget);
  });

  testWidgets('aucun examen publié : message explicite', (tester) async {
    await _ouvrir(
        tester,
        await construireApp(
            repository: _FakeConsultationRepository(examens: [])));

    expect(find.text('Aucun résultat publié pour le moment.'), findsOneWidget);
  });

  testWidgets('un résultat récent ouvre la recherche avec cet examen',
      (tester) async {
    await _ouvrir(tester, await construireApp());

    await tester.tap(find.text('BEPC 2026'));
    await tester.pumpAndSettle();

    expect(find.text('Page /consultation-rapide?examen=bepc'), findsOneWidget);
  });

  testWidgets('le CTA du carrousel ouvre la recherche', (tester) async {
    await _ouvrir(tester, await construireApp());

    await tester.tap(find.text('Rechercher un résultat'));
    await tester.pumpAndSettle();

    expect(find.text('Page /consultation-rapide'), findsOneWidget);
  });

  testWidgets('une catégorie ouvre la recherche filtrée', (tester) async {
    await _ouvrir(tester, await construireApp());

    await tester.tap(find.text('Fonction publique'));
    await tester.pumpAndSettle();

    expect(find.text('Page /consultation-rapide?categorie=FONCTION_PUBLIQUE'),
        findsOneWidget);
  });

  testWidgets('Mes résultats sans compte ouvre la connexion', (tester) async {
    await _ouvrir(tester, await construireApp());

    await tester.tap(find.text('Mes résultats'));
    await tester.pumpAndSettle();

    expect(find.text('Page /auth'), findsOneWidget);
  });

  testWidgets('Mes résultats avec un compte ouvre le dashboard',
      (tester) async {
    await _ouvrir(tester, await construireApp(token: 'jwt'));

    await tester.tap(find.text('Mes résultats'));
    await tester.pumpAndSettle();

    expect(find.text('Page /dashboard'), findsOneWidget);
  });

  testWidgets('Créer mon espace ouvre la connexion / inscription',
      (tester) async {
    await _ouvrir(tester, await construireApp());

    await tester.tap(find.text('Créer mon espace').last);
    await tester.pumpAndSettle();

    expect(find.text('Page /auth'), findsOneWidget);
  });

  testWidgets('le carrousel mène aussi à la consultation par SMS',
      (tester) async {
    await _ouvrir(tester, await construireApp());

    await tester.drag(find.byType(PageView), const Offset(-400, 0));
    await tester.pumpAndSettle();
    await tester.drag(find.byType(PageView), const Offset(-400, 0));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Consulter par SMS'));
    await tester.pumpAndSettle();

    expect(find.text('Page /consultation-sms'), findsOneWidget);
  });

  testWidgets('Questions fréquentes ouvre l’aide', (tester) async {
    await _ouvrir(tester, await construireApp());

    await tester.tap(find.text('Questions fréquentes'));
    await tester.pumpAndSettle();

    expect(find.text('Page /aide'), findsOneWidget);
  });

  testWidgets('Assistance affiche les numéros de contact', (tester) async {
    await _ouvrir(tester, await construireApp());

    await tester.tap(find.text('Assistance'));
    await tester.pumpAndSettle();

    expect(find.text('56 12 18 18'), findsOneWidget);
    expect(find.text('62 29 18 18'), findsOneWidget);
  });

  testWidgets('premier lancement affiche le bandeau de consentement',
      (tester) async {
    await _ouvrir(tester, await construireApp(consentementDejaAccepte: false));

    expect(find.text('Avant de continuer'), findsOneWidget);
  });

  testWidgets("J'ai compris enregistre le consentement et ferme le bandeau",
      (tester) async {
    await _ouvrir(tester, await construireApp(consentementDejaAccepte: false));

    await tester.tap(find.text("J'ai compris"));
    await tester.pumpAndSettle();

    expect(find.text('Avant de continuer'), findsNothing);
  });

  testWidgets('consentement déjà accepté ne réaffiche pas le bandeau',
      (tester) async {
    await _ouvrir(tester, await construireApp());

    expect(find.text('Avant de continuer'), findsNothing);
  });
}
