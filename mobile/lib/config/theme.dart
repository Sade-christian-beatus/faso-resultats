import 'package:flutter/material.dart';

/// Thème sobre mobile-first (prompt app mobile § UX) : bleu foncé en primaire,
/// jaune/orange en accent, contraste élevé pour une utilisation en plein
/// soleil fréquente au Burkina Faso.
class AppColors {
  const AppColors._();

  static const Color bleuFonce = Color(0xFF0B3D6B);
  static const Color bleuFonceClair = Color(0xFF1A5A94);
  static const Color accentOrange = Color(0xFFE8871E);
  static const Color succes = Color(0xFF1E7A3D);
  static const Color erreur = Color(0xFFC0341D);
  static const Color fond = Color(0xFFF7F8FA);
  static const Color surface = Colors.white;
  static const Color texte = Color(0xFF1A1D21);
  static const Color texteAttenue = Color(0xFF5B6572);
}

class AppTheme {
  const AppTheme._();

  static ThemeData get clair {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: AppColors.bleuFonce,
      primary: AppColors.bleuFonce,
      secondary: AppColors.accentOrange,
      error: AppColors.erreur,
      surface: AppColors.surface,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: AppColors.fond,
      textTheme: const TextTheme().apply(
        bodyColor: AppColors.texte,
        displayColor: AppColors.texte,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.bleuFonce,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: false,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.bleuFonce,
          foregroundColor: Colors.white,
          // Boutons gros et espacés (prompt § UX) : écrans tactiles imprécis
          // sur les téléphones bas de gamme.
          minimumSize: const Size.fromHeight(52),
          padding: const EdgeInsets.symmetric(horizontal: 20),
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size.fromHeight(52),
          side: const BorderSide(color: AppColors.bleuFonce, width: 1.5),
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.surface,
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFFD0D5DD)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.bleuFonce, width: 2),
        ),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        color: AppColors.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
          side: const BorderSide(color: Color(0xFFE7EAEE)),
        ),
      ),
    );
  }
}
