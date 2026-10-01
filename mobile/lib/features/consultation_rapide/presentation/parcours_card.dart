import 'package:flutter/material.dart';

import '../../../config/theme.dart';
import '../../../core/utils/date_formatter.dart';
import '../domain/parcours.dart';
import 'resultat_card.dart';

/// Phase-by-phase progress of one candidate (paramilitary competitions,
/// docs/CONTEXTE_METIER.md § 2.4): one dot per phase, same wording as the web
/// page (frontend/public/js/public.js, `renderEtape`). "Ne figure pas" is only
/// ever shown once the administration closed the phase — the server decides,
/// this widget only displays [EtapeParcours.situation].
class ParcoursCard extends StatelessWidget {
  const ParcoursCard({required this.parcours, super.key});

  final ParcoursCandidat parcours;

  @override
  Widget build(BuildContext context) {
    final identite = parcours.identite;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (identite != null)
              Text(
                '${identite.prenom} ${identite.nom}',
                style:
                    const TextStyle(fontSize: 17, fontWeight: FontWeight.w700),
              ),
            const SizedBox(height: 4),
            Text(
              'Récépissé n° ${parcours.numeroPv} — Jury ${parcours.jury}',
              style:
                  const TextStyle(fontSize: 13, color: AppColors.texteAttenue),
            ),
            const SizedBox(height: 16),
            for (var i = 0; i < parcours.etapes.length; i++)
              _LigneEtape(
                etape: parcours.etapes[i],
                derniere: i == parcours.etapes.length - 1,
              ),
          ],
        ),
      ),
    );
  }
}

class _LigneEtape extends StatelessWidget {
  const _LigneEtape({required this.etape, required this.derniere});

  final EtapeParcours etape;
  final bool derniere;

  Color get _couleurPastille => switch (etape.situation) {
        SituationCandidat.resultat => AppColors.vertFonce,
        SituationCandidat.enAttente => AppColors.avertissement,
        SituationCandidat.neFigurePas => AppColors.texteAttenue,
        SituationCandidat.aVenir ||
        SituationCandidat.nonConcerne =>
          const Color(0xFFD0D5DD),
      };

  @override
  Widget build(BuildContext context) {
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Timeline: dot + connector to the next phase.
          SizedBox(
            width: 20,
            child: Column(
              children: [
                const SizedBox(height: 3),
                Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    color: _couleurPastille,
                    shape: BoxShape.circle,
                  ),
                ),
                if (!derniere)
                  Expanded(
                    child: Container(width: 2, color: const Color(0xFFE7EAEE)),
                  ),
              ],
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Padding(
              padding: EdgeInsets.only(bottom: derniere ? 0 : 16),
              child: Semantics(
                container: true,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      etape.phase.libelle,
                      style: const TextStyle(
                          fontSize: 14, fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 4),
                    _DetailEtape(etape: etape),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _DetailEtape extends StatelessWidget {
  const _DetailEtape({required this.etape});

  final EtapeParcours etape;

  static const _texte = TextStyle(fontSize: 13);
  static const _texteAttenue =
      TextStyle(fontSize: 12.5, color: AppColors.texteAttenue);

  @override
  Widget build(BuildContext context) {
    final resultat = etape.resultat;
    switch (etape.situation) {
      case SituationCandidat.resultat when resultat != null:
        final date = resultat.datePublicationPhase;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Wrap(
              spacing: 8,
              runSpacing: 4,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                BadgeDecision(resultat: resultat),
                if (resultat.rangAffiche != null)
                  Text('Rang : ${resultat.rangAffiche}', style: _texteAttenue),
              ],
            ),
            if (date != null) ...[
              const SizedBox(height: 4),
              Text('Publié le ${DateFormatter.pourAffichage(date)}',
                  style: _texteAttenue),
            ],
            if (resultat.phaseSuivanteAttendue != null) ...[
              const SizedBox(height: 4),
              Text(
                'Prochaine étape : ${resultat.phaseSuivanteAttendue!.libelle}',
                style: _texteAttenue,
              ),
            ],
          ],
        );
      case SituationCandidat.enAttente:
        return const Text(
          'Publication en cours : votre nom ne figure pas sur les listes '
          "publiées à ce jour. D'autres listes peuvent encore paraître.",
          style: _texte,
        );
      case SituationCandidat.neFigurePas:
        return const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Toutes les listes de cette phase sont publiées : vous n’y '
              'figurez pas.',
              style: _texte,
            ),
            SizedBox(height: 2),
            Text(
              "En cas de doute, rapprochez-vous de l'organisateur du "
              'concours.',
              style: _texteAttenue,
            ),
          ],
        );
      case SituationCandidat.nonConcerne:
        return const Text('Non concerné', style: _texteAttenue);
      case SituationCandidat.resultat:
      case SituationCandidat.aVenir:
        return const Text('Pas encore publiée', style: _texteAttenue);
    }
  }
}
