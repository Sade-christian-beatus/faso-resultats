import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/storage/secure_storage.dart';
import '../features/accueil/presentation/accueil_screen.dart';
import '../features/accueil/presentation/navigation_principale.dart';
import '../features/accueil/presentation/splash_screen.dart';
import '../features/aide/presentation/aide_screen.dart';
import '../features/auth_candidat/presentation/auth_candidat_screen.dart';
import '../features/candidatures/presentation/ajout_candidature_screen.dart';
import '../features/candidatures/presentation/dashboard_screen.dart';
import '../features/consultation_rapide/domain/categorie_examen.dart';
import '../features/consultation_rapide/presentation/consultation_rapide_screen.dart';
import '../features/consultation_sms/presentation/consultation_sms_screen.dart';
import '../features/notifications/presentation/notifications_screen.dart';
import '../features/parametres/presentation/a_propos_screen.dart';
import '../features/parametres/presentation/conditions_utilisation_screen.dart';
import '../features/parametres/presentation/parametres_screen.dart';
import '../features/parametres/presentation/politique_confidentialite_screen.dart';
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
  static const consultationSms = '/consultation-sms';
  static const authCandidat = '/auth';
  static const dashboard = '/dashboard';
  static const ajoutCandidature = '/dashboard/ajouter';
  static const profil = '/profil';
  static const securiteDroits = '/profil/securite';
  static const notifications = '/profil/notifications';
  static const parametres = '/profil/parametres';
  static const politiqueConfidentialite = '/profil/parametres/confidentialite';
  static const conditionsUtilisation = '/profil/parametres/conditions';
  static const aPropos = '/profil/parametres/a-propos';
  static const aide = '/aide';

  /// Search screen narrowed to a home page category and/or with an exam
  /// preselected ("Résultats récents").
  static String consultationFiltree({
    CategorieExamen? categorie,
    String? examenId,
  }) {
    final parametres = {
      if (categorie != null) 'categorie': categorie.code,
      if (examenId != null) 'examen': examenId,
    };
    return parametres.isEmpty
        ? consultationRapide
        : Uri(path: consultationRapide, queryParameters: parametres).toString();
  }
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
      // The five bottom navigation tabs (mobile blueprint of 2026-09-30).
      // Other screens stay outside the shell: they open full screen with a
      // back button.
      ShellRoute(
        builder: (context, state, child) => NavigationPrincipale(
          cheminCourant: state.uri.path,
          child: child,
        ),
        routes: [
          GoRoute(
            path: AppRoutes.accueil,
            builder: (context, state) => const AccueilScreen(),
          ),
          GoRoute(
            path: AppRoutes.consultationRapide,
            builder: (context, state) => ConsultationRapideScreen(
              // Keyed on the query so a new shortcut resets the form.
              key: ValueKey(state.uri.query),
              categorie: CategorieExamen.parCode(
                  state.uri.queryParameters['categorie']),
              examenId: state.uri.queryParameters['examen'],
            ),
          ),
          GoRoute(
            path: AppRoutes.dashboard,
            builder: (context, state) => const DashboardScreen(),
          ),
          GoRoute(
            path: AppRoutes.notifications,
            builder: (context, state) => const NotificationsScreen(),
          ),
          GoRoute(
            path: AppRoutes.profil,
            builder: (context, state) => const ProfilScreen(),
          ),
        ],
      ),
      GoRoute(
        path: AppRoutes.aide,
        builder: (context, state) => const AideScreen(),
      ),
      GoRoute(
        path: AppRoutes.consultationSms,
        builder: (context, state) => const ConsultationSmsScreen(),
      ),
      GoRoute(
        path: AppRoutes.authCandidat,
        builder: (context, state) => const AuthCandidatScreen(),
      ),
      GoRoute(
        path: AppRoutes.ajoutCandidature,
        builder: (context, state) => const AjoutCandidatureScreen(),
      ),
      GoRoute(
        path: AppRoutes.securiteDroits,
        builder: (context, state) => const SecuriteDroitsScreen(),
      ),
      GoRoute(
        path: AppRoutes.parametres,
        builder: (context, state) => const ParametresScreen(),
      ),
      GoRoute(
        path: AppRoutes.politiqueConfidentialite,
        builder: (context, state) => const PolitiqueConfidentialiteScreen(),
      ),
      GoRoute(
        path: AppRoutes.conditionsUtilisation,
        builder: (context, state) => const ConditionsUtilisationScreen(),
      ),
      GoRoute(
        path: AppRoutes.aPropos,
        builder: (context, state) => const AProposScreen(),
      ),
    ],
  );
});
