import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/storage/secure_storage.dart';
import '../features/accueil/presentation/accueil_screen.dart';
import '../features/accueil/presentation/splash_screen.dart';
import '../features/auth_candidat/presentation/auth_candidat_screen.dart';
import '../features/consultation_rapide/presentation/consultation_rapide_screen.dart';

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
      // Les routes ci-dessous sont construites jour par jour (§ plan) ; elles
      // existent déjà pour que les CTA de l'accueil aient une destination
      // fonctionnelle dès aujourd'hui plutôt qu'un lien mort.
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
        builder: (context, state) =>
            const _EcranAVenir(titre: 'Tableau de bord'),
      ),
    ],
  );
});

class _EcranAVenir extends StatelessWidget {
  const _EcranAVenir({required this.titre});

  final String titre;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(titre)),
      body: const Center(
          child: Text('Cet écran arrive dans une prochaine étape.')),
    );
  }
}
