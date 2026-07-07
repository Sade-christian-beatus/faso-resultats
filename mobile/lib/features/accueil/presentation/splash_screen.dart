import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../config/routes.dart';
import '../../../config/theme.dart';
import '../../../core/storage/secure_storage.dart';

/// Redirige immédiatement : déjà connecté → dashboard, sinon → accueil. Un
/// token présent en stockage sécurisé n'est pas revalidé ici (juste sa
/// présence) — une requête API invalide le forcera à se reconnecter via le
/// 401 intercepté par `AuthInterceptor`, géré à partir du jour 3.
class SplashScreen extends StatefulWidget {
  const SplashScreen({required this.secureStorage, super.key});

  final SecureStorage secureStorage;

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _rediriger();
  }

  Future<void> _rediriger() async {
    final token = await widget.secureStorage.lireToken();
    if (!mounted) return;
    context.go(token != null ? AppRoutes.dashboard : AppRoutes.accueil);
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: AppColors.bleuFonce,
      body: Center(
        child: CircularProgressIndicator(color: Colors.white),
      ),
    );
  }
}
