import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';

import '../../../config/theme.dart';
import '../domain/resultat.dart';

class ResultatCard extends StatelessWidget {
  const ResultatCard({required this.resultat, super.key});

  final Resultat resultat;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    '${resultat.prenom} ${resultat.nom}',
                    style: const TextStyle(
                        fontSize: 17, fontWeight: FontWeight.w700),
                  ),
                ),
                BadgeDecision(resultat: resultat),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              'Récépissé n° ${resultat.numeroPv} — Jury ${resultat.jury}',
              style:
                  const TextStyle(fontSize: 13, color: AppColors.texteAttenue),
            ),
            const SizedBox(height: 12),
            _LigneDetail(label: 'Phase', valeur: resultat.phase.libelle),
            if (resultat.phaseSuivanteAttendue != null)
              _LigneDetail(
                label: 'Prochaine étape',
                valeur: resultat.phaseSuivanteAttendue!.libelle,
              ),
            if (resultat.rangAffiche != null)
              _LigneDetail(label: 'Rang', valeur: resultat.rangAffiche!),
            if (resultat.moyenne != null)
              _LigneDetail(
                  label: 'Moyenne',
                  valeur: resultat.moyenne!.toStringAsFixed(2)),
            if (resultat.etablissement != null)
              _LigneDetail(
                  label: 'Établissement', valeur: resultat.etablissement!),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _partager(resultat),
                    icon: const Icon(Icons.share_outlined, size: 18),
                    label: const Text('Partager'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _afficherSmsBientotDisponible(context),
                    icon: const Icon(Icons.sms_outlined, size: 18),
                    label: const Text('Recevoir par SMS'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  void _partager(Resultat resultat) {
    final texte = '${resultat.prenom} ${resultat.nom} — ${resultat.decision} '
        '(récépissé ${resultat.numeroPv}, jury ${resultat.jury}) — Faso Résultats';
    Share.share(texte);
  }

  // Aucun endpoint backend n'envoie un résultat par SMS à un numéro arbitraire
  // (hors compte candidat) — voir mobile/docs/API.md, écart identifié au
  // jour 1. Gated plutôt que silencieusement absent, pour que l'intention
  // reste visible dans l'app.
  void _afficherSmsBientotDisponible(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Bientôt disponible.')),
    );
  }
}

/// Decision pill, coloured by [Resultat.tonalite]. Shared with the
/// phase-by-phase card.
class BadgeDecision extends StatelessWidget {
  const BadgeDecision({required this.resultat, super.key});

  final Resultat resultat;

  @override
  Widget build(BuildContext context) {
    final couleur = switch (resultat.tonalite) {
      TonaliteDecision.positive => AppColors.succes,
      TonaliteDecision.negative => AppColors.erreur,
      TonaliteDecision.neutre => AppColors.avertissement,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: couleur.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        resultat.decision,
        style: TextStyle(
            color: couleur, fontWeight: FontWeight.w700, fontSize: 13),
      ),
    );
  }
}

class _LigneDetail extends StatelessWidget {
  const _LigneDetail({required this.label, required this.valeur});

  final String label;
  final String valeur;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        children: [
          SizedBox(
            width: 110,
            child: Text(
              label,
              style:
                  const TextStyle(fontSize: 13, color: AppColors.texteAttenue),
            ),
          ),
          Expanded(
            child: Text(
              valeur,
              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }
}
