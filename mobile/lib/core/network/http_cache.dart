import 'package:dio_cache_interceptor/dio_cache_interceptor.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../config/constants.dart';

/// Cache HTTP en mémoire (jour 9), pour les listes stables (administrations,
/// examens) et les résultats déjà consultés. `MemCacheStore` plutôt qu'un
/// store persistant sur disque (ex. `dio_cache_interceptor_hive_store`) :
/// pas de nouvelle dépendance pour ce besoin, au prix de perdre le cache au
/// redémarrage de l'app — limite documentée, voir mobile/docs/ARCHITECTURE.md.
final cacheStoreProvider = Provider<CacheStore>((ref) => MemCacheStore());

/// Politique par défaut de l'intercepteur global : aucun cache automatique.
/// Chaque endpoint qui veut être mis en cache le demande explicitement via
/// [cacheOptionsListes]/[cacheOptionsResultats] sur sa propre requête —
/// jamais par défaut, pour ne jamais mettre en cache une réponse contenant
/// des données personnelles (dashboard, profil, export candidat...).
CacheOptions cacheOptionsParDefaut(CacheStore store) => CacheOptions(
      store: store,
      policy: CachePolicy.noCache,
    );

/// Listes publiques stables (administrations, examens). Le backend ne pose
/// aucun en-tête `Cache-Control` (le cache serveur, Redis, est interne et
/// invisible côté HTTP) : `forceCache` met en cache malgré cette absence, et
/// `hitCacheOnErrorExcept: []` sert la version en cache si l'appareil est
/// hors ligne plutôt que d'afficher une erreur.
CacheOptions cacheOptionsListes(CacheStore store) => CacheOptions(
      store: store,
      policy: CachePolicy.forceCache,
      hitCacheOnErrorExcept: const [],
      maxStale: const Duration(hours: 1),
    );

/// Résultat déjà consulté : conservé 24h (prompt § 9, `AppDurations.cacheResultats`).
CacheOptions cacheOptionsResultats(CacheStore store) => CacheOptions(
      store: store,
      policy: CachePolicy.forceCache,
      hitCacheOnErrorExcept: const [],
      maxStale: AppDurations.cacheResultats,
    );
