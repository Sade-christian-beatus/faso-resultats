import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'config/routes.dart';
import 'config/theme.dart';
import 'core/network/session_expiree.dart';

class FasoResultatsApp extends ConsumerWidget {
  const FasoResultatsApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

    ref.listen(sessionExpireeProvider, (previous, expiree) {
      if (expiree) {
        ref.read(sessionExpireeProvider.notifier).state = false;
        router.go(AppRoutes.accueil);
      }
    });

    return MaterialApp.router(
      title: 'Faso Résultats',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.clair,
      routerConfig: router,
      // Français uniquement au MVP, structure i18n prête (lib/l10n) — jour 8.
      locale: const Locale('fr'),
      supportedLocales: const [Locale('fr')],
    );
  }
}
