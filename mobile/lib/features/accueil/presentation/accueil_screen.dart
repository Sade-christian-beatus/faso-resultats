import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../config/constants.dart';
import '../../../config/routes.dart';
import '../../../config/theme.dart';
import '../../../core/storage/prefs_storage.dart';

/// Écran d'accueil : deux parcours possibles, sans hiérarchie imposée entre
/// les deux (prompt § 1 — un candidat peut préférer rester anonyme).
///
/// Affiche aussi, à la toute première ouverture, un bandeau d'information
/// versionné et horodaté (jour 8) — c'est le seul écran garanti d'être vu
/// avant toute création de compte candidat (le splash redirige directement
/// au dashboard si un token existe déjà).
class AccueilScreen extends ConsumerStatefulWidget {
  const AccueilScreen({super.key});

  @override
  ConsumerState<AccueilScreen> createState() => _AccueilScreenState();
}

class _AccueilScreenState extends ConsumerState<AccueilScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance
        .addPostFrameCallback((_) => _verifierConsentement());
  }

  Future<void> _verifierConsentement() async {
    final prefs = ref.read(prefsStorageProvider);
    if (prefs.versionConsentementAcceptee == AppInfo.versionConsentementApp) {
      return;
    }
    if (!mounted) return;
    await showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: const Text('Avant de continuer'),
        content: const Text(
          'Faso Résultats vous permet de consulter vos résultats sans '
          'créer de compte. Si vous créez un espace candidat, vos données '
          '(CNIB, téléphone, date de naissance) sont chiffrées et utilisées '
          'uniquement pour vérifier votre identité et vous notifier de vos '
          'résultats. Vous pouvez les consulter ou les supprimer à tout '
          'moment.',
        ),
        actions: [
          TextButton(
            onPressed: () => context.push(AppRoutes.politiqueConfidentialite),
            child: const Text('En savoir plus'),
          ),
          FilledButton(
            onPressed: () async {
              await ref
                  .read(prefsStorageProvider)
                  .enregistrerConsentement(AppInfo.versionConsentementApp);
              if (context.mounted) Navigator.of(context).pop();
            },
            child: const Text("J'ai compris"),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const _Logo(),
              const SizedBox(height: 16),
              // Wordmark (docs/CHARTE_GRAPHIQUE.md): "Faso" in midnight
              // blue + yellow star, "Résultats" in Faso green.
              const Text.rich(
                TextSpan(
                  style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
                  children: [
                    TextSpan(
                      text: 'Faso',
                      style: TextStyle(color: AppColors.bleuNuit),
                    ),
                    TextSpan(
                      text: '★ ',
                      style: TextStyle(color: AppColors.jauneFaso),
                    ),
                    TextSpan(
                      text: 'Résultats',
                      style: TextStyle(color: AppColors.vertFonce),
                    ),
                  ],
                ),
                semanticsLabel: 'Faso Résultats',
              ),
              const SizedBox(height: 6),
              const Text(
                'Vos résultats en un clic',
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w500,
                  color: AppColors.texte,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                "Consultez vos résultats d'examens et concours",
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 15, color: AppColors.texteAttenue),
              ),
              const SizedBox(height: 40),
              ElevatedButton(
                onPressed: () => context.go(AppRoutes.consultationRapide),
                child: const Text('Consulter mon résultat'),
              ),
              const SizedBox(height: 14),
              OutlinedButton(
                onPressed: () => context.go(AppRoutes.authCandidat),
                child: const Text('Créer ou accéder à mon espace candidat'),
              ),
              const SizedBox(height: 8),
              TextButton(
                onPressed: () => context.go(AppRoutes.consultationSms),
                child: const Text('Pas de connexion ? Consulter par SMS'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Logo extends StatelessWidget {
  const _Logo();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 72,
      height: 72,
      decoration: BoxDecoration(
        color: AppColors.vertFonce,
        borderRadius: BorderRadius.circular(20),
      ),
      child: const Icon(Icons.school_outlined, color: Colors.white, size: 36),
    );
  }
}
