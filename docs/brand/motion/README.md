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
| 9 – 13 s | Vue d'ensemble | Les cinq services côte à côte |
| 13 – 22 s | **01 Consultation simple** (vert) | Sans compte : examen → n° de PV → « ADMIS » |
| 22 – 32 s | **02 Compte candidat unifié** (bleu) | Facultatif. Connexion par téléphone + code, candidatures de plusieurs administrations réunies, résultat retrouvé automatiquement par CNIB |
| 32 – 42 s | **03 Concours paramilitaires** (violet) | Épreuves sportives → admissibilité → admission définitive ; « publication en cours » tant que la phase n'est pas clôturée |
| 42 – 50 s | **04 SMS** (jaune) | Inscription en ligne (PV + téléphone + consentement), SMS à la publication, alerte à chaque phase |
| 50 – 58 s | **05 Espace administrations** (bleu nuit) | Import → aperçu et correction → validation humaine → publication ; rôles, chiffrement, clôture des phases, audit |
| 58 – 62 s | Signature | Logo officiel, « Ensemble pour une éducation plus accessible ! », LUPORA Group |

Les candidats montrés sont fictifs (SANOU Richard et TRAORE Awa viennent de
`backend/seed.py`). Le texte du SMS reprend le format réel de
`NotificationEngine.formater_message_resultat`, sans le lien (domaine non encore
réservé).

Les affirmations restent vérifiables, comme pour la page d'accueil (décision
du 2026-09-30) : pas de « plateforme officielle » ni de « gratuit », l'app
mobile n'est pas présentée comme publiée, pas de chiffres d'audience inventés.
Le badge « Bientôt » du SMS a été retiré à la demande du porteur du projet
(2026-10-06) ; la section SMS garde la mention « Service en préparation avec les
opérateurs télécom », la Phase 2 n'étant pas démarrée.

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
### Versions courtes par service (réseaux sociaux)

Chaque version courte enchaîne une section complète et la signature finale
(57,6 → 61,6 s), sans rien rendre en double : ce sont des extraits de la même
timeline, montés par l'argument `segments` de `render.mjs`.

| Fichier | Segments | Durée |
|---|---|---|
| `faso-resultats-01-consultation-simple.mp4` | `13.4-22.4,57.6-61.6` | 13 s |
| `faso-resultats-02-compte-candidat.mp4` | `22.4-32.2,57.6-61.6` | 13,8 s |
| `faso-resultats-03-concours-paramilitaires.mp4` | `32.2-42.4,57.6-61.6` | 14,2 s |
| `faso-resultats-04-sms.mp4` | `42.4-49.8,57.6-61.6` | 11,4 s |
| `faso-resultats-05-administrations.mp4` | `49.8-57.6,57.6-61.6` | 11,8 s |

```bash
node render.mjs faso-resultats-motion.html faso-resultats-01-consultation-simple.mp4 30 13.4-22.4,57.6-61.6
```

Si une scène est décalée (`--s` / `--e` dans le HTML), reporter ses nouvelles bornes ici.

Pour une version plus légère (WhatsApp, réseaux sociaux) :

```bash
ffmpeg -i faso-resultats-motion.mp4 -vf scale=1280:-2 -crf 26 faso-resultats-motion-720p.mp4
```
