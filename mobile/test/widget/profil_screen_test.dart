import 'package:faso_resultats_mobile/features/auth_candidat/domain/auth_candidat_repository.dart';
import 'package:faso_resultats_mobile/features/auth_candidat/domain/session_candidat.dart';
import 'package:faso_resultats_mobile/features/auth_candidat/presentation/auth_candidat_providers.dart';
import 'package:faso_resultats_mobile/features/profil_candidat/domain/profil_candidat.dart';
import 'package:faso_resultats_mobile/features/profil_candidat/domain/profil_candidat_export.dart';
import 'package:faso_resultats_mobile/features/profil_candidat/domain/profil_candidat_repository.dart';
import 'package:faso_resultats_mobile/features/profil_candidat/presentation/profil_candidat_providers.dart';
import 'package:faso_resultats_mobile/features/profil_candidat/presentation/profil_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

const _profilInitial = ProfilCandidat(
  id: 'p-1',
  nomComplet: 'TRAORE Awa',
  telephoneVerifie: true,
  emailVerifie: false,
  notificationsSms: true,
  notificationsPush: false,
  notificationsEmail: false,
  statut: 'ACTIF',
);

class _FakeProfilCandidatRepository implements ProfilCandidatRepository {
  ProfilCandidat profil = _profilInitial;
  bool suppressionAppelee = false;

  @override
  Future<ProfilCandidat> obtenir() async => profil;

  @override
  Future<ProfilCandidat> mettreAJour({
    String? email,
    bool? notificationsSms,
    bool? notificationsPush,
    bool? notificationsEmail,
  }) async {
    return profil = ProfilCandidat(
      id: profil.id,
      nomComplet: profil.nomComplet,
      telephoneVerifie: profil.telephoneVerifie,
      email: email ?? profil.email,
      emailVerifie: profil.emailVerifie,
      notificationsSms: notificationsSms ?? profil.notificationsSms,
      notificationsPush: notificationsPush ?? profil.notificationsPush,
      notificationsEmail: notificationsEmail ?? profil.notificationsEmail,
      statut: profil.statut,
    );
  }

  @override
  Future<ProfilCandidatExport> exporter() async {
    return ProfilCandidatExport(
      numeroCnib: 'B14863543',
      nomComplet: profil.nomComplet,
      dateNaissance: '2000-01-01',
      telephone: '+22670000001',
      consentementApdpDate: DateTime(2026),
      consentementApdpVersion: 'v1',
      createdAt: DateTime(2026),
      candidatures: const [],
      journal: const [],
    );
  }

  @override
  Future<void> supprimerCompte() async {
    suppressionAppelee = true;
  }
}

class _FakeAuthCandidatRepository implements AuthCandidatRepository {
  bool deconnexionAppelee = false;

  @override
  Future<void> deconnecter() async {
    deconnexionAppelee = true;
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
  Future<SessionCandidat> validerOtp(
      {required String telephone, required String code}) async {
    return const SessionCandidat(accessToken: 'x', compteCree: false);
  }

  @override
  Future<bool> estConnecte() async => true;
}

Widget construireApp(
  ProfilCandidatRepository profilRepository,
  AuthCandidatRepository authRepository,
) {
  return ProviderScope(
    overrides: [
      profilCandidatRepositoryProvider.overrideWithValue(profilRepository),
      authCandidatRepositoryProvider.overrideWithValue(authRepository),
    ],
    child: MaterialApp.router(
      routerConfig: GoRouter(
        initialLocation: '/profil',
        routes: [
          GoRoute(
              path: '/profil',
              builder: (context, state) => const ProfilScreen()),
          GoRoute(
            path: '/accueil',
            builder: (context, state) => const Scaffold(body: Text('Accueil')),
          ),
          GoRoute(
            path: '/profil/securite',
            builder: (context, state) => const Scaffold(body: Text('Securite')),
          ),
        ],
      ),
    ),
  );
}

void main() {
  testWidgets('affiche le nom du profil et les préférences', (tester) async {
    await tester.pumpWidget(construireApp(
        _FakeProfilCandidatRepository(), _FakeAuthCandidatRepository()));
    await tester.pumpAndSettle();

    expect(find.text('TRAORE Awa'), findsOneWidget);
    expect(find.text('Notifications par SMS'), findsOneWidget);
  });

  testWidgets('basculer une préférence appelle mettreAJour', (tester) async {
    final repository = _FakeProfilCandidatRepository();
    await tester
        .pumpWidget(construireApp(repository, _FakeAuthCandidatRepository()));
    await tester.pumpAndSettle();

    await tester.tap(find.byType(SwitchListTile).first);
    await tester.pumpAndSettle();

    expect(repository.profil.notificationsSms, isFalse);
  });

  testWidgets(
      "se déconnecter appelle le repository auth et redirige vers l'accueil", (
    tester,
  ) async {
    final authRepository = _FakeAuthCandidatRepository();
    await tester.pumpWidget(
        construireApp(_FakeProfilCandidatRepository(), authRepository));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Se déconnecter'));
    await tester.pumpAndSettle();

    expect(authRepository.deconnexionAppelee, isTrue);
    expect(find.text('Accueil'), findsOneWidget);
  });
}
