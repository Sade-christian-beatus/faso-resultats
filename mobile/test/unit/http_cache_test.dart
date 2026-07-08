import 'package:dio_cache_interceptor/dio_cache_interceptor.dart';
import 'package:faso_resultats_mobile/config/constants.dart';
import 'package:faso_resultats_mobile/core/network/http_cache.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final store = MemCacheStore();

  test('cacheOptionsParDefaut ne met rien en cache automatiquement', () {
    expect(cacheOptionsParDefaut(store).policy, CachePolicy.noCache);
  });

  test(
      'cacheOptionsListes force le cache pendant 1 heure et sert le stale '
      'hors ligne', () {
    final options = cacheOptionsListes(store);
    expect(options.policy, CachePolicy.forceCache);
    expect(options.maxStale, const Duration(hours: 1));
    expect(options.hitCacheOnErrorExcept, isEmpty);
  });

  test('cacheOptionsResultats conserve 24h (AppDurations.cacheResultats)', () {
    final options = cacheOptionsResultats(store);
    expect(options.policy, CachePolicy.forceCache);
    expect(options.maxStale, AppDurations.cacheResultats);
    expect(AppDurations.cacheResultats, const Duration(hours: 24));
  });
}
