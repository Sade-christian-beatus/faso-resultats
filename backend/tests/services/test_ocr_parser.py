from app.services.ingestion.ocr_parser import lignes_depuis_texte


def test_lignes_depuis_texte_extrait_colonnes_separees_par_espaces() -> None:
    texte = (
        "Numero PV  Jury  Nom  Prenom  Decision\n"
        "001  Ouaga 1  Traore  Awa  Admis\n"
        "002  Ouaga 1  Kabore  Issa  Ajourne\n"
    )

    resultat = lignes_depuis_texte(texte)

    assert resultat.nombre_lignes == 2
    assert resultat.lignes[0].donnees["numero_pv"] == "001"
    assert resultat.lignes[0].donnees["decision"] == "ADMIS"


def test_lignes_depuis_texte_vide_renvoie_erreur_fichier() -> None:
    resultat = lignes_depuis_texte("   \n\n  ")

    assert resultat.lignes == []
    assert resultat.erreurs_fichier == ["Aucun texte détecté par l'OCR"]


def test_lignes_depuis_texte_ignore_les_titres_avant_entete() -> None:
    """Calibrage OCR (2026-07-04) : les documents officiels ont presque toujours un
    titre au-dessus de l'en-tête du tableau (ex. "ASSISTANTS DES DOUANES/HOMMES",
    "ADMISSIBLES") — l'en-tête n'est donc pas forcément la première ligne de texte."""
    texte = (
        "ASSISTANTS DES DOUANES/HOMMES\n"
        "ADMISSIBLES\n"
        "Numero PV  Jury  Nom  Prenom  Decision\n"
        "001  Ouaga 1  Traore  Awa  Admis\n"
    )

    resultat = lignes_depuis_texte(texte)

    assert resultat.nombre_lignes == 1
    assert resultat.lignes[0].donnees["numero_pv"] == "001"
    assert resultat.lignes[0].donnees["nom"] == "Traore"
