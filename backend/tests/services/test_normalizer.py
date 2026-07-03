from app.services.ingestion.normalizer import (
    construire_mapping_colonnes,
    normaliser_entete,
    normaliser_ligne,
)


def test_normaliser_entete_supprime_accents_et_ponctuation() -> None:
    assert normaliser_entete("Numéro PV") == "numero pv"
    assert normaliser_entete("Prénom") == "prenom"
    assert normaliser_entete("  Décision  ") == "decision"


def test_construire_mapping_colonnes_reconnait_les_alias() -> None:
    mapping = construire_mapping_colonnes(
        ["N° PV", "Centre", "Nom", "Prénom", "Décision", "Colonne inconnue"]
    )

    assert mapping == {
        "N° PV": "numero_pv",
        "Centre": "jury",
        "Nom": "nom",
        "Prénom": "prenom",
        "Décision": "decision",
    }


def test_normaliser_ligne_complete_sans_erreur() -> None:
    mapping = construire_mapping_colonnes(["numero_pv", "jury", "nom", "prenom", "decision"])
    ligne = {
        "numero_pv": "12345",
        "jury": "Ouagadougou 1",
        "nom": "Traore",
        "prenom": "Awa",
        "decision": "admis",
    }

    resultat = normaliser_ligne(ligne, mapping)

    assert resultat.erreurs == []
    assert resultat.donnees["decision"] == "ADMIS"


def test_normaliser_ligne_signale_champs_obligatoires_manquants() -> None:
    mapping = construire_mapping_colonnes(["numero_pv", "nom"])
    resultat = normaliser_ligne({"numero_pv": "1", "nom": ""}, mapping)

    assert "nom manquant" in resultat.erreurs
    assert "prenom manquant" in resultat.erreurs
    assert "jury manquant" in resultat.erreurs
    assert "decision manquant" in resultat.erreurs


def test_normaliser_ligne_parse_date_dd_mm_yyyy() -> None:
    mapping = construire_mapping_colonnes(
        ["numero_pv", "jury", "nom", "prenom", "decision", "date de naissance"]
    )
    ligne = {
        "numero_pv": "1",
        "jury": "J",
        "nom": "N",
        "prenom": "P",
        "decision": "ADMIS",
        "date de naissance": "12/05/2008",
    }

    resultat = normaliser_ligne(ligne, mapping)

    assert resultat.donnees["date_naissance"] == "2008-05-12"
    assert resultat.erreurs == []


def test_normaliser_ligne_signale_date_illisible() -> None:
    mapping = construire_mapping_colonnes(
        ["numero_pv", "jury", "nom", "prenom", "decision", "date de naissance"]
    )
    ligne = {
        "numero_pv": "1",
        "jury": "J",
        "nom": "N",
        "prenom": "P",
        "decision": "ADMIS",
        "date de naissance": "pas une date",
    }

    resultat = normaliser_ligne(ligne, mapping)

    assert any("date de naissance illisible" in erreur for erreur in resultat.erreurs)


def test_normaliser_ligne_parse_moyenne_avec_virgule() -> None:
    mapping = construire_mapping_colonnes(
        ["numero_pv", "jury", "nom", "prenom", "decision", "moyenne"]
    )
    ligne = {
        "numero_pv": "1",
        "jury": "J",
        "nom": "N",
        "prenom": "P",
        "decision": "ADMIS",
        "moyenne": "13,45",
    }

    resultat = normaliser_ligne(ligne, mapping)

    assert resultat.donnees["moyenne"] == 13.45
