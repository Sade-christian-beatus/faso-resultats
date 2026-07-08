import 'candidature.dart';

abstract class CandidaturesRepository {
  Future<List<Candidature>> lister();

  Future<Candidature> creer({
    required String administrationId,
    required String examenId,
    required String numeroRecepisse,
  });

  /// Mécanisme 3 (fallback OTP) : confirme la propriété du récépissé quand
  /// ni le CNIB ni la date de naissance ne figurent dans le résultat publié.
  Future<Candidature> confirmerOtp({
    required String candidatureId,
    required String code,
  });

  Future<void> retirer(String candidatureId);
}
