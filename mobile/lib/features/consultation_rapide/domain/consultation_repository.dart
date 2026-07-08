import 'administration.dart';
import 'examen.dart';
import 'resultat.dart';

/// Contrat implémenté par la couche data — permet de mocker entièrement
/// l'accès réseau dans les tests de la couche presentation.
abstract class ConsultationRepository {
  Future<List<Administration>> listerAdministrations();

  Future<List<Examen>> listerExamens();

  Future<List<Resultat>> rechercherResultats({
    required String examenId,
    required String numeroPv,
    String? jury,
  });
}
