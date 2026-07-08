import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Basculé à `true` par `AuthInterceptor` sur un 401 — écouté au niveau de
/// l'app (voir app.dart) pour rediriger vers l'accueil et effacer l'état
/// "connecté" affiché à l'écran, sans que la couche réseau ne connaisse la
/// navigation elle-même.
final sessionExpireeProvider = StateProvider<bool>((ref) => false);
