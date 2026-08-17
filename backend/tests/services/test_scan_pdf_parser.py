from PIL import Image, ImageDraw, ImageFont

from app.services.parsers.scan_pdf_parser import parser_pdf_scan

_FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 20)
_FONT_GRAS = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 20)


def _construire_pdf_scan(
    chemin, titre_lignes: list[str], lignes_resultats: list[str], pied: str
) -> None:
    """Reconstitue un communiqué Fonction publique scanné : image rendue puis
    enregistrée en PDF sans couche texte (comme un vrai scan)."""
    toutes_lignes = (
        [(True, ligne) for ligne in titre_lignes]
        + [("", "")]
        + [(False, ligne) for ligne in lignes_resultats]
        + [("", ""), (False, pied)]
    )

    largeur, hauteur = 1400, 80 + 35 * len(toutes_lignes)
    image = Image.new("RGB", (largeur, hauteur), "white")
    dessin = ImageDraw.Draw(image)
    y = 20
    for est_titre, texte in toutes_lignes:
        police = _FONT_GRAS if est_titre is True else _FONT
        if est_titre is True:
            largeur_texte = dessin.textlength(texte, font=police)
            dessin.text(((largeur - largeur_texte) / 2, y), texte, font=police, fill="black")
        else:
            dessin.text((30, y), texte, font=police, fill="black")
        y += 35
    image.save(str(chemin), "PDF")


def test_parser_pdf_scan_extrait_les_resultats(tmp_path) -> None:
    chemin = tmp_path / "communique.pdf"
    _construire_pdf_scan(
        chemin,
        ["CHIRURGIENS-DENTISTES GENERALISTES", "ADMISSIBLES"],
        [
            "1° KONATE BEN OUMAR STANISLAS KONABE 000015-120-03 B18622704 03/12/97",
            "2° TRAORE AWA 000042-120-03 B19876543 15/05/98",
        ],
        "Arrete la presente liste a 2 admissibles.",
    )

    resultat = parser_pdf_scan(str(chemin))

    assert resultat.erreurs_fichier == []
    assert len(resultat.lignes) == 2
    premiere = resultat.lignes[0].donnees
    assert premiere["numero_pv"] == "000015"
    assert premiere["numero_recepisse"] == "000015"
    assert premiere["code_concours"] == "120"
    assert premiere["code_centre"] == "03"
    assert premiere["jury"] == "03"
    assert premiere["rang_numerique"] == 1
    assert premiere["rang_affiche"] == "1°"
    assert premiere["nom"] == "KONATE BEN OUMAR STANISLAS KONABE"
    assert premiere["numero_cnib"] == "B18622704"
    assert premiere["date_naissance"] == "1997-12-03"
    assert premiere["decision"] == "ADMISSIBLE"
    assert "prenom manquant" in resultat.lignes[0].erreurs


def test_parser_pdf_scan_gere_les_ex_aequo(tmp_path) -> None:
    chemin = tmp_path / "communique.pdf"
    _construire_pdf_scan(
        chemin,
        ["ADMISSIBLES"],
        [
            "4° OUEDRAOGO ISSA 000058-120-03 B12345678 21/09/99",
            "4° SANOU RICHARD 000061-120-03 B23456789 09/01/00",
        ],
        "Arrete la presente liste a 2 admissibles.",
    )

    resultat = parser_pdf_scan(str(chemin))

    assert [ligne.donnees["rang_numerique"] for ligne in resultat.lignes] == [4, 4]
    assert [ligne.donnees["rang_affiche"] for ligne in resultat.lignes] == ["4°", "4°"]


def test_parser_pdf_scan_signale_un_ecart_avec_le_nombre_declare(tmp_path) -> None:
    chemin = tmp_path / "communique.pdf"
    _construire_pdf_scan(
        chemin,
        ["ADMISSIBLES"],
        ["1° TRAORE AWA 000042-120-03 B19876543 15/05/98"],
        "Arrete la presente liste a 5 admissibles.",
    )

    resultat = parser_pdf_scan(str(chemin))

    assert len(resultat.lignes) == 1
    assert any("Écart détecté" in erreur for erreur in resultat.erreurs_fichier)


def test_parser_pdf_scan_utilise_la_decision_par_defaut_si_phase_indetectable(tmp_path) -> None:
    chemin = tmp_path / "communique.pdf"
    _construire_pdf_scan(
        chemin,
        [],
        ["1° TRAORE AWA 000042-120-03 B19876543 15/05/98"],
        "Fin de liste. Total : 1.",
    )

    resultat = parser_pdf_scan(str(chemin), decision_par_defaut="ADMIS")

    assert resultat.lignes[0].donnees["decision"] == "ADMIS"


def test_parser_pdf_scan_liste_non_admis_nest_pas_confondue_avec_admis(tmp_path) -> None:
    """Régression (audit 2026-08-17) : "NON ADMIS" contient le mot "ADMIS" — la
    détection de décision ne doit pas retenir la forme positive quand le titre du
    communiqué est en réalité une négation."""
    chemin = tmp_path / "communique.pdf"
    _construire_pdf_scan(
        chemin,
        ["LISTE DES CANDIDATS NON ADMIS"],
        ["1° TRAORE AWA 000042-120-03 B19876543 15/05/98"],
        "Fin de liste. Total : 1.",
    )

    resultat = parser_pdf_scan(str(chemin))

    assert resultat.lignes[0].donnees["decision"] == "NON ADMIS"


def test_parser_pdf_scan_aucune_ligne_reconnue(tmp_path) -> None:
    chemin = tmp_path / "communique.pdf"
    _construire_pdf_scan(chemin, ["TITRE SANS TABLEAU"], [], "")

    resultat = parser_pdf_scan(str(chemin))

    assert resultat.lignes == []
    assert resultat.erreurs_fichier == ["Aucune ligne de résultat reconnue dans ce PDF scanné"]
