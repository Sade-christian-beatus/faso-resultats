import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../config/routes.dart';
import '../../../config/theme.dart';

/// Écran d'accueil : deux parcours possibles, sans hiérarchie imposée entre
/// les deux (prompt § 1 — un candidat peut préférer rester anonyme).
class AccueilScreen extends StatelessWidget {
  const AccueilScreen({super.key});

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
              const Text(
                'Faso Résultats',
                style: TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.bold,
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
        color: AppColors.bleuFonce,
        borderRadius: BorderRadius.circular(20),
      ),
      child: const Icon(Icons.school_outlined, color: Colors.white, size: 36),
    );
  }
}
