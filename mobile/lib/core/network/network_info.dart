import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Détection de connectivité en temps réel (prompt § jour 9) — un simple
/// wrapper testable autour de `connectivity_plus`, pas de logique
/// supplémentaire tant que le bandeau hors-ligne n'est pas construit.
class NetworkInfo {
  NetworkInfo(this._connectivity);

  final Connectivity _connectivity;

  Future<bool> get estConnecte async {
    final resultats = await _connectivity.checkConnectivity();
    return !resultats.contains(ConnectivityResult.none);
  }

  Stream<bool> get changementsConnexion {
    return _connectivity.onConnectivityChanged.map(
      (resultats) => !resultats.contains(ConnectivityResult.none),
    );
  }
}

final networkInfoProvider = Provider<NetworkInfo>((ref) {
  return NetworkInfo(Connectivity());
});
