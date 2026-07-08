import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../config/constants.dart';
import '../../../core/network/dio_client.dart';

part 'droits_candidat_provider.g.dart';

class DroitsCandidat {
  const DroitsCandidat({required this.contactDpo, required this.droits});

  final String contactDpo;
  final List<String> droits;
}

/// `GET /api/v1/public/droits-candidat` : endpoint public simple, sans
/// réutilisation ailleurs dans l'app — pas de repository dédié pour un seul
/// GET en lecture seule (pas de sur-abstraction).
@riverpod
Future<DroitsCandidat> droitsCandidat(Ref ref) async {
  final reponse = await ref
      .watch(dioProvider)
      .get<Map<String, dynamic>>(ApiPaths.publicDroitsCandidat);
  final data = reponse.data!;
  return DroitsCandidat(
    contactDpo: data['contact_dpo'] as String,
    droits: (data['droits'] as List<dynamic>).cast<String>(),
  );
}
