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

Génération de code (`@riverpod`, `riverpod_generator`) utilisée dès le jour 2
plutôt que la syntaxe classique `Provider((ref) => ...)`, conformément aux
dépendances listées dans le prompt d'origine. **Les fichiers `*.g.dart`
générés sont committés** (pas dans `.gitignore`) — évite d'imposer une étape
`build_runner` à chaque `git clone`/CI simplement pour analyser ou tester le
code. Contrepartie assumée : après avoir modifié un provider annoté
`@riverpod`, il faut relancer `dart run build_runner build
--delete-conflicting-outputs` avant de committer, sans quoi le fichier généré
reste silencieusement désynchronisé (aucune erreur immédiate, seulement un
comportement runtime incohérent). Solo dev sur ce projet — risque jugé
acceptable ; à reconsidérer si l'équipe grandit.

**mockito n'est pas utilisé** : la version compatible avec l'analyzer actuel
(`>=5.5.1`) exige `build ^3.0.0`, qui entre en conflit avec `riverpod_generator`
2.x (`build ^2.0.0`) — les deux builders ne peuvent pas cohabiter dans le même
`build_runner`. Les repositories ont peu de méthodes ; les tests utilisent des
implémentations factices écrites à la main (`class _FakeXxxRepository
implements XxxRepository`) plutôt que des mocks générés — voir
`test/widget/consultation_rapide_screen_test.dart` pour un exemple. À
reconsidérer si le nombre de dépendances à mocker grandit significativement.

## Navigation : go_router

Choisi plutôt qu'`auto_route` : déclaratif, sans étape de génération de code
obligatoire pour les routes simples de cette app (peu d'écrans imbriqués,
peu de routes typées complexes). `auto_route` apporterait des routes
typées via `build_runner`, utile sur de très grosses apps multi-équipes —
gain marginal ici pour un coût de complexité réel.

## Réseau : Dio + intercepteurs

Un seul client Dio (`lib/core/network/dio_client.dart`), avec :

- `DioCacheInterceptor` (jour 9, `lib/core/network/http_cache.dart`) : policy
  globale par défaut `CachePolicy.noCache` — n'agit que si un appel précise
  explicitement des `CacheOptions` sur sa propre requête. Choix volontaire :
  jamais de cache implicite sur un endpoint authentifié (dashboard, profil,
  export), qui contiendrait des données personnelles. Seuls
  `listerAdministrations`/`listerExamens` (`forceCache`, 1h,
  `cacheOptionsListes`) et `rechercherResultats` (`forceCache`, 24h,
  `cacheOptionsResultats`, conforme au prompt § 9) l'utilisent, via
  `MemCacheStore` (en mémoire — perdu au redémarrage de l'app ; pas de store
  disque type `dio_cache_interceptor_hive_store` pour éviter une dépendance
  supplémentaire pour ce besoin). Le backend ne pose aucun en-tête
  `Cache-Control` (cache serveur Redis interne, invisible en HTTP), d'où
  `forceCache` plutôt que `request` : sans ça, l'intercepteur ne mettrait
  jamais rien en cache faute de directives serveur à respecter.
  `hitCacheOnErrorExcept: []` sert la version en cache dès qu'une requête
  échoue (y compris hors ligne) plutôt que de propager l'erreur.
- `AuthInterceptor` : ajoute le token de session à chaque requête, notifie un
  callback sur 401 (la couche réseau ne navigue jamais elle-même — séparation
  stricte avec la couche presentation).
- `RetryInterceptor` : une seule nouvelle tentative sur erreur réseau
  transitoire (timeout, connexion perdue) — pertinent en 3G instable, jamais
  sur une erreur serveur reçue (4xx/5xx).
- `LogInterceptor` (uniquement en `kDebugMode`) : jamais de logs réseau en
  release, conforme à l'exigence « pas de logs de données sensibles ».

## Connectivité et bandeau hors ligne (jour 9)

`lib/core/network/connectivity_provider.dart` expose `enLigneProvider`
(`Stream<bool>`, via `connectivity_plus`) — détecte l'interface réseau
disponible (wifi/données/aucune), pas la joignabilité réelle d'internet
(une sonde active serait une sur-ingénierie pour un simple bandeau
d'information, CLAUDE.md). `app.dart` l'observe via `MaterialApp.builder`
pour afficher un bandeau « Vous êtes hors ligne » au-dessus de tous les
écrans sans dupliquer cette logique dans chacun d'eux. Combiné aux messages
d'erreur déjà en place (`ReseauException`, message générique dès jour 1),
ce bandeau couvre l'exigence « message clair si action nécessitant internet
en hors ligne » sans mécanisme supplémentaire.

**Gap de test connu (jour 9)** : `_AvecBandeauHorsLigne` (dans `app.dart`)
n'a pas de test dédié — `Connectivity()` de `connectivity_plus` n'est pas
injectable sans un wrapper d'interface dédié, qu'il n'a pas semblé
justifié de construire seulement pour ce test avant le jour 10 (tests et
polissage), où l'ensemble de la couverture sera revu.

## Erreurs : exceptions typées, propagées telles quelles jusqu'à la presentation

Pas de type `Either`/`Result` générique (pas de dépendance `dartz`/`fpdart`) :
un simple `try/catch` par repository suffit à ce volume de code. Les
repositories lèvent des exceptions typées (`ServerException`,
`ReseauException`, `AuthentificationException`, `CacheException` — voir
`lib/core/errors/exceptions.dart`), toutes porteuses d'un message déjà en
français, prêt à afficher. Les notifiers Riverpod codegen les laissent
remonter sans les intercepter : elles arrivent telles quelles dans
`AsyncValue.error`, que la presentation lit via l'interface commune
`AppException` (`erreur is AppException ? erreur.message : '...'`).

*(Correction jour 5 : les 4 exceptions implémentaient initialement
`Exception` seul, et un sealed class `Failure` distinct — jamais réellement
levé par aucun repository — servait de test dans 6 écrans. Le test
`is Failure` était donc toujours faux et chaque écran retombait sur son
message générique de repli, y compris pour des erreurs réseau où le message
réel était plus informatif. `Failure`/`failures.dart` supprimés, remplacés
par l'interface `AppException` réellement implémentée par les exceptions
levées.)*

## Stockage

- `flutter_secure_storage` : uniquement le token de session candidat
  (Keystore Android / Keychain iOS).
- `shared_preferences` : préférences non sensibles uniquement (langue,
  version + horodatage du bandeau d'information de première ouverture —
  jour 8, `PrefsStorage.enregistrerConsentement`).

## Contenus légaux : rendus dans l'app, jamais liés vers une URL externe

`Politique de confidentialité` et `Conditions d'utilisation` (jour 8) sont
du texte statique dans l'app plutôt qu'un `url_launcher` vers une page web :
aucune page publique n'est encore déployée pour ces documents. Lier vers une
URL inexistante induirait l'utilisateur en erreur — même raisonnement que
pour l'écran de consultation SMS gated (jour 7). Le contenu de la politique
de confidentialité est un résumé en langage clair de
`docs/APDP_PROFIL_CANDIDAT.md`, qui reste la source de référence technique
à maintenir à jour en premier.

## Lint : very_good_analysis

Quatre règles désactivées explicitement dans `analysis_options.yaml`, avec
justification en commentaire : `always_use_package_imports` (imports
relatifs idiomatiques en Flutter), `lines_longer_than_80_chars` et
`require_trailing_commas` (les deux entrent en conflit direct avec le
comportement par défaut de `dart format`), `sort_pub_dependencies`
(pubspec organisé par groupe fonctionnel commenté, plus lisible que l'ordre
alphabétique strict).
