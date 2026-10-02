import 'package:flutter/material.dart';

import '../../../config/theme.dart';
import '../../consultation_rapide/domain/resultat.dart';
import '../domain/candidature.dart';

/// Last known result of a candidature, worded and coloured like the search
/// screen: phase label instead of the API code, the "not on the list"
/// sentence instead of the raw status, decision colour from
/// [tonaliteDecision] (a negative decision is never green).
class DernierResultat extends StatelessWidget {
  const DernierResultat({required this.candidature, super.key});

  final Candidature candidature;

  @override
  Widget build(BuildContext context) {
    final statut = candidature.dernierResultatStatut;
    if (statut == null) {
      return const Text(
        'Résultat pas encore publié',
        style: TextStyle(fontSize: 13, color: AppColors.texteAttenue),
      );
    }
    final phase = candidature.dernierResultatPhase;
    final libellePhase =
        phase == null ? null : PhasePublication.depuisApi(phase).libelle;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (libellePhase != null &&
            PhasePublication.depuisApi(phase!) !=
                PhasePublication.resultatUnique)
          Text(libellePhase,
              style:
                  const TextStyle(fontSize: 12, color: AppColors.texteAttenue)),
        if (statut == statutAbsentDeLaListe)
          const Text(
            'Toutes les listes de cette phase sont publiées : vous n’y '
            'figurez pas.',
            style: TextStyle(fontSize: 14),
          )
        else
          Text(
            statut,
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w700,
              color: switch (tonaliteDecision(statut)) {
                TonaliteDecision.positive => AppColors.succes,
                TonaliteDecision.negative => AppColors.erreur,
                TonaliteDecision.neutre => AppColors.texte,
              },
            ),
          ),
      ],
    );
  }
}
