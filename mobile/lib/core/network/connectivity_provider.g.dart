// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'connectivity_provider.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$enLigneHash() => r'758d0a1c15c9aee8eb753d72598377d4ee40a851';

/// État de connectivité réseau (jour 9), pour le bandeau « Vous êtes hors
/// ligne » global. Détecte l'interface réseau (wifi/données/aucune), pas la
/// joignabilité réelle d'internet — suffisant pour ce besoin, une sonde de
/// joignabilité serait une sur-ingénierie pour un simple bandeau
/// d'information (CLAUDE.md).
///
/// Copied from [enLigne].
@ProviderFor(enLigne)
final enLigneProvider = AutoDisposeStreamProvider<bool>.internal(
  enLigne,
  name: r'enLigneProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$enLigneHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef EnLigneRef = AutoDisposeStreamProviderRef<bool>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
