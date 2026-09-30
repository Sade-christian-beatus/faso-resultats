import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../config/constants.dart';
import '../../../config/routes.dart';
import '../../../config/theme.dart';
import '../../../core/widgets/contact_support_sheet.dart';

/// "FAQ" shortcut of the home screen: the questions candidates ask most,
/// then the support phone numbers.
class AideScreen extends StatelessWidget {
  const AideScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Aide et questions fréquentes')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const _Question(
              question: 'Où trouver mon numéro de PV ?',
              reponse: 'Il figure sur votre convocation ou sur le récépissé '
                  "remis lors de votre inscription à l'examen ou au concours.",
            ),
            const _Question(
              question: "Mon résultat n'apparaît pas. Pourquoi ?",
              reponse: "Un résultat n'est visible qu'une fois la liste "
                  "validée et publiée par l'administration organisatrice. "
                  'Vérifiez aussi le numéro saisi et, si besoin, précisez '
                  'votre jury ou centre. Certains concours publient leurs '
                  'listes phase par phase.',
            ),
            const _Question(
              question: 'Faut-il créer un compte ?',
              reponse: 'Non. La consultation par numéro de PV est libre. '
                  "L'espace candidat sert à suivre plusieurs examens et "
                  'concours au même endroit.',
            ),
            const _Question(
              question: "Je n'ai pas de connexion internet.",
              reponse: 'Les résultats déjà consultés restent affichés '
                  'quelque temps sans connexion. La consultation par SMS '
                  'sera proposée prochainement.',
            ),
            _Question(
              question: 'Que devient mon numéro de téléphone ?',
              reponse: 'Vos données servent uniquement à vérifier votre '
                  'identité et à vous informer de vos résultats.',
              action: TextButton(
                onPressed: () =>
                    context.push(AppRoutes.politiqueConfidentialite),
                child: const Text('Politique de confidentialité'),
              ),
            ),
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "Besoin d'aide ?",
                      style:
                          TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Notre équipe vous répond par téléphone.',
                      style: TextStyle(color: AppColors.texteAttenue),
                    ),
                    const SizedBox(height: 12),
                    for (final numero in ContactSupport.telephones)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: OutlinedButton.icon(
                          onPressed: () => appelerSupport(context, numero),
                          icon: const Icon(Icons.call),
                          label: Text(ContactSupport.formater(numero)),
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Question extends StatelessWidget {
  const _Question({required this.question, required this.reponse, this.action});

  final String question;
  final String reponse;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      clipBehavior: Clip.antiAlias,
      child: ExpansionTile(
        shape: const Border(),
        title:
            Text(question, style: const TextStyle(fontWeight: FontWeight.w600)),
        childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
        expandedCrossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(reponse, style: const TextStyle(height: 1.4)),
          if (action != null) action!,
        ],
      ),
    );
  }
}
