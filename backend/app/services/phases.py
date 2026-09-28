"""Business rules of phased publication (docs/CONTEXTE_METIER.md § 2.4).

A concours paramilitaire is published in successive phases (sports tests, then
admissibility, then final admission), each as one or several lists. Decisions taken
with the developer (2026-09-28):
- phases are published **in order**: a phase can only receive lists once every
  previous phase is closed;
- a phase is **closed** explicitly by an admin once all its lists are published. Only
  then may the platform tell a candidate from the previous phase that they are not on
  the list — before closure, missing from a list may just mean "your centre's list is
  not published yet".

Pure functions only (no database): the routes load the data and call these.
"""

import enum
from dataclasses import dataclass

from app.models import Examen, PhasePublication, Resultat

# Decisions meaning the candidate does not move on to the next phase. Decisions are free
# text coming from official files ("ADMIS", "APTE", "NON ADMISSIBLE", "AJOURNÉ"...), so
# anything not recognised as negative is treated as moving on: at worst the candidate
# sees "next step: admissibility", never a wrong "not selected".
_PREFIXES_NEGATIFS = ("NON ", "NON-")  # "NON ADMIS", but not "ADMIS (NON BOURSIER)"
_MARQUEURS_NEGATIFS = ("AJOURN", "INAPTE", "ELIMIN", "ÉLIMIN", "ABSENT", "REFUS")


class ErreurPhase(ValueError):
    """Business rule violation; the message is shown as-is to the admin (French)."""


def phases_effectives(examen: Examen) -> list[PhasePublication]:
    """Ordered phases of the exam; an exam without declared phases has a single one."""
    if not examen.phases_publication:
        return [PhasePublication.RESULTAT_UNIQUE]
    return [PhasePublication(valeur) for valeur in examen.phases_publication]


def est_multi_phases(examen: Examen) -> bool:
    return len(phases_effectives(examen)) > 1


def phases_cloturees(examen: Examen) -> set[PhasePublication]:
    return {PhasePublication(valeur) for valeur in (examen.phases_cloturees or [])}


def phase_suivante(examen: Examen, phase: PhasePublication) -> PhasePublication | None:
    phases = phases_effectives(examen)
    index = phases.index(phase)
    return phases[index + 1] if index + 1 < len(phases) else None


def phase_precedente(examen: Examen, phase: PhasePublication) -> PhasePublication | None:
    phases = phases_effectives(examen)
    index = phases.index(phase)
    return phases[index - 1] if index > 0 else None


def decision_negative(decision: str) -> bool:
    valeur = decision.strip().upper()
    return valeur.startswith(_PREFIXES_NEGATIFS) or any(m in valeur for m in _MARQUEURS_NEGATIFS)


def phase_suivante_attendue(
    examen: Examen, phase: PhasePublication, decision: str
) -> PhasePublication | None:
    """Next step shown to a candidate on a list: none after a negative decision."""
    if decision_negative(decision):
        return None
    return phase_suivante(examen, phase)


def phase_par_defaut(examen: Examen) -> PhasePublication | None:
    """Phase used when the admin does not pick one: only unambiguous for single-phase
    exams. For a multi-phase exam the admin must say which list they are importing."""
    phases = phases_effectives(examen)
    return phases[0] if len(phases) == 1 else None


def verifier_phase_ouverte(examen: Examen, phase: PhasePublication) -> None:
    """A list can be imported/published for `phase` only if the phase belongs to the
    exam, is not closed yet, and every previous phase is closed (enforced order)."""
    phases = phases_effectives(examen)
    if phase not in phases:
        raise ErreurPhase(
            f"La phase {phase.value} n'est pas prévue pour cet examen "
            f"(phases prévues : {', '.join(p.value for p in phases)})"
        )
    cloturees = phases_cloturees(examen)
    if phase in cloturees:
        raise ErreurPhase(
            f"La phase {phase.value} est déjà clôturée : aucune nouvelle liste ne peut y "
            "être publiée"
        )
    for precedente in phases[: phases.index(phase)]:
        if precedente not in cloturees:
            raise ErreurPhase(
                f"La phase {precedente.value} doit être clôturée avant de publier des "
                f"listes pour la phase {phase.value}"
            )


def verifier_cloturable(
    examen: Examen,
    phase: PhasePublication,
    *,
    nombre_listes_publiees: int,
    nombre_listes_en_attente: int,
) -> None:
    verifier_phase_ouverte(examen, phase)
    if nombre_listes_publiees == 0:
        raise ErreurPhase(
            f"Aucune liste n'a encore été publiée pour la phase {phase.value} : "
            "impossible de la clôturer"
        )
    if nombre_listes_en_attente > 0:
        raise ErreurPhase(
            f"{nombre_listes_en_attente} liste(s) de la phase {phase.value} sont encore en "
            "attente de validation : publiez-les ou rejetez-les avant de clôturer"
        )


class StatutPhase(str, enum.Enum):
    A_VENIR = "A_VENIR"  # no list published yet
    EN_COURS = "EN_COURS"  # lists being published, the phase is not closed
    CLOTUREE = "CLOTUREE"  # all lists published


class SituationCandidat(str, enum.Enum):
    RESULTAT = "RESULTAT"  # the candidate is on a list of this phase
    EN_ATTENTE = "EN_ATTENTE"  # not on the lists published so far, phase still open
    NE_FIGURE_PAS = "NE_FIGURE_PAS"  # phase closed and the candidate is on none of its lists
    A_VENIR = "A_VENIR"  # nothing published for this phase yet
    NON_CONCERNE = "NON_CONCERNE"  # the candidate stopped at an earlier phase


@dataclass
class EtapeParcours:
    phase: PhasePublication
    statut_phase: StatutPhase
    situation: SituationCandidat
    resultat: Resultat | None


def statut_phase(
    examen: Examen, phase: PhasePublication, phases_avec_listes: set[PhasePublication]
) -> StatutPhase:
    if phase in phases_cloturees(examen):
        return StatutPhase.CLOTUREE
    if phase in phases_avec_listes:
        return StatutPhase.EN_COURS
    return StatutPhase.A_VENIR


def construire_parcours(
    examen: Examen,
    resultats_du_candidat: list[Resultat],
    phases_avec_listes: set[PhasePublication],
) -> list[EtapeParcours]:
    """One step per phase of the exam, for one candidate (PV number + jury). "Not on
    the list" is only concluded for a **closed** phase following a phase where the
    candidate moved on — never from a list still being published."""
    par_phase = {r.phase: r for r in resultats_du_candidat}
    etapes: list[EtapeParcours] = []
    en_course = False  # the candidate is on a list and was not stopped since
    arrete = False
    for phase in phases_effectives(examen):
        statut = statut_phase(examen, phase, phases_avec_listes)
        resultat = par_phase.get(phase)
        if resultat is not None:
            situation = SituationCandidat.RESULTAT
            en_course = not decision_negative(resultat.decision)
            arrete = not en_course
        elif arrete:
            situation = SituationCandidat.NON_CONCERNE
        elif statut == StatutPhase.CLOTUREE:
            # Factual: all lists of this phase are out and the candidate is on none.
            situation = SituationCandidat.NE_FIGURE_PAS
            arrete = en_course
        elif statut == StatutPhase.A_VENIR:
            situation = SituationCandidat.A_VENIR
        else:
            situation = SituationCandidat.EN_ATTENTE
        etapes.append(EtapeParcours(phase, statut, situation, resultat))
    return etapes
