# Motion design — Faso Résultats

Vidéo de présentation de la plateforme (62 s, 1920×1080, 30 i/s, sans son),
aux couleurs de la charte (`docs/CHARTE_GRAPHIQUE.md`).

| Fichier | Rôle |
|---|---|
| `faso-resultats-motion.html` | Animation source, autonome (Poppins et logos intégrés). S'ouvre dans un navigateur et tourne en boucle — utilisable telle quelle sur un écran de stand ou en fond de présentation. |
| `render.mjs` | Exporte l'animation en MP4, image par image (rendu parfaitement fluide). |

## Découpage

La vidéo distingue cinq services. Chacun a **sa couleur et son numéro**, rappelés
par une pastille en haut à gauche et un sommaire en haut à droite de chaque section.

| Temps | Scène | Message |
|---|---|---|
| 0 – 5 s | Logo | Bandes du drapeau, symbole, logotype lettre par lettre, slogan |
| 5 – 9 s | Jour de proclamation | « Des milliers de candidats attendent. » |
| 9 – 13 s | Vue d'ensemble | Les cinq services côte à côte (SMS marqué « Bientôt ») |
| 13 – 22 s | **01 Consultation simple** (vert) | Sans compte : examen → n° de PV → « ADMIS » |
| 22 – 32 s | **02 Compte candidat unifié** (bleu) | Facultatif. Connexion par téléphone + code, candidatures de plusieurs administrations réunies, résultat retrouvé automatiquement par CNIB |
| 32 – 42 s | **03 Concours paramilitaires** (violet) | Épreuves sportives → admissibilité → admission définitive ; « publication en cours » tant que la phase n'est pas clôturée |
| 42 – 50 s | **04 SMS** (jaune, « Bientôt ») | Inscription en ligne (PV + téléphone + consentement), SMS à la publication, alerte à chaque phase |
| 50 – 58 s | **05 Espace administrations** (bleu nuit) | Import → aperçu et correction → validation humaine → publication ; rôles, chiffrement, clôture des phases, audit |
| 58 – 62 s | Signature | Logo officiel, « Ensemble pour une éducation plus accessible ! », LUPORA Group |

Les candidats montrés sont fictifs (SANOU Richard et TRAORE Awa viennent de
`backend/seed.py`). Le texte du SMS reprend le format réel de
`NotificationEngine.formater_message_resultat`, sans le lien (domaine non encore
réservé).

Les affirmations restent vérifiables, comme pour la page d'accueil (décision
du 2026-09-30) : pas de « plateforme officielle » ni de « gratuit », l'app
mobile n'est pas présentée comme publiée, le SMS est explicitement « bientôt »
(Phase 2 non démarrée, dépend du contrat opérateur), pas de chiffres d'audience
inventés.

## Modifier et ré-exporter

Les textes et le minutage sont dans le HTML : chaque élément porte son instant
d'apparition **relatif au début de sa scène** (`style="--t:1.2s"`), chaque scène son
début et sa fin absolus (`--s` / `--e`) : décaler une scène ne demande de changer que
son `--s`. La durée totale est `DUREE` dans le script.

```bash
cd docs/brand/motion
npm i --no-save playwright && npx playwright install chromium   # une seule fois
node render.mjs faso-resultats-motion.html faso-resultats-motion.mp4 30
```

Prérequis : Node 18+ et ffmpeg. Environ 10 minutes de rendu.
Pour une version plus légère (WhatsApp, réseaux sociaux) :

```bash
ffmpeg -i faso-resultats-motion.mp4 -vf scale=1280:-2 -crf 26 faso-resultats-motion-720p.mp4
```
