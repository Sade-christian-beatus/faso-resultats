import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/network/dio_client.dart';
import '../../../core/storage/secure_storage.dart';
import '../data/auth_candidat_repository_impl.dart';
import '../domain/auth_candidat_repository.dart';
import '../domain/session_candidat.dart';

part 'auth_candidat_providers.g.dart';

@riverpod
AuthCandidatRepository authCandidatRepository(Ref ref) {
  return AuthCandidatRepositoryImpl(
      ref.watch(dioProvider), ref.watch(secureStorageProvider));
}

/// Envoi du code OTP, que ce soit pour une inscription ou une connexion —
/// même état partagé puisque l'écran de saisie du code qui suit est
/// identique dans les deux cas.
@riverpod
class OtpEnvoi extends _$OtpEnvoi {
  @override
  AsyncValue<String?>? build() => null;

  Future<void> inscrire({
    required String numeroCnib,
    required String nomComplet,
    required DateTime dateNaissance,
    required String telephone,
    required String consentementApdpVersion,
  }) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(
      () => ref.read(authCandidatRepositoryProvider).inscrire(
            numeroCnib: numeroCnib,
            nomComplet: nomComplet,
            dateNaissance: dateNaissance,
            telephone: telephone,
            consentementApdpVersion: consentementApdpVersion,
          ),
    );
  }

  Future<void> demanderConnexion(String telephone) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(
      () =>
          ref.read(authCandidatRepositoryProvider).demanderConnexion(telephone),
    );
  }

  void reinitialiser() => state = null;
}

@riverpod
class OtpValidation extends _$OtpValidation {
  @override
  AsyncValue<SessionCandidat>? build() => null;

  Future<void> valider(
      {required String telephone, required String code}) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(
      () => ref
          .read(authCandidatRepositoryProvider)
          .validerOtp(telephone: telephone, code: code),
    );
  }

  void reinitialiser() => state = null;
}
