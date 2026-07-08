import 'package:dio/dio.dart';
import 'package:dio_cache_interceptor/dio_cache_interceptor.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../config/constants.dart';
import '../../config/env.dart';
import '../storage/secure_storage.dart';
import 'http_cache.dart';
import 'interceptors/auth_interceptor.dart';
import 'interceptors/retry_interceptor.dart';
import 'session_expiree.dart';

/// Client HTTP unique de l'application. `onNonAutorise` est branché depuis
/// `app.dart` pour forcer une déconnexion sur 401 sans que cette couche
/// réseau ne connaisse la navigation.
Dio creerDioClient(
  SecureStorage secureStorage,
  CacheStore cacheStore, {
  Future<void> Function()? onNonAutorise,
}) {
  final dio = Dio(
    BaseOptions(
      baseUrl: EnvConfig.apiBaseUrl,
      connectTimeout: AppDurations.timeoutReseau,
      receiveTimeout: AppDurations.timeoutReseau,
    ),
  );

  dio.interceptors.addAll([
    DioCacheInterceptor(options: cacheOptionsParDefaut(cacheStore)),
    AuthInterceptor(secureStorage, onNonAutorise: onNonAutorise),
    RetryInterceptor(dio),
    if (kDebugMode)
      LogInterceptor(logPrint: (objet) => debugPrint(objet.toString())),
  ]);

  return dio;
}

final dioProvider = Provider<Dio>((ref) {
  return creerDioClient(
    ref.watch(secureStorageProvider),
    ref.watch(cacheStoreProvider),
    onNonAutorise: () async {
      ref.read(sessionExpireeProvider.notifier).state = true;
    },
  );
});
