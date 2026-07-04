"""Référentiel statique des ministères de tutelle par type d'examen — utile pour
l'affichage (ex. page publique, statistiques) sans dupliquer cette information à
chaque création d'examen. Source : docs/CONTEXTE_METIER.md § 2.

À ne pas confondre avec `Examen.ministere_tutelle` (saisi/ajusté au cas par cas à la
création d'un examen) : ce référentiel ne sert que de valeur par défaut suggérée et de
table de correspondance pour l'affichage.
"""

from app.models import TypeExamen

ORGANISMES_PAR_TYPE_EXAMEN: dict[TypeExamen, str] = {
    # Examens scolaires et universitaires (DGEC / Ministère de l'Éducation nationale),
    # sauf CEP dont la tutelle est le MEBAPLN.
    TypeExamen.CEP: "Ministère de l'Enseignement de Base, de l'Alphabétisation et de "
    "la Promotion des Langues Nationales (MEBAPLN)",
    TypeExamen.BEPC: "Direction Générale des Examens et Concours (DGEC)",
    TypeExamen.BEP: "Direction Générale des Examens et Concours (DGEC)",
    TypeExamen.CAP: "Direction Générale des Examens et Concours (DGEC)",
    TypeExamen.BAC: "Direction Générale des Examens et Concours (DGEC)",
    TypeExamen.BAC_GENERAL: "Direction Générale des Examens et Concours (DGEC)",
    TypeExamen.BAC_TECHNOLOGIQUE: "Direction Générale des Examens et Concours (DGEC)",
    TypeExamen.BAC_PROFESSIONNEL: "Direction Générale des Examens et Concours (DGEC)",
    TypeExamen.CQP: "Direction Générale des Examens et Concours (DGEC)",
    TypeExamen.BQP: "Direction Générale des Examens et Concours (DGEC)",
    TypeExamen.BPT: "Direction Générale des Examens et Concours (DGEC)",
    # Concours directs et professionnels (Fonction publique)
    TypeExamen.CONCOURS_DIRECT: "Ministère de la Fonction Publique, du Travail et de "
    "la Protection sociale",
    TypeExamen.CD_CATEGORIE_A: "Ministère de la Fonction Publique, du Travail et de "
    "la Protection sociale",
    TypeExamen.CD_CATEGORIE_B: "Ministère de la Fonction Publique, du Travail et de "
    "la Protection sociale",
    TypeExamen.CD_CATEGORIE_C: "Ministère de la Fonction Publique, du Travail et de "
    "la Protection sociale",
    TypeExamen.CD_CATEGORIE_D: "Ministère de la Fonction Publique, du Travail et de "
    "la Protection sociale",
    TypeExamen.CONCOURS_PROFESSIONNEL: "Ministère de la Fonction Publique, du Travail "
    "et de la Protection sociale",
    # Concours paramilitaires et spécifiques : tutelle double (Fonction publique +
    # ministère sectoriel), on retient ici le ministère le plus pertinent pour
    # l'affichage utilisateur.
    TypeExamen.ARMEE: "Ministère de la Défense",
    TypeExamen.GENDARMERIE: "Ministère de la Défense",
    TypeExamen.POLICE: "Ministère de la Sécurité",
    TypeExamen.DOUANES: "Ministère de la Fonction Publique / Ministère des Finances",
    TypeExamen.EAUX_FORETS: "Ministère de la Fonction Publique / Ministère de " "l'Environnement",
    TypeExamen.SECURITE_PENITENTIAIRE: "Ministère de la Fonction Publique / Ministère "
    "de la Justice",
    TypeExamen.AUTRE: "À déterminer au cas par cas",
}
