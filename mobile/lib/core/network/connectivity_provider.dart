import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'connectivity_provider.g.dart';

/// État de connectivité réseau (jour 9), pour le bandeau « Vous êtes hors
/// ligne » global. Détecte l'interface réseau (wifi/données/aucune), pas la
/// joignabilité réelle d'internet — suffisant pour ce besoin, une sonde de
/// joignabilité serait une sur-ingénierie pour un simple bandeau
/// d'information (CLAUDE.md).
@riverpod
Stream<bool> enLigne(Ref ref) async* {
  final connectivity = Connectivity();
  yield _estConnecte(await connectivity.checkConnectivity());
  yield* connectivity.onConnectivityChanged.map(_estConnecte);
}

bool _estConnecte(List<ConnectivityResult> resultats) =>
    resultats.isNotEmpty && !resultats.contains(ConnectivityResult.none);
