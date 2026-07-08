import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../config/routes.dart';
import '../../../config/theme.dart';

/// Écran « Paramètres » (jour 8). Les préférences de notifications restent
/// gérées depuis Profil (switches déjà construits jour 4, connectés à
/// `PATCH /me`) — un raccourci y renvoie plutôt que de dupliquer les mêmes
/// widgets ici sous un autre provider.
class ParametresScreen extends StatelessWidget {
  const ParametresScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Paramètres')),
      body: ListView(
        padding: const EdgeInsets.symmetric(vertical: 8),
        children: [
          ListTile(
            leading: const Icon(Icons.notifications_outlined),
            title: const Text('Préférences de notifications'),
            subtitle: const Text('SMS, push, email — depuis votre profil'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.push(AppRoutes.profil),
          ),
          const ListTile(
            leading: Icon(Icons.language_outlined),
            title: Text('Langue'),
            trailing: Text(
              'Français',
              style: TextStyle(color: AppColors.texteAttenue),
            ),
          ),
          const Divider(height: 1),
          ListTile(
            leading: const Icon(Icons.privacy_tip_outlined),
            title: const Text('Politique de confidentialité'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.push(AppRoutes.politiqueConfidentialite),
          ),
          ListTile(
            leading: const Icon(Icons.description_outlined),
            title: const Text("Conditions d'utilisation"),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.push(AppRoutes.conditionsUtilisation),
          ),
          const Divider(height: 1),
          ListTile(
            leading: const Icon(Icons.info_outline),
            title: const Text('À propos'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.push(AppRoutes.aPropos),
          ),
        ],
      ),
    );
  }
}
