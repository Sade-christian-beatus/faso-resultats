# Motion design — Faso Résultats

Vidéo de présentation de la plateforme (32 s, 1920×1080, 30 i/s, sans son),
aux couleurs de la charte (`docs/CHARTE_GRAPHIQUE.md`).

| Fichier | Rôle |
|---|---|
| `faso-resultats-motion.html` | Animation source, autonome (Poppins et logos intégrés). S'ouvre dans un navigateur et tourne en boucle — utilisable telle quelle sur un écran de stand ou en fond de présentation. |
| `render.mjs` | Exporte l'animation en MP4, image par image (rendu parfaitement fluide). |

## Découpage

| Temps | Scène | Message |
|---|---|---|
| 0 – 5 s | Logo | Bandes du drapeau, symbole, logotype lettre par lettre, slogan « Vos résultats en un clic » |
| 5 – 9 s | Jour de proclamation | Grille de candidats qui s'allument : « Des milliers de candidats attendent. » |
| 9 – 18 s | Démonstration | Téléphone : choix de l'examen → saisie du n° de PV → « ADMIS », en 3 étapes |
| 18 – 23 s | Valeurs | Rapide · Fiable · Accessible |
| 23 – 28 s | Administrations | Import → aperçu et correction → validation humaine → publication ; chiffrement, isolation, audit |
| 28 – 32 s | Signature | Logo officiel, « Ensemble pour une éducation plus accessible ! », LUPORA Group |

Le candidat de la démonstration (SANOU Richard, BAC 2026, PV 000201) est fictif :
c'est une donnée de `backend/seed.py`.

Les affirmations restent vérifiables, comme pour la page d'accueil (décision
du 2026-09-30) : pas de « plateforme officielle » ni de « gratuit », l'app
mobile est annoncée « bientôt », pas de SMS (Phase 2 non démarrée), pas de
chiffres d'audience inventés.

## Modifier et ré-exporter

Les textes et le minutage sont dans le HTML : chaque élément porte son instant
d'apparition (`style="--t:12.3s"`), chaque scène ses instants d'entrée et de sortie
(`--in` / `--out`) ; la durée totale est `DUREE` dans le script.

```bash
cd docs/brand/motion
npm i --no-save playwright && npx playwright install chromium   # une seule fois
node render.mjs faso-resultats-motion.html faso-resultats-motion.mp4 30
```

Prérequis : Node 18+ et ffmpeg. Environ 5 minutes de rendu pour 32 s.
Pour une version plus légère (WhatsApp, réseaux sociaux) :

```bash
ffmpeg -i faso-resultats-motion.mp4 -vf scale=1280:-2 -crf 26 faso-resultats-motion-720p.mp4
```
