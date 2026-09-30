import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'config/routes.dart';
import 'config/theme.dart';
import 'core/network/connectivity_provider.dart';
import 'core/network/session_expiree.dart';

/// Material/Cupertino/widgets strings in French. Required as soon as the
/// locale is 'fr': Flutter only bundles English by default, and widgets such
/// as the date picker or the navigation bar crash without them.
const localisationsApp = GlobalMaterialLocalizations.delegates;

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
      localizationsDelegates: localisationsApp,
      builder: (context, child) => _AvecBandeauHorsLigne(child: child),
    );
  }
}

/// Bandeau discret « Vous êtes hors ligne » (jour 9), affiché au-dessus de
/// tous les écrans via `MaterialApp.builder` plutôt que dans chaque route
/// individuellement.
class _AvecBandeauHorsLigne extends ConsumerWidget {
  const _AvecBandeauHorsLigne({required this.child});

  final Widget? child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Optimiste (true) tant que le premier événement de connectivité n'est
    // pas encore arrivé, pour ne pas afficher le bandeau par défaut.
    final enLigne = ref.watch(enLigneProvider).valueOrNull ?? true;

    return Column(
      children: [
        if (!enLigne)
          Container(
            width: double.infinity,
            color: AppColors.erreur,
            padding: const EdgeInsets.symmetric(vertical: 6),
            child: const SafeArea(
              bottom: false,
              child: Text(
                'Vous êtes hors ligne',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        Expanded(child: child ?? const SizedBox.shrink()),
      ],
    );
  }
}
