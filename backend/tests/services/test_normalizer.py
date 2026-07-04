from app.services.ingestion.normalizer import (
    colonnes_non_reconnues,
    construire_mapping_colonnes,
    message_colonnes_non_reconnues,
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


def test_colonnes_non_reconnues_retourne_les_entetes_ignorees() -> None:
    entetes = ["N° PV", "Centre", "Nom", "Prénom", "Décision", "Colonne inconnue"]
    mapping = construire_mapping_colonnes(entetes)

    assert colonnes_non_reconnues(entetes, mapping) == ["Colonne inconnue"]


def test_colonnes_non_reconnues_ignore_les_entetes_vides() -> None:
    entetes = ["Nom", "", "Prénom"]
    mapping = construire_mapping_colonnes(entetes)

    assert colonnes_non_reconnues(entetes, mapping) == []


def test_message_colonnes_non_reconnues_liste_les_noms() -> None:
    message = message_colonnes_non_reconnues(["Adresse", "Téléphone"])

    assert "Adresse, Téléphone" in message


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


def test_mapping_colonnes_reconnait_les_en_tetes_concours_direct() -> None:
    """Calibrage sur un vrai document de concours direct (liste d'admissibilité
    Assistants des Douanes, OCECOS/AGRE) : en-têtes très différentes d'un examen
    scolaire classique."""
    mapping = construire_mapping_colonnes(
        ["N°", "NOM ET PRENOM(s)", "RECEPISSE-CODE-CENTRE", "N°CNIB", "DATE NAIS.", "CENTRE"]
    )

    assert mapping["NOM ET PRENOM(s)"] == "nom_prenom"
    assert mapping["RECEPISSE-CODE-CENTRE"] == "numero_pv"
    assert mapping["N°CNIB"] == "numero_cnib"
    assert mapping["DATE NAIS."] == "date_naissance"
    assert mapping["CENTRE"] == "jury"


def test_normaliser_ligne_colonne_nom_prenom_combinee_reste_a_corriger() -> None:
    """Import brut (pas de découpage automatique) : le nom complet va dans "nom",
    "prenom" reste vide et donc signalé en erreur pour correction manuelle."""
    mapping = construire_mapping_colonnes(["NOM ET PRENOM(s)", "RECEPISSE-CODE-CENTRE", "CENTRE"])
    ligne = {
        "NOM ET PRENOM(s)": "BAYALA JEAN-CLAUDE",
        "RECEPISSE-CODE-CENTRE": "005924-002-06",
        "CENTRE": "Koudo",
    }

    resultat = normaliser_ligne(ligne, mapping, decision_par_defaut="ADMISSIBLE")

    assert resultat.donnees["nom"] == "BAYALA JEAN-CLAUDE"
    assert resultat.donnees["prenom"] == ""
    assert "prenom manquant" in resultat.erreurs


def test_normaliser_ligne_decision_par_defaut_appliquee_si_absente() -> None:
    mapping = construire_mapping_colonnes(["numero_pv", "jury", "nom", "prenom"])
    ligne = {"numero_pv": "1", "jury": "Koudo", "nom": "N", "prenom": "P"}

    resultat = normaliser_ligne(ligne, mapping, decision_par_defaut="admissible")

    assert resultat.donnees["decision"] == "ADMISSIBLE"
    assert "decision manquant" not in resultat.erreurs


def test_normaliser_ligne_decision_par_defaut_ignoree_si_colonne_presente() -> None:
    """La décision par ligne prime toujours sur la décision par défaut du fichier."""
    mapping = construire_mapping_colonnes(["numero_pv", "jury", "nom", "prenom", "decision"])
    ligne = {"numero_pv": "1", "jury": "J", "nom": "N", "prenom": "P", "decision": "AJOURNE"}

    resultat = normaliser_ligne(ligne, mapping, decision_par_defaut="ADMISSIBLE")

    assert resultat.donnees["decision"] == "AJOURNE"
