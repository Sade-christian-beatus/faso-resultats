import 'package:faso_resultats_mobile/features/profil_candidat/domain/profil_candidat.dart';
import 'package:faso_resultats_mobile/features/profil_candidat/domain/profil_candidat_export.dart';
import 'package:faso_resultats_mobile/features/profil_candidat/domain/profil_candidat_repository.dart';
import 'package:faso_resultats_mobile/features/profil_candidat/presentation/droits_candidat_provider.dart';
import 'package:faso_resultats_mobile/features/profil_candidat/presentation/profil_candidat_providers.dart';
import 'package:faso_resultats_mobile/features/profil_candidat/presentation/securite_droits_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/date_symbol_data_local.dart';

class _FakeProfilCandidatRepository implements ProfilCandidatRepository {
  _FakeProfilCandidatRepository({List<JournalEntree>? journal})
      : export = ProfilCandidatExport(
          numeroCnib: 'B14863543',
          nomComplet: 'TRAORE Awa',
          dateNaissance: '2000-01-01',
          telephone: '+22670000001',
          consentementApdpDate: DateTime(2026),
          consentementApdpVersion: 'v1',
          createdAt: DateTime(2026),
          candidatures: const [],
          journal: journal ?? const [],
        );

  final ProfilCandidatExport export;
  bool suppressionAppelee = false;

  @override
  Future<ProfilCandidat> obtenir() async => throw UnimplementedError();

  @override
  Future<ProfilCandidat> mettreAJour({
    String? email,
    bool? notificationsSms,
    bool? notificationsPush,
    bool? notificationsEmail,
  }) async =>
      throw UnimplementedError();

  @override
  Future<ProfilCandidatExport> exporter() async => export;

  @override
  Future<void> supprimerCompte() async {
    suppressionAppelee = true;
  }
}

Widget construireApp(
  ProfilCandidatRepository repository, {
  DroitsCandidat droits = const DroitsCandidat(
    contactDpo: 'dpo@faso-resultats.bf',
    droits: ['Accès', 'Rectification', 'Effacement'],
  ),
}) {
  return ProviderScope(
    overrides: [
      profilCandidatRepositoryProvider.overrideWithValue(repository),
      droitsCandidatProvider.overrideWith((ref) async => droits),
    ],
    child: MaterialApp.router(
      routerConfig: GoRouter(
        initialLocation: '/profil/securite',
        routes: [
          GoRoute(
            path: '/profil/securite',
            builder: (context, state) => const SecuriteDroitsScreen(),
          ),
          GoRoute(
            path: '/profil',
            builder: (context, state) => const Scaffold(body: Text('Profil')),
          ),
          GoRoute(
            path: '/accueil',
            builder: (context, state) => const Scaffold(body: Text('Accueil')),
          ),
        ],
      ),
    ),
  );
}

void main() {
  setUpAll(() => initializeDateFormatting('fr_FR'));

  testWidgets('affiche mes droits et le contact DPO', (tester) async {
    await tester.pumpWidget(construireApp(_FakeProfilCandidatRepository()));
    await tester.pumpAndSettle();

    expect(find.text('• Accès'), findsOneWidget);
    expect(find.textContaining('dpo@faso-resultats.bf'), findsOneWidget);
  });

  testWidgets('affiche un message quand le journal est vide', (tester) async {
    await tester.pumpWidget(construireApp(_FakeProfilCandidatRepository()));
    await tester.pumpAndSettle();

    expect(find.text('Aucune activité enregistrée.'), findsOneWidget);
  });

  testWidgets('affiche les entrées du journal avec leur date formatée',
      (tester) async {
    final repository = _FakeProfilCandidatRepository(journal: [
      JournalEntree(action: 'LOGIN', timestamp: DateTime(2026, 3, 7)),
    ]);
    await tester.pumpWidget(construireApp(repository));
    await tester.pumpAndSettle();

    expect(find.text('LOGIN'), findsOneWidget);
    expect(find.text('07/03/2026'), findsOneWidget);
  });

  testWidgets('rectifier mes données navigue vers le profil', (tester) async {
    await tester.pumpWidget(construireApp(_FakeProfilCandidatRepository()));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Rectifier mes données'));
    await tester.pumpAndSettle();

    expect(find.text('Profil'), findsOneWidget);
  });

  testWidgets(
      "exporter mes données ne fait jamais planter l'écran, que le partage "
      "natif réussisse ou échoue dans l'environnement de test", (tester) async {
    await tester.pumpWidget(construireApp(_FakeProfilCandidatRepository()));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Exporter mes données'));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(find.text('Sécurité et mes droits'), findsOneWidget);
  });

  testWidgets(
      'supprimer mon compte, après double confirmation, appelle le '
      "repository et redirige vers l'accueil", (tester) async {
    final repository = _FakeProfilCandidatRepository();
    await tester.pumpWidget(construireApp(repository));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Supprimer mon compte'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Continuer'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Supprimer définitivement'));
    await tester.pumpAndSettle();

    expect(repository.suppressionAppelee, isTrue);
    expect(find.text('Accueil'), findsOneWidget);
  });

  testWidgets('annuler la première confirmation ne supprime rien',
      (tester) async {
    final repository = _FakeProfilCandidatRepository();
    await tester.pumpWidget(construireApp(repository));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Supprimer mon compte'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Annuler'));
    await tester.pumpAndSettle();

    expect(repository.suppressionAppelee, isFalse);
  });
}
