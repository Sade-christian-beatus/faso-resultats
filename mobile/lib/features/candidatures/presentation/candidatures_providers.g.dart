// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'candidatures_providers.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$candidaturesRepositoryHash() =>
    r'3c944bda45ce193dcf42d9e4aa88e562994b08fc';

/// See also [candidaturesRepository].
@ProviderFor(candidaturesRepository)
final candidaturesRepositoryProvider =
    AutoDisposeProvider<CandidaturesRepository>.internal(
  candidaturesRepository,
  name: r'candidaturesRepositoryProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$candidaturesRepositoryHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef CandidaturesRepositoryRef
    = AutoDisposeProviderRef<CandidaturesRepository>;
String _$candidaturesHash() => r'42c194c36d478102a8bc51d994c11281fd3b843a';

/// See also [Candidatures].
@ProviderFor(Candidatures)
final candidaturesProvider =
    AutoDisposeAsyncNotifierProvider<Candidatures, List<Candidature>>.internal(
  Candidatures.new,
  name: r'candidaturesProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$candidaturesHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

typedef _$Candidatures = AutoDisposeAsyncNotifier<List<Candidature>>;
String _$ajoutCandidatureHash() => r'7fd9302d8f870b09c98c6a6b94de4d26ab7bc1cc';

/// État de l'ajout d'une candidature (jour 5) : soumission puis, le cas
/// échéant, confirmation du mécanisme 3 (fallback OTP).
///
/// Copied from [AjoutCandidature].
@ProviderFor(AjoutCandidature)
final ajoutCandidatureProvider = AutoDisposeNotifierProvider<AjoutCandidature,
    AsyncValue<Candidature>?>.internal(
  AjoutCandidature.new,
  name: r'ajoutCandidatureProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$ajoutCandidatureHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

typedef _$AjoutCandidature = AutoDisposeNotifier<AsyncValue<Candidature>?>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
