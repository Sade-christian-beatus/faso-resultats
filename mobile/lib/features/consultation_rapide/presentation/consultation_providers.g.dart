// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'consultation_providers.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$consultationRepositoryHash() =>
    r'65c0d50416bb7b1cbb68bca483b2d9ada7f83ada';

/// See also [consultationRepository].
@ProviderFor(consultationRepository)
final consultationRepositoryProvider =
    AutoDisposeProvider<ConsultationRepository>.internal(
  consultationRepository,
  name: r'consultationRepositoryProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$consultationRepositoryHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef ConsultationRepositoryRef
    = AutoDisposeProviderRef<ConsultationRepository>;
String _$administrationsPubliquesHash() =>
    r'887c8636dfe1f466d2cd783f2adb30177e54b3ac';

/// See also [administrationsPubliques].
@ProviderFor(administrationsPubliques)
final administrationsPubliquesProvider =
    AutoDisposeFutureProvider<List<Administration>>.internal(
  administrationsPubliques,
  name: r'administrationsPubliquesProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$administrationsPubliquesHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef AdministrationsPubliquesRef
    = AutoDisposeFutureProviderRef<List<Administration>>;
String _$examensPublicsHash() => r'76accebd569be0007822a30399c32cd1bc26ebe3';

/// See also [examensPublics].
@ProviderFor(examensPublics)
final examensPublicsProvider = AutoDisposeFutureProvider<List<Examen>>.internal(
  examensPublics,
  name: r'examensPublicsProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$examensPublicsHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef ExamensPublicsRef = AutoDisposeFutureProviderRef<List<Examen>>;
String _$rechercheResultatHash() => r'880577f8ab84eb525d780c8a05223773c50fe35b';

/// État de la recherche de résultat — un simple `AsyncValue` déclenché
/// manuellement par l'utilisateur (pas un fetch automatique au montage de
/// l'écran, contrairement aux deux providers ci-dessus).
///
/// Copied from [RechercheResultat].
@ProviderFor(RechercheResultat)
final rechercheResultatProvider = AutoDisposeNotifierProvider<RechercheResultat,
    AsyncValue<List<Resultat>>?>.internal(
  RechercheResultat.new,
  name: r'rechercheResultatProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$rechercheResultatHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

typedef _$RechercheResultat = AutoDisposeNotifier<AsyncValue<List<Resultat>>?>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
