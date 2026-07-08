// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'auth_candidat_providers.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$authCandidatRepositoryHash() =>
    r'ab5f92004d857826eb3b5f1b9cb17d68c4da4344';

/// See also [authCandidatRepository].
@ProviderFor(authCandidatRepository)
final authCandidatRepositoryProvider =
    AutoDisposeProvider<AuthCandidatRepository>.internal(
  authCandidatRepository,
  name: r'authCandidatRepositoryProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$authCandidatRepositoryHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef AuthCandidatRepositoryRef
    = AutoDisposeProviderRef<AuthCandidatRepository>;
String _$otpEnvoiHash() => r'b37305e43fefa968b5a0bf72d43b788abf91f46a';

/// Envoi du code OTP, que ce soit pour une inscription ou une connexion —
/// même état partagé puisque l'écran de saisie du code qui suit est
/// identique dans les deux cas.
///
/// Copied from [OtpEnvoi].
@ProviderFor(OtpEnvoi)
final otpEnvoiProvider =
    AutoDisposeNotifierProvider<OtpEnvoi, AsyncValue<String?>?>.internal(
  OtpEnvoi.new,
  name: r'otpEnvoiProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$otpEnvoiHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

typedef _$OtpEnvoi = AutoDisposeNotifier<AsyncValue<String?>?>;
String _$otpValidationHash() => r'f714a658b3a7afb47fc2ae6f91a4bc4fae25b60e';

/// See also [OtpValidation].
@ProviderFor(OtpValidation)
final otpValidationProvider = AutoDisposeNotifierProvider<OtpValidation,
    AsyncValue<SessionCandidat>?>.internal(
  OtpValidation.new,
  name: r'otpValidationProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$otpValidationHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

typedef _$OtpValidation = AutoDisposeNotifier<AsyncValue<SessionCandidat>?>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
