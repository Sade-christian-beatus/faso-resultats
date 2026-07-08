# Faso Résultats — Application mobile candidat

Application Flutter consommant l'API publique et candidat de
[`../backend`](../backend). Voir `docs/API.md` pour le détail des endpoints
utilisés par écran.

## Prérequis

- Flutter 3.44.5 (channel stable), Dart 3.12.2 — dernière version stable au
  moment du développement (le prompt d'origine demande explicitement la
  dernière stable ; la version installée au jour 1, 3.27.1, était obsolète et
  a été corrigée au jour 2)
- Un backend Faso Résultats accessible (voir `../backend/README.md`)

## Installation locale

```bash
cd mobile
flutter pub get
```

## Lancer en développement

```bash
# Émulateur Android : 10.0.2.2 est l'alias vers localhost de la machine hôte.
flutter run --dart-define=ENV=dev

# Appareil physique ou backend distant (ex. tunnel ngrok) :
flutter run --dart-define=ENV=dev --dart-define=API_BASE_URL=https://xxxx.ngrok.io
```

## Tests

```bash
flutter analyze
dart format --output=none --set-exit-if-changed lib test
flutter test --coverage
```

## Architecture

Clean Architecture à 3 couches (`presentation` / `domain` / `data`) par
fonctionnalité sous `lib/features/`, state management Riverpod, navigation
go_router. Détail dans `docs/ARCHITECTURE.md`.

## Limites connues (voir docs/API.md pour le détail complet des écarts)

- **Notifications push (FCM)** : dépendances déclarées (`firebase_core`,
  `firebase_messaging`) mais SDK **non initialisé** — aucun projet Firebase
  réel configuré dans ce dépôt et aucun backend d'enregistrement de token
  côté API. Écran « Notifications » gated « bientôt disponible ».
- **Consultation par SMS** : écran gated, sans numéro ni syntaxe affichés —
  le SMS réel dépend d'un contrat opérateur (Orange Business) non encore
  signé (Phase 2, volontairement non démarrée).
- **Build Android release signé** : infrastructure de signature en place
  (`android/app/build.gradle`, `docs/RELEASE.md`), mais aucun keystore de
  production n'existe encore — les builds retombent sur la signature debug.
- **Test manuel multi-écrans et mesure de la taille de l'APK** : non faits
  dans l'environnement de développement (pas de SDK Android/émulateur
  disponible) — à faire avant toute publication, voir
  `docs/ARCHITECTURE.md` § Tests et polissage.
- **iOS** : structure de projet générée, jamais testée (pas d'environnement
  macOS/Xcode disponible pendant le développement initial).
