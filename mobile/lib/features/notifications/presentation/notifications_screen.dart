import 'package:flutter/material.dart';

import '../../../core/widgets/empty_view.dart';

/// Écran « Notifications » (jour 6). Gated plutôt que retiré : aucune
/// infrastructure push n'existe encore côté backend (pas de modèle de
/// notification, pas d'endpoint d'enregistrement de token FCM — voir
/// mobile/docs/API.md). Le SDK FCM (`firebase_core`/`firebase_messaging`,
/// déjà en dépendance depuis le jour 1) n'est délibérément pas initialisé
/// ici : sans projet Firebase configuré (pas de `google-services.json` /
/// `GoogleService-Info.plist` dans ce dépôt), l'appeler planterait l'app au
/// démarrage plutôt que d'échouer proprement. La préférence
/// « Notifications push » de l'écran Profil reste modifiable dès maintenant
/// (elle est persistée côté backend) : seule la livraison réelle manque.
class NotificationsScreen extends StatelessWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Notifications')),
      body: const EmptyView(
        message: 'Les notifications push arrivent bientôt.\n\n'
            'Votre préférence est déjà enregistrée (voir Profil > '
            'Notifications push) : vous recevrez vos résultats dès que '
            'cette fonctionnalité sera activée.',
        icon: Icons.notifications_none,
      ),
    );
  }
}
