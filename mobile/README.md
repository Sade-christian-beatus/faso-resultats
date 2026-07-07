# Faso Résultats — Application mobile candidat

Application Flutter consommant l'API publique et candidat de
[`../backend`](../backend). Voir `docs/API.md` pour le détail des endpoints
utilisés par écran.

## Prérequis

- Flutter 3.27.1 (channel stable), Dart 3.6.0
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

## Limites connues (voir docs/ROADMAP_MOBILE.md)

- **Notifications push (FCM)** : SDK intégré côté client, mais aucun backend
  d'enregistrement de token n'existe encore côté API — écrans concernés
  gated « bientôt disponible ».
- **Consultation par SMS** : écran gated, le SMS réel dépend d'un contrat
  opérateur (Orange Business) non encore signé.
- **Build Android release signé** : pas encore configuré (voir
  `docs/RELEASE.md`, à construire au jour 10).
- **iOS** : structure de projet générée, jamais testée (pas d'environnement
  macOS/Xcode disponible pendant le développement initial).
