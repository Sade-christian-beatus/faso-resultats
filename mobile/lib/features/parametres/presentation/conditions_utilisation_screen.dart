import 'package:flutter/material.dart';

class ConditionsUtilisationScreen extends StatelessWidget {
  const ConditionsUtilisationScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Conditions d'utilisation")),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: const [
          _Section(
            titre: 'Objet',
            texte: 'Faso Résultats permet de consulter les résultats '
                "d'examens et concours publiés par les administrations "
                'partenaires, et de suivre ses candidatures depuis un '
                'espace personnel optionnel.',
          ),
          _Section(
            titre: 'Fiabilité des résultats',
            texte: "Chaque résultat publié provient d'un fichier officiel "
                "transmis par l'administration concernée, vérifié "
                "manuellement avant publication. En cas d'écart avec le "
                'document officiel remis par votre administration, ce '
                'dernier fait foi.',
          ),
          _Section(
            titre: "Usage de l'espace candidat",
            texte: "L'espace candidat est réservé à un usage personnel. "
                'Vous vous engagez à ne déclarer que des récépissés qui '
                'vous appartiennent réellement. Un compte utilisé de '
                'manière abusive peut être suspendu.',
          ),
          _Section(
            titre: 'Évolution du service',
            texte: 'Le service peut évoluer (nouvelles fonctionnalités, '
                'nouvelles administrations partenaires). Les changements '
                "majeurs affectant vos données sont annoncés dans l'app.",
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
