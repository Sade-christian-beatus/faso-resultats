// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'droits_candidat_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$droitsCandidatHash() => r'274dcc41c8c82b85cba5c664330d7ab542f431b7';

/// `GET /api/v1/public/droits-candidat` : endpoint public simple, sans
/// réutilisation ailleurs dans l'app — pas de repository dédié pour un seul
/// GET en lecture seule (pas de sur-abstraction).
///
/// Copied from [droitsCandidat].
@ProviderFor(droitsCandidat)
final droitsCandidatProvider =
    AutoDisposeFutureProvider<DroitsCandidat>.internal(
  droitsCandidat,
  name: r'droitsCandidatProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$droitsCandidatHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef DroitsCandidatRef = AutoDisposeFutureProviderRef<DroitsCandidat>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
