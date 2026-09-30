import 'package:flutter/material.dart';

/// Charte graphique Faso Résultats (docs/CHARTE_GRAPHIQUE.md) : vert Faso en
/// primaire, jaune en accent, bleu nuit pour le texte. Contraste élevé pour
/// une utilisation en plein soleil fréquente au Burkina Faso.
class AppColors {
  const AppColors._();

  /// Official brand green (#00A651). White text on it is below WCAG AA, so
  /// filled surfaces carrying text use [vertFonce].
  static const Color vertFaso = Color(0xFF00A651);
  static const Color vertFonce = Color(0xFF007A3D);
  static const Color rougeFaso = Color(0xFFE30613);
  static const Color jauneFaso = Color(0xFFFFD000);
  static const Color bleuNuit = Color(0xFF0B1F2D);

  /// Status colours (kept distinct from the brand palette on purpose: a
  /// "pending" badge must not look like a decorative yellow).
  static const Color avertissement = Color(0xFFB45309);
  static const Color succes = Color(0xFF007A3D);
  static const Color erreur = Color(0xFFC62828);

  static const Color fond = Color(0xFFF4F6F8);
  static const Color surface = Colors.white;
  static const Color texte = bleuNuit;
  static const Color texteAttenue = Color(0xFF5B6572);
}

class AppTheme {
  const AppTheme._();

  static ThemeData get clair {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: AppColors.vertFaso,
      primary: AppColors.vertFonce,
      secondary: AppColors.jauneFaso,
      onSecondary: AppColors.bleuNuit,
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
        backgroundColor: AppColors.vertFonce,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: false,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.vertFonce,
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
          side: const BorderSide(color: AppColors.vertFonce, width: 1.5),
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
          borderSide: const BorderSide(color: AppColors.vertFonce, width: 2),
        ),
      ),
      // Bottom navigation (5 tabs): labels kept on one line on a 360 dp
      // wide phone ("Notifications", "Mes résultats").
      navigationBarTheme: NavigationBarThemeData(
        labelTextStyle: WidgetStateProperty.resolveWith(
          (etats) => TextStyle(
            fontSize: 11,
            fontWeight: etats.contains(WidgetState.selected)
                ? FontWeight.w700
                : FontWeight.w500,
            color: etats.contains(WidgetState.selected)
                ? AppColors.vertFonce
                : AppColors.texteAttenue,
          ),
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
