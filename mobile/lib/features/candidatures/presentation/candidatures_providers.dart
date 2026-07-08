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
