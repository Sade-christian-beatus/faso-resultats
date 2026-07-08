import 'package:flutter/material.dart';

/// Bouton principal réutilisé partout — évite de dupliquer la logique de
/// chargement (spinner inline) sur chaque écran avec formulaire.
class PrimaryButton extends StatelessWidget {
  const PrimaryButton({
    required this.label,
    required this.onPressed,
    this.enCours = false,
    super.key,
  });

  final String label;
  final VoidCallback? onPressed;
  final bool enCours;

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: enCours ? null : onPressed,
      child: enCours
          ? const SizedBox(
              width: 22,
              height: 22,
              child: CircularProgressIndicator(
                strokeWidth: 2.5,
                color: Colors.white,
              ),
            )
          : Text(label),
    );
  }
}
