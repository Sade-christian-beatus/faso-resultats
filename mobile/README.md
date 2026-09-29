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

1. **Démarrer le backend** (depuis la racine du dépôt) : `docker compose up`. L'API
   écoute sur le port 8000 de toutes les interfaces réseau (`--host 0.0.0.0`),
   donc un téléphone du même Wi-Fi peut la joindre.
2. **Vérifier l'environnement Flutter** : `flutter doctor` (Android SDK, émulateur
   ou téléphone en mode développeur avec débogage USB activé).
3. **Lister les appareils** : `flutter devices`.
4. **Lancer l'app** depuis `mobile/`, selon l'appareil :

```bash
# Émulateur Android : 10.0.2.2 est l'alias vers localhost de la machine hôte.
flutter run --dart-define=ENV=dev

# Téléphone Android physique (même Wi-Fi que l'ordinateur) : IP locale de la
# machine qui fait tourner le backend (ip addr / ifconfig), jamais localhost.
flutter run --dart-define=ENV=dev --dart-define=API_BASE_URL=http://192.168.1.20:8000

# Simulateur iOS (macOS uniquement) : localhost désigne directement la machine.
flutter run --dart-define=ENV=dev --dart-define=API_BASE_URL=http://localhost:8000

# Backend distant ou tunnel (ngrok...) :
flutter run --dart-define=ENV=dev --dart-define=API_BASE_URL=https://xxxx.ngrok.io
```

Pendant l'exécution : `r` = hot reload, `R` = redémarrage complet, `q` = quitter.

### Sous Windows (invite de commandes `cmd`)

- **Docker Desktop doit être démarré** (icône « Engine running ») avant
  `docker compose up`, sinon erreur `...dockerDesktopLinuxEngine... context canceled`.
  Vérifier avec `docker version` (les sections Client **et** Server doivent répondre).
- Toutes les commandes `flutter` se lancent **depuis le dossier `mobile`**
  (`cd mobile`), sinon : `No pubspec.yaml file found`.
- `#` n'est pas un commentaire dans `cmd` : taper **une seule commande à la fois**,
  sans le texte de commentaire.
- Adresse IP locale du PC : `ipconfig` (ligne « Adresse IPv4 » de la carte Wi-Fi).
- Téléphone physique : autoriser le port 8000 dans le pare-feu Windows (réseau
  privé), sinon le téléphone n'atteint pas l'API.
- Pas de simulateur iOS sous Windows (macOS uniquement).

```bat
cd C:\faso-resultats
docker compose up -d
cd mobile
flutter pub get
flutter devices
flutter run --dart-define=ENV=dev
```

Le HTTP non chiffré (API locale) n'est autorisé qu'en **debug** sur Android
(`android/app/src/debug/AndroidManifest.xml`) ; les builds release n'acceptent que
HTTPS. Sur iOS, seul le réseau local est ouvert (`NSAllowsLocalNetworking`).

Comptes de démonstration (créés par `backend/seed.py`) : se connecter avec le
téléphone `+22670000001`, `+22670000002` ou `+22670000003`. Aucun SMS n'est
envoyé (Phase 2) : hors production, le code OTP est renvoyé dans la réponse de
l'API (`code_otp_debug`) et visible dans les logs du backend.

## Construire un APK

```bash
flutter build apk --release   # build/app/outputs/flutter-apk/app-release.apk
flutter build apk --debug     # plus rapide, pour tester sur un téléphone
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
