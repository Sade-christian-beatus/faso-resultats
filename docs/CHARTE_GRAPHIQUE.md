# Charte graphique — Faso Résultats

> Référence visuelle : [`docs/brand/charte-graphique.webp`](brand/charte-graphique.webp)
> (planche fournie par le porteur du projet le 2026-09-28).
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

**Poppins** (400, 500, 600, 700), repli sur la police système.

- Web : chargée depuis Google Fonts avec `display=swap` (le texte s'affiche
  immédiatement en police système sur 3G, Poppins remplace ensuite). Coût
  ≈ 30 Ko pour les 4 graisses en sous-ensemble latin — dans l'objectif
  < 500 Ko. ⚠️ À auto-héberger avant la mise en production sur serveurs
  burkinabè (souveraineté, et ne pas dépendre de Google pour l'affichage).
- Mobile : police système pour l'instant (Poppins non encore embarquée, voir
  « Reste à faire »).

## Logo et icônes

| Fichier | Contenu | Statut |
|---------|---------|--------|
| `frontend/public/assets/logo-mark.svg` | Symbole simplifié (feuille de résultat + coche + toque, sur carré vert) | **Provisoire**, redessiné à la main d'après la planche |
| `frontend/public/assets/favicon.svg` | Toque blanche sur disque bleu nuit (variante « Favicon » de la planche) | Provisoire |

Le logotype texte (« Faso★Résultats ») est rendu en HTML/Flutter avec Poppins
plutôt qu'en image : net à toutes les tailles, zéro octet supplémentaire.

## Éléments de la planche volontairement **non** repris

La planche est une maquette de communication ; certains éléments contredisent
des décisions du projet et ne doivent pas être implémentés tels quels :

- **« Recherche par nom » / « N° de candidat, nom… »** : la recherche publique
  se fait uniquement par numéro de PV (+ jury). Chercher par nom permettrait
  d'énumérer les candidats (décision du 2026-07-03, `CLAUDE.md`).
- **« Universités »** : hors du périmètre actuel (examens CEP/BEPC/BAC et
  concours de la Fonction publique).
- **Silhouette de la carte du Burkina Faso dans le logo** : non reprise dans le
  symbole provisoire ; à intégrer depuis le fichier vectoriel officiel.

## Reste à faire

1. Obtenir les **fichiers sources vectoriels** (SVG/AI/PDF) du logo complet,
   des variantes horizontale/verticale et monochromes, et remplacer les SVG
   provisoires.
2. Générer les **icônes d'application** Android (`mipmap-*`, icône adaptative)
   et iOS (`AppIcon.appiconset`) à partir de l'icône officielle, ainsi que
   l'écran de démarrage natif.
3. Embarquer **Poppins** dans l'app Flutter (fichiers `.ttf` dans
   `mobile/assets/fonts/` + déclaration `fonts:` dans `pubspec.yaml` — pas de
   paquet `google_fonts`, qui téléchargerait la police au premier lancement).
4. **Auto-héberger Poppins** côté web (fichiers `.woff2` dans
   `frontend/public/fonts/`) avant la mise en production.
5. Déclinaisons PNG du favicon (32×32, 180×180 `apple-touch-icon`) et image
   de partage réseaux sociaux (`og:image`).
