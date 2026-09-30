import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../config/routes.dart';
import '../../../config/theme.dart';
import '../../../core/storage/secure_storage.dart';

/// Bottom navigation shared by the five main tabs (mobile blueprint):
/// Accueil, Rechercher, Mes résultats, Notifications, Mon compte.
class NavigationPrincipale extends ConsumerWidget {
  const NavigationPrincipale({
    required this.cheminCourant,
    required this.child,
    super.key,
  });

  final String cheminCourant;
  final Widget child;

  static const _onglets = [
    (
      chemin: AppRoutes.accueil,
      libelle: 'Accueil',
      icone: Icons.home_outlined,
      iconeActive: Icons.home,
      compteRequis: false,
    ),
    (
      chemin: AppRoutes.consultationRapide,
      libelle: 'Rechercher',
      icone: Icons.search,
      iconeActive: Icons.search,
      compteRequis: false,
    ),
    (
      chemin: AppRoutes.dashboard,
      libelle: 'Mes résultats',
      icone: Icons.description_outlined,
      iconeActive: Icons.description,
      compteRequis: true,
    ),
    (
      chemin: AppRoutes.notifications,
      libelle: 'Notifications',
      icone: Icons.notifications_none,
      iconeActive: Icons.notifications,
      compteRequis: false,
    ),
    (
      chemin: AppRoutes.profil,
      libelle: 'Mon compte',
      icone: Icons.person_outline,
      iconeActive: Icons.person,
      compteRequis: true,
    ),
  ];

  /// Index of the tab owning [chemin]. Most specific paths first:
  /// `/profil/notifications` belongs to "Notifications", not "Mon compte".
  static int indexPour(String chemin) {
    if (chemin.startsWith(AppRoutes.consultationRapide)) return 1;
    if (chemin.startsWith(AppRoutes.dashboard)) return 2;
    if (chemin.startsWith(AppRoutes.notifications)) return 3;
    if (chemin.startsWith(AppRoutes.profil)) return 4;
    return 0;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: indexPour(cheminCourant),
        backgroundColor: Colors.white,
        indicatorColor: AppColors.vertFaso.withValues(alpha: 0.15),
        labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
        onDestinationSelected: (index) {
          final onglet = _onglets[index];
          if (onglet.compteRequis) {
            ouvrirEspaceCandidat(context, ref, onglet.chemin);
          } else {
            context.go(onglet.chemin);
          }
        },
        destinations: [
          for (final onglet in _onglets)
            NavigationDestination(
              icon: Icon(onglet.icone),
              selectedIcon:
                  Icon(onglet.iconeActive, color: AppColors.vertFonce),
              label: onglet.libelle,
            ),
        ],
      ),
    );
  }
}

/// Opens a screen that needs a candidate account, or the sign-in screen
/// when no token is stored (the token itself is checked by the API).
Future<void> ouvrirEspaceCandidat(
  BuildContext context,
  WidgetRef ref,
  String destination,
) async {
  final token = await ref.read(secureStorageProvider).lireToken();
  if (!context.mounted) return;
  context.go(token != null ? destination : AppRoutes.authCandidat);
}
