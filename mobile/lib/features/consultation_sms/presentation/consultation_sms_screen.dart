import 'package:flutter/material.dart';

import '../../../core/widgets/empty_view.dart';

/// Écran « Consulter par SMS » (jour 7), pour les candidats sans connexion
/// internet à un moment donné. Gated plutôt que réalisé : la consultation
/// par SMS dépend de l'intégration Orange Business (Phase 2, voir
/// CLAUDE.md § Roadmap), volontairement non démarrée — il n'existe donc
/// encore ni numéro court réel ni syntaxe SMS définie côté organisme. Un
/// faux numéro ou une fausse syntaxe affichés ici induiraient un candidat
/// en erreur (un SMS envoyé à un numéro inventé ne reçoit jamais de
/// réponse) : ce risque est jugé plus grave qu'un écran incomplet.
class ConsultationSmsScreen extends StatelessWidget {
  const ConsultationSmsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Consulter par SMS')),
      body: const EmptyView(
        message: "La consultation par SMS n'est pas encore disponible.\n\n"
            'En attendant, utilisez « Consulter mon résultat » dès que vous '
            'retrouvez une connexion internet, même faible.',
        icon: Icons.sms_outlined,
      ),
    );
  }
}
