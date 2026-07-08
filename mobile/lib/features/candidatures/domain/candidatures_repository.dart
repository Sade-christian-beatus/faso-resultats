import 'candidature.dart';

abstract class CandidaturesRepository {
  Future<List<Candidature>> lister();

  /// Ajout d'une candidature et confirmation OTP (mécanisme 3) : jour 5.
  Future<void> retirer(String candidatureId);
}
