import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/network/dio_client.dart';
import '../../../core/network/http_cache.dart';
import '../data/consultation_repository_impl.dart';
import '../domain/administration.dart';
import '../domain/consultation_repository.dart';
import '../domain/examen.dart';
import '../domain/parcours.dart';

part 'consultation_providers.g.dart';

@riverpod
ConsultationRepository consultationRepository(Ref ref) {
  return ConsultationRepositoryImpl(
      ref.watch(dioProvider), ref.watch(cacheStoreProvider));
}

@riverpod
Future<List<Administration>> administrationsPubliques(Ref ref) {
  return ref.watch(consultationRepositoryProvider).listerAdministrations();
}

@riverpod
Future<List<Examen>> examensPublics(Ref ref) {
  return ref.watch(consultationRepositoryProvider).listerExamens();
}

/// État de la recherche de résultat — un simple `AsyncValue` déclenché
/// manuellement par l'utilisateur (pas un fetch automatique au montage de
/// l'écran, contrairement aux deux providers ci-dessus).
@riverpod
class RechercheResultat extends _$RechercheResultat {
  @override
  AsyncValue<List<ParcoursCandidat>>? build() => null;

  Future<void> rechercher({
    required String examenId,
    required String numeroPv,
    String? jury,
  }) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(
      () => ref.read(consultationRepositoryProvider).rechercherParcours(
          examenId: examenId, numeroPv: numeroPv, jury: jury),
    );
  }

  void reinitialiser() => state = null;
}
