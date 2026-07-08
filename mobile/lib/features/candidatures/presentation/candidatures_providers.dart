import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/network/dio_client.dart';
import '../data/candidatures_repository_impl.dart';
import '../domain/candidature.dart';
import '../domain/candidatures_repository.dart';

part 'candidatures_providers.g.dart';

@riverpod
CandidaturesRepository candidaturesRepository(Ref ref) {
  return CandidaturesRepositoryImpl(ref.watch(dioProvider));
}

@riverpod
class Candidatures extends _$Candidatures {
  @override
  Future<List<Candidature>> build() {
    return ref.watch(candidaturesRepositoryProvider).lister();
  }

  Future<void> rafraichir() async {
    ref.invalidateSelf();
    await future;
  }

  Future<void> retirer(String candidatureId) async {
    await ref.read(candidaturesRepositoryProvider).retirer(candidatureId);
    await rafraichir();
  }
}

/// État de l'ajout d'une candidature (jour 5) : soumission puis, le cas
/// échéant, confirmation du mécanisme 3 (fallback OTP).
@riverpod
class AjoutCandidature extends _$AjoutCandidature {
  @override
  AsyncValue<Candidature>? build() => null;

  Future<void> creer({
    required String administrationId,
    required String examenId,
    required String numeroRecepisse,
  }) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(
      () => ref.read(candidaturesRepositoryProvider).creer(
            administrationId: administrationId,
            examenId: examenId,
            numeroRecepisse: numeroRecepisse,
          ),
    );
    if (state?.hasValue ?? false) {
      await ref.read(candidaturesProvider.notifier).rafraichir();
    }
  }

  Future<void> confirmerOtp(
      {required String candidatureId, required String code}) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(
      () => ref.read(candidaturesRepositoryProvider).confirmerOtp(
            candidatureId: candidatureId,
            code: code,
          ),
    );
    if (state?.hasValue ?? false) {
      await ref.read(candidaturesProvider.notifier).rafraichir();
    }
  }

  void reinitialiser() => state = null;
}
