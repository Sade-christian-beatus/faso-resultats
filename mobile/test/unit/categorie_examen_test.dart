import 'package:faso_resultats_mobile/config/constants.dart';
import 'package:faso_resultats_mobile/config/routes.dart';
import 'package:faso_resultats_mobile/features/accueil/presentation/navigation_principale.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/categorie_examen.dart';
import 'package:faso_resultats_mobile/features/consultation_rapide/domain/examen.dart';
import 'package:flutter_test/flutter_test.dart';

Examen _examen(String type) => Examen(
    id: type,
    administrationId: 'a',
    typeExamen: type,
    annee: 2026,
    libelle: type);

void main() {
  group('CategorieExamen', () {
    test('regroupe les types comme la page web', () {
      expect(
          CategorieExamen.de(_examen('BAC_GENERAL')), CategorieExamen.examens);
      expect(CategorieExamen.de(_examen('CD_CATEGORIE_B')),
          CategorieExamen.concours);
      expect(CategorieExamen.de(_examen('CONCOURS_PROFESSIONNEL')),
          CategorieExamen.fonctionPublique);
      expect(CategorieExamen.de(_examen('GENDARMERIE')),
          CategorieExamen.paramilitaires);
      expect(CategorieExamen.de(_examen('AUTRE')), CategorieExamen.autres);
    });

    test('un type inconnu tombe dans « Autres » sans planter', () {
      expect(
          CategorieExamen.de(_examen('NOUVEAU_TYPE')), CategorieExamen.autres);
    });

    test('aucun type n’appartient à deux catégories', () {
      final vus = <String>{};
      for (final categorie in CategorieExamen.values) {
        for (final type in categorie.types) {
          expect(vus.add(type), isTrue, reason: type);
        }
      }
    });

    test('parCode retrouve la catégorie, null si inconnu', () {
      expect(CategorieExamen.parCode('PARAMILITAIRES'),
          CategorieExamen.paramilitaires);
      expect(CategorieExamen.parCode('UNIVERSITES'), isNull);
      expect(CategorieExamen.parCode(null), isNull);
    });

    test('libellé court des types', () {
      expect(libelleTypeExamen('BAC'), 'BAC');
      expect(libelleTypeExamen('EAUX_FORETS'), 'Eaux et forêts');
    });
  });

  group('AppRoutes.consultationFiltree', () {
    test('sans filtre : la recherche simple', () {
      expect(AppRoutes.consultationFiltree(), '/consultation-rapide');
    });

    test('avec catégorie ou examen', () {
      expect(AppRoutes.consultationFiltree(categorie: CategorieExamen.concours),
          '/consultation-rapide?categorie=CONCOURS');
      expect(AppRoutes.consultationFiltree(examenId: 'abc'),
          '/consultation-rapide?examen=abc');
    });
  });

  group('NavigationPrincipale.indexPour', () {
    test('associe chaque chemin à son onglet', () {
      expect(NavigationPrincipale.indexPour(AppRoutes.accueil), 0);
      expect(NavigationPrincipale.indexPour('/consultation-rapide'), 1);
      expect(NavigationPrincipale.indexPour(AppRoutes.dashboard), 2);
      // Notifications lives under /profil but is its own tab.
      expect(NavigationPrincipale.indexPour(AppRoutes.notifications), 3);
      expect(NavigationPrincipale.indexPour(AppRoutes.profil), 4);
    });
  });

  group('ContactSupport', () {
    test('formate les numéros par paires', () {
      expect(ContactSupport.formater('56121818'), '56 12 18 18');
    });

    test('appel avec l’indicatif du Burkina Faso', () {
      expect(
          ContactSupport.uriAppel('62291818').toString(), 'tel:+22662291818');
    });
  });
}
