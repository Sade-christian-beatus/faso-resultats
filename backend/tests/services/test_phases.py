"""Phased publication rules (app/services/phases.py) — no database."""

import pytest

from app.models import Examen, PhasePublication, Resultat
from app.services.phases import (
    ErreurPhase,
    SituationCandidat,
    StatutPhase,
    construire_parcours,
    decision_negative,
    phase_par_defaut,
    phase_suivante_attendue,
    verifier_cloturable,
    verifier_phase_ouverte,
)

SPORT = PhasePublication.EPREUVES_SPORTIVES
ADMISSIBILITE = PhasePublication.ADMISSIBILITE
ADMISSION = PhasePublication.ADMISSION_DEFINITIVE


def _concours(cloturees: list[PhasePublication] = ()) -> Examen:
    return Examen(
        phases_publication=[SPORT.value, ADMISSIBILITE.value, ADMISSION.value],
        phases_cloturees=[p.value for p in cloturees],
    )


def _resultat(phase: PhasePublication, decision: str = "APTE") -> Resultat:
    return Resultat(numero_pv="001", jury="A", phase=phase, decision=decision)


@pytest.mark.parametrize(
    "decision", ["NON ADMIS", "NON ADMISSIBLE", "AJOURNÉ", "AJOURNE", "INAPTE", "ÉLIMINÉ"]
)
def test_decisions_negatives(decision: str) -> None:
    assert decision_negative(decision)


@pytest.mark.parametrize("decision", ["ADMIS", "ADMISSIBLE", "APTE", "ADMIS (NON BOURSIER)"])
def test_decisions_positives(decision: str) -> None:
    assert not decision_negative(decision)


def test_phase_suivante_attendue_seulement_si_le_candidat_continue() -> None:
    examen = _concours()
    assert phase_suivante_attendue(examen, SPORT, "APTE") == ADMISSIBILITE
    assert phase_suivante_attendue(examen, SPORT, "INAPTE") is None
    assert phase_suivante_attendue(examen, ADMISSION, "ADMIS") is None


def test_examen_sans_phase_declaree_a_une_phase_unique() -> None:
    examen = Examen(phases_publication=[], phases_cloturees=[])
    assert phase_par_defaut(examen) == PhasePublication.RESULTAT_UNIQUE
    assert phase_suivante_attendue(examen, PhasePublication.RESULTAT_UNIQUE, "ADMIS") is None
    assert phase_par_defaut(_concours()) is None  # multi-phase: the admin must choose


def test_ordre_des_phases_impose() -> None:
    verifier_phase_ouverte(_concours(), SPORT)
    with pytest.raises(ErreurPhase, match="EPREUVES_SPORTIVES doit être clôturée"):
        verifier_phase_ouverte(_concours(), ADMISSIBILITE)
    verifier_phase_ouverte(_concours(cloturees=[SPORT]), ADMISSIBILITE)


def test_phase_cloturee_ou_non_prevue_refusee() -> None:
    with pytest.raises(ErreurPhase, match="déjà clôturée"):
        verifier_phase_ouverte(_concours(cloturees=[SPORT]), SPORT)
    with pytest.raises(ErreurPhase, match="n'est pas prévue"):
        verifier_phase_ouverte(_concours(), PhasePublication.SECOND_TOUR)


def test_cloture_exige_une_liste_publiee_et_aucune_en_attente() -> None:
    with pytest.raises(ErreurPhase, match="Aucune liste"):
        verifier_cloturable(
            _concours(), SPORT, nombre_listes_publiees=0, nombre_listes_en_attente=0
        )
    with pytest.raises(ErreurPhase, match="en attente de validation"):
        verifier_cloturable(
            _concours(), SPORT, nombre_listes_publiees=2, nombre_listes_en_attente=1
        )
    verifier_cloturable(_concours(), SPORT, nombre_listes_publiees=2, nombre_listes_en_attente=0)


def _situations(examen: Examen, resultats: list[Resultat], avec_listes: set) -> list:
    return [
        (e.statut_phase, e.situation) for e in construire_parcours(examen, resultats, avec_listes)
    ]


def test_parcours_phase_suivante_pas_encore_publiee() -> None:
    assert _situations(_concours(), [_resultat(SPORT)], {SPORT}) == [
        (StatutPhase.EN_COURS, SituationCandidat.RESULTAT),
        (StatutPhase.A_VENIR, SituationCandidat.A_VENIR),
        (StatutPhase.A_VENIR, SituationCandidat.A_VENIR),
    ]


def test_parcours_absent_d_une_phase_en_cours_n_est_jamais_declare_non_retenu() -> None:
    # Phase 2 lists are arriving centre by centre: absent so far means "wait".
    situations = _situations(
        _concours(cloturees=[SPORT]), [_resultat(SPORT)], {SPORT, ADMISSIBILITE}
    )
    assert situations[1] == (StatutPhase.EN_COURS, SituationCandidat.EN_ATTENTE)


def test_parcours_absent_d_une_phase_cloturee() -> None:
    assert _situations(
        _concours(cloturees=[SPORT, ADMISSIBILITE]), [_resultat(SPORT)], {SPORT, ADMISSIBILITE}
    ) == [
        (StatutPhase.CLOTUREE, SituationCandidat.RESULTAT),
        (StatutPhase.CLOTUREE, SituationCandidat.NE_FIGURE_PAS),
        (StatutPhase.A_VENIR, SituationCandidat.NON_CONCERNE),
    ]


def test_parcours_decision_negative_arrete_le_parcours() -> None:
    situations = _situations(
        _concours(cloturees=[SPORT]), [_resultat(SPORT, "INAPTE")], {SPORT, ADMISSIBILITE}
    )
    assert [s for _, s in situations] == [
        SituationCandidat.RESULTAT,
        SituationCandidat.NON_CONCERNE,
        SituationCandidat.NON_CONCERNE,
    ]


def test_parcours_complet() -> None:
    resultats = [
        _resultat(SPORT),
        _resultat(ADMISSIBILITE, "ADMISSIBLE"),
        _resultat(ADMISSION, "ADMIS"),
    ]
    situations = _situations(
        _concours(cloturees=[SPORT, ADMISSIBILITE]), resultats, {SPORT, ADMISSIBILITE, ADMISSION}
    )
    assert [s for _, s in situations] == [SituationCandidat.RESULTAT] * 3
