import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/network/dio_client.dart';
import '../../../core/storage/secure_storage.dart';
import '../data/profil_candidat_repository_impl.dart';
import '../domain/profil_candidat.dart';
import '../domain/profil_candidat_repository.dart';

part 'profil_candidat_providers.g.dart';

@riverpod
ProfilCandidatRepository profilCandidatRepository(Ref ref) {
  return ProfilCandidatRepositoryImpl(
      ref.watch(dioProvider), ref.watch(secureStorageProvider));
}

@riverpod
class ProfilCandidatNotifier extends _$ProfilCandidatNotifier {
  @override
  Future<ProfilCandidat> build() {
    return ref.watch(profilCandidatRepositoryProvider).obtenir();
  }

  Future<void> mettreAJour({
    String? email,
    bool? notificationsSms,
    bool? notificationsPush,
    bool? notificationsEmail,
  }) async {
    final profil = await ref.read(profilCandidatRepositoryProvider).mettreAJour(
          email: email,
          notificationsSms: notificationsSms,
          notificationsPush: notificationsPush,
          notificationsEmail: notificationsEmail,
        );
    state = AsyncValue.data(profil);
  }
}
