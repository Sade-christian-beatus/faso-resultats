# Architecture — Faso Résultats mobile

## Vue d'ensemble

Clean Architecture à 3 couches, une par fonctionnalité sous `lib/features/` :

```
lib/features/<feature>/
├── data/          # Repositories concrets, clients API, modèles JSON
├── domain/        # Entités, contrats de repository (interfaces), use cases
└── presentation/  # Écrans, widgets, providers Riverpod
```

`lib/core/` regroupe ce qui traverse toutes les features (réseau, stockage,
erreurs, widgets partagés, utilitaires). `lib/config/` regroupe la
configuration globale de l'app (thème, routes, environnement, constantes).

## State management : Riverpod

Choisi plutôt que Provider pur (meilleure testabilité, pas de `BuildContext`
requis pour lire un provider en dehors du widget tree) et plutôt que BLoC
(moins de code boilerplate pour ce volume d'écrans — pas de sur-ingénierie,
cohérent avec la préférence du projet backend pour la simplicité). Pas de
fichier d'injection centralisé de type `get_it` : chaque provider Riverpod
déclare directement ses dépendances via `ref.watch(...)`, ce que Riverpod
permet nativement sans registre séparé.

## Navigation : go_router

Choisi plutôt qu'`auto_route` : déclaratif, sans étape de génération de code
obligatoire pour les routes simples de cette app (peu d'écrans imbriqués,
peu de routes typées complexes). `auto_route` apporterait des routes
typées via `build_runner`, utile sur de très grosses apps multi-équipes —
gain marginal ici pour un coût de complexité réel.

## Réseau : Dio + intercepteurs

Un seul client Dio (`lib/core/network/dio_client.dart`), avec :

- `AuthInterceptor` : ajoute le token de session à chaque requête, notifie un
  callback sur 401 (la couche réseau ne navigue jamais elle-même — séparation
  stricte avec la couche presentation).
- `RetryInterceptor` : une seule nouvelle tentative sur erreur réseau
  transitoire (timeout, connexion perdue) — pertinent en 3G instable, jamais
  sur une erreur serveur reçue (4xx/5xx).
- `LogInterceptor` (uniquement en `kDebugMode`) : jamais de logs réseau en
  release, conforme à l'exigence « pas de logs de données sensibles ».

`dio_cache_interceptor` est une dépendance déjà déclarée, câblée au jour 9
(gestion hors-ligne) plutôt qu'au jour 1, pour ne pas construire une couche
de cache avant d'avoir des données réelles à mettre en cache.

## Erreurs : exceptions (data) → Failure (domain/presentation)

Pas de type `Either`/`Result` générique (pas de dépendance `dartz`/`fpdart`) :
un simple `try/catch` par repository suffit à ce volume de code, et un
sealed class `Failure` (voir `lib/core/errors/failures.dart`) porte déjà un
message prêt à afficher, en français, jamais un code d'erreur brut.

## Stockage

- `flutter_secure_storage` : uniquement le token de session candidat
  (Keystore Android / Keychain iOS).
- `shared_preferences` : préférences non sensibles uniquement (langue).

## Lint : very_good_analysis

Quatre règles désactivées explicitement dans `analysis_options.yaml`, avec
justification en commentaire : `always_use_package_imports` (imports
relatifs idiomatiques en Flutter), `lines_longer_than_80_chars` et
`require_trailing_commas` (les deux entrent en conflit direct avec le
comportement par défaut de `dart format`), `sort_pub_dependencies`
(pubspec organisé par groupe fonctionnel commenté, plus lisible que l'ordre
alphabétique strict).
