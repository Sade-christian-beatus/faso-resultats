import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'config/routes.dart';
import 'config/theme.dart';

class FasoResultatsApp extends ConsumerWidget {
  const FasoResultatsApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

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
