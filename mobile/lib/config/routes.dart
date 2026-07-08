import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/storage/secure_storage.dart';
import '../features/accueil/presentation/accueil_screen.dart';
import '../features/accueil/presentation/splash_screen.dart';
import '../features/auth_candidat/presentation/auth_candidat_screen.dart';
import '../features/candidatures/presentation/dashboard_screen.dart';
import '../features/consultation_rapide/presentation/consultation_rapide_screen.dart';
import '../features/profil_candidat/presentation/profil_screen.dart';
import '../features/profil_candidat/presentation/securite_droits_screen.dart';

/// go_router plutôt qu'auto_route (choix structurant) : déclaratif, sans
/// génération de code obligatoire pour les cas simples de ce projet (peu
/// d'écrans imbriqués), documentation officielle Flutter la recommande en
/// premier. auto_route apporte surtout des routes typées via génération —
/// utile sur de très grosses apps, pas indispensable ici (pas de sur-
/// abstraction, CLAUDE.md).
class AppRoutes {
  const AppRoutes._();

  static const splash = '/';
  static const accueil = '/accueil';
  static const consultationRapide = '/consultation-rapide';
  static const authCandidat = '/auth';
  static const dashboard = '/dashboard';
  static const profil = '/profil';
  static const securiteDroits = '/profil/securite';
}

final routerProvider = Provider<GoRouter>((ref) {
  final secureStorage = ref.watch(secureStorageProvider);

  return GoRouter(
    initialLocation: AppRoutes.splash,
    routes: [
      GoRoute(
        path: AppRoutes.splash,
        builder: (context, state) => SplashScreen(secureStorage: secureStorage),
      ),
      GoRoute(
        path: AppRoutes.accueil,
        builder: (context, state) => const AccueilScreen(),
      ),
      GoRoute(
        path: AppRoutes.consultationRapide,
        builder: (context, state) => const ConsultationRapideScreen(),
      ),
      GoRoute(
        path: AppRoutes.authCandidat,
        builder: (context, state) => const AuthCandidatScreen(),
      ),
      GoRoute(
        path: AppRoutes.dashboard,
        builder: (context, state) => const DashboardScreen(),
      ),
      GoRoute(
        path: AppRoutes.profil,
        builder: (context, state) => const ProfilScreen(),
      ),
      GoRoute(
        path: AppRoutes.securiteDroits,
        builder: (context, state) => const SecuriteDroitsScreen(),
      ),
    ],
  );
});
