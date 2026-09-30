import 'examen.dart';

/// Home page shortcuts grouping `TypeExamen` values (backend
/// app/models/examen.py). Same grouping as the web home page
/// (frontend/public/js/public.js, `CATEGORIES`), so both channels speak the
/// same language. "Universités" from the blueprint is out of scope
/// (decision of 2026-07-03).
enum CategorieExamen {
  examens(
    code: 'EXAMENS',
    titre: 'Examens',
    types: {
      'CEP',
      'BEPC',
      'BEP',
      'CAP',
      'BAC',
      'BAC_GENERAL',
      'BAC_TECHNOLOGIQUE',
      'BAC_PROFESSIONNEL',
      'CQP',
      'BQP',
      'BPT',
    },
  ),
  concours(
    code: 'CONCOURS',
    titre: 'Concours',
    types: {
      'CONCOURS_DIRECT',
      'CD_CATEGORIE_A',
      'CD_CATEGORIE_B',
      'CD_CATEGORIE_C',
      'CD_CATEGORIE_D',
    },
  ),
  fonctionPublique(
    code: 'FONCTION_PUBLIQUE',
    titre: 'Fonction publique',
    types: {'CONCOURS_PROFESSIONNEL'},
  ),
  paramilitaires(
    code: 'PARAMILITAIRES',
    titre: 'Paramilitaires',
    types: {
      'ARMEE',
      'POLICE',
      'DOUANES',
      'GENDARMERIE',
      'EAUX_FORETS',
      'SECURITE_PENITENTIAIRE',
    },
  ),
  autres(code: 'AUTRES', titre: 'Autres', types: {'AUTRE'});

  const CategorieExamen({
    required this.code,
    required this.titre,
    required this.types,
  });

  /// Value used in URLs (`/consultation-rapide?categorie=EXAMENS`).
  final String code;
  final String titre;
  final Set<String> types;

  bool contient(Examen examen) => types.contains(examen.typeExamen);

  static CategorieExamen de(Examen examen) => CategorieExamen.values
      .firstWhere((c) => c.contient(examen), orElse: () => autres);

  static CategorieExamen? parCode(String? code) {
    for (final categorie in CategorieExamen.values) {
      if (categorie.code == code) return categorie;
    }
    return null;
  }
}

/// Short display label of an exam type ("BAC", "Concours direct cat. B"...).
String libelleTypeExamen(String typeExamen) =>
    _libellesTypeExamen[typeExamen] ?? typeExamen;

const _libellesTypeExamen = {
  'BAC_GENERAL': 'BAC général',
  'BAC_TECHNOLOGIQUE': 'BAC technologique',
  'BAC_PROFESSIONNEL': 'BAC professionnel',
  'CONCOURS_DIRECT': 'Concours direct',
  'CD_CATEGORIE_A': 'Concours direct cat. A',
  'CD_CATEGORIE_B': 'Concours direct cat. B',
  'CD_CATEGORIE_C': 'Concours direct cat. C',
  'CD_CATEGORIE_D': 'Concours direct cat. D',
  'CONCOURS_PROFESSIONNEL': 'Concours professionnel',
  'ARMEE': 'Armée',
  'POLICE': 'Police',
  'DOUANES': 'Douanes',
  'GENDARMERIE': 'Gendarmerie',
  'EAUX_FORETS': 'Eaux et forêts',
  'SECURITE_PENITENTIAIRE': 'Sécurité pénitentiaire',
  'AUTRE': 'Autre',
};
