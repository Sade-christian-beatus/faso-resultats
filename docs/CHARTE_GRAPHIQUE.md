# Charte graphique — Faso Résultats

> Référence visuelle : [`docs/brand/charte-graphique.webp`](brand/charte-graphique.webp)
> (planche fournie par le porteur du projet le 2026-09-28) et logo officiel
> [`docs/brand/logo-faso-resultats.webp`](brand/logo-faso-resultats.webp)
> (fond transparent, 1774×887 — fichier source de toutes les déclinaisons).
> Ce document traduit la planche en règles applicables au code web et mobile.

## Signature

- **Nom :** Faso Résultats — logotype en deux lignes : « Faso » en bleu nuit
  suivi d'une étoile jaune, « Résultats » en vert Faso.
- **Slogan :** « Vos résultats en un clic » (encadré d'un tiret rouge à gauche
  et d'un tiret vert à droite).
- **Valeurs :** Rapide (en quelques secondes) · Fiable (des sources
  officielles) · Accessible (partout, tout le temps).
- **Signature institutionnelle :** « Ensemble pour une éducation plus accessible ! »

## Palette

| Nom | Hex | Rôle | Usage dans le code |
|-----|-----|------|--------------------|
| Vert Faso | `#00A651` | Confiance, réussite | `faso-500` (web), `AppColors.vertFaso` (mobile) — décor, icônes, barre tricolore |
| Vert foncé (dérivé) | `#007A3D` | Accessibilité | `faso-700`, `AppColors.vertFonce` — boutons, texte vert, surfaces portant du texte blanc |
| Rouge | `#E30613` | Énergie, engagement | `rouge`, `AppColors.rougeFaso` — accents décoratifs uniquement |
| Jaune | `#FFD000` | Excellence, espoir | `jaune`, `AppColors.jauneFaso` — étoile, accents ; jamais de texte jaune sur fond blanc |
| Bleu nuit | `#0B1F2D` | Sérieux, crédibilité | `nuit`, `AppColors.bleuNuit` — texte principal, favicon |
| Gris clair | `#F4F6F8` | Équilibre, modernité | `clair`, `AppColors.fond` — fond de page |

**Règle d'accessibilité :** du texte blanc sur `#00A651` n'atteint pas le
contraste WCAG AA (≈ 3:1). Tout bouton ou bandeau portant du texte utilise le
vert foncé `#007A3D` (≈ 5,3:1). Le vert officiel reste réservé au décor.

**Couleurs d'état :** les statuts (admis / ajourné / en attente / erreur)
gardent leurs propres couleurs (`red-*`, `amber-*` côté web ;
`AppColors.succes`, `.erreur`, `.avertissement` côté mobile). Un badge « en
attente » ne doit pas être confondu avec un accent décoratif jaune, et une
décision « ajourné » ne doit jamais emprunter le rouge de marque par hasard
de style — la lisibilité de la décision prime sur la marque.

## Typographie

**Poppins** (400, 500, 600, 700, 800), repli sur la police système.

- Web : **auto-hébergée** depuis le 2026-10-02 (`frontend/public/fonts/`,
  sous-ensemble latin, ≈ 39 Ko pour les 5 graisses, licence SIL OFL dans
  `fonts/OFL.txt`), déclarée dans `frontend/src/app.css` avec
  `font-display: swap` (le texte s'affiche immédiatement en police système
  sur 3G, Poppins remplace ensuite). Plus aucune requête vers Google.
- Mobile : police système pour l'instant (Poppins non encore embarquée, voir
  « Reste à faire »).

## Logo et icônes

Toutes les déclinaisons sont générées depuis `docs/brand/logo-faso-resultats.webp`
(recadrage + redimensionnement, aucune retouche du dessin) :

| Fichier | Contenu | Usage |
|---------|---------|-------|
| `frontend/public/assets/logo.webp` | Logo complet (symbole + nom + slogan), 720 px, ≈ 60 Ko | En-tête de la page de consultation publique |
| `frontend/public/assets/logo-symbole.webp` | Symbole seul, 256 px | En-têtes admin et espace candidat (à côté du nom en texte) |
| `frontend/public/assets/favicon-32.png` | Symbole, 32 px | Icône d'onglet |
| `frontend/public/assets/apple-touch-icon.png` | Symbole sur fond blanc, 180 px | Raccourci écran d'accueil iPhone |
| `mobile/assets/images/logo.webp` | Logo complet, 720 px | Écran d'accueil de l'app |
| `mobile/assets/images/hero.webp` | Photo de la bannière recadrée en portrait, 400 px, ≈ 19 Ko | Carrousel de l'écran d'accueil de l'app |
| `frontend/public/assets/hero.webp` | Photo de la bannière recadrée, 560 px, ≈ 25 Ko | Bannière de la page d'accueil web |

La photo source (fournie par le porteur du projet le 2026-09-30) est conservée
dans `docs/brand/photo-banniere.webp` (1996×788).
| `mobile/android/.../mipmap-*/ic_launcher.png`, `mobile/ios/.../AppIcon.appiconset/*.png` | Symbole sur fond blanc opaque (iOS refuse la transparence) | Icône de l'app |

Sur les petites tailles (admin, espace candidat), le nom est rendu en texte
(« Faso★Résultats », Poppins) à côté du symbole : le logo complet y serait
illisible.

⚠️ Le logo n'existe qu'en version pour **fond clair** (« Faso » en bleu nuit).
Ne pas le poser sur un fond sombre ou vert sans une variante dédiée. Dans l'en-tête
vert de l'app mobile (maquette du 2026-09-30), il est posé sur une plaque
blanche arrondie en attendant cette variante.

## Composants de la page publique

- **Page d'accueil (maquette web du 2026-09-30)** : bannière verte dégradée,
  pastilles d'icône rondes par catégorie — vert foncé (examens), bleu `#1D4E89`
  (concours directs), jaune avec icône bleu nuit (fonction publique), violet
  `#6D28D9` (paramilitaires) —, cartes blanches à coins arrondis, pied de page
  vert foncé. Le drapeau et le téléphone de la bannière sont dessinés en CSS
  (aucune image à charger) en attendant la photo officielle. Remplace la bande
  défilante « Examens et concours disponibles » (2026-09-28), absente de la
  maquette : la liste « Dernières publications » joue désormais ce rôle.
- **Frise des phases** (concours paramilitaires) : une pastille par phase — verte
  pour un résultat, ambre pour « publication en cours », grise pour « ne figure pas »
  ou « à venir ».

## Éléments de la planche volontairement **non** repris

La planche est une maquette de communication ; certains éléments contredisent
des décisions du projet et ne doivent pas être implémentés tels quels :

- **« Recherche par nom » / « N° de candidat, nom… »** : la recherche publique
  se fait uniquement par numéro de PV (+ jury). Chercher par nom permettrait
  d'énumérer les candidats (décision du 2026-07-03, `CLAUDE.md`).
- **« Universités »** : hors du périmètre actuel (examens CEP/BEPC/BAC et
  concours de la Fonction publique).

## Reste à faire

1. Obtenir une **version vectorielle** (SVG/AI/PDF) du logo : le fichier actuel
   est une image matricielle, suffisante pour l'écran mais pas pour
   l'impression grand format (signalétique, goodies).
2. Variante **fond sombre** du logo (et monochrome), et **icône adaptative
   Android** (premier plan + fond séparés, Android 8+) — les icônes actuelles
   sont des carrés blancs classiques.
3. Écran de démarrage natif (Android/iOS) aux couleurs de la marque.
4. Embarquer **Poppins** dans l'app Flutter (fichiers `.ttf` dans
   `mobile/assets/fonts/` + déclaration `fonts:` dans `pubspec.yaml` — pas de
   paquet `google_fonts`, qui téléchargerait la police au premier lancement).
5. ~~Auto-héberger Poppins côté web~~ — fait le 2026-10-02.
6. Image de partage réseaux sociaux (`og:image`).
