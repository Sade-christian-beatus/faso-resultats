import 'administration.dart';
import 'examen.dart';
import 'parcours.dart';

/// Contrat implémenté par la couche data — permet de mocker entièrement
/// l'accès réseau dans les tests de la couche presentation.
abstract class ConsultationRepository {
  Future<List<Administration>> listerAdministrations();

  Future<List<Examen>> listerExamens();

  /// One [ParcoursCandidat] per candidate matching the PV number (several
  /// only when the same number exists in several juries). Empty list when
  /// nothing matches.
  Future<List<ParcoursCandidat>> rechercherParcours({
    required String examenId,
    required String numeroPv,
    String? jury,
  });
}
