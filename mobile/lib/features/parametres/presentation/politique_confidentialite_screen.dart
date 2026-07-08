import 'package:flutter/material.dart';

/// Contenu affiché directement dans l'app plutôt qu'un lien externe : aucune
/// page web dédiée n'est encore publiée pour ce document (voir
/// `docs/APDP_PROFIL_CANDIDAT.md`, qui reste la source de référence
/// technique — ce texte en est un résumé en langage clair). Un lien vers
/// une URL inexistante induirait l'utilisateur en erreur, comme pour la
/// consultation SMS du jour 7.
class PolitiqueConfidentialiteScreen extends StatelessWidget {
  const PolitiqueConfidentialiteScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Politique de confidentialité')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: const [
          _Section(
            titre: 'Consultation sans compte',
            texte: 'Rechercher un résultat avec votre numéro de récépissé '
                'ne nécessite aucune inscription et ne conserve aucune '
                'donnée vous concernant sur nos serveurs.',
          ),
          _Section(
            titre: 'Si vous créez un espace candidat',
            texte: 'Nous conservons votre numéro CNIB, votre date de '
                'naissance et votre téléphone, chiffrés, uniquement pour '
                'vérifier que vous êtes bien le propriétaire du récépissé '
                'que vous déclarez. Votre nom et votre email (facultatif) '
                "servent à l'affichage de votre profil et, si vous "
                "l'activez, à vous notifier de vos résultats.",
          ),
          _Section(
            titre: 'Ce que nous ne faisons jamais',
            texte: 'Aucune revente de données, aucun profilage commercial, '
                'aucune donnée partagée avec une administration en dehors '
                'de ce qui est strictement nécessaire à la vérification de '
                'vos candidatures.',
          ),
          _Section(
            titre: 'Vos droits',
            texte: 'Vous pouvez à tout moment consulter, exporter ou '
                'supprimer définitivement vos données depuis '
                'Profil > Sécurité et mes droits. La suppression de votre '
                'compte a un effet immédiat sur vos données personnelles.',
          ),
          _Section(
            titre: 'Contact',
            texte: 'Pour toute question ou demande relevant de la protection '
                'de vos données, un contact dédié est disponible depuis '
                'Profil > Sécurité et mes droits > Mes droits.',
          ),
          SizedBox(height: 8),
          Text(
            'Document de référence technique complet : '
            'docs/APDP_PROFIL_CANDIDAT.md (dépôt du projet).',
            style: TextStyle(fontSize: 12, color: Colors.grey),
          ),
        ],
      ),
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.titre, required this.texte});

  final String titre;
  final String texte;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(titre,
              style:
                  const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
          const SizedBox(height: 6),
          Text(texte, style: const TextStyle(fontSize: 14, height: 1.4)),
        ],
      ),
    );
  }
}
