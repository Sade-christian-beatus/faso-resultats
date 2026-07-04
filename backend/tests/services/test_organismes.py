from app.data.reference.organismes import ORGANISMES_PAR_TYPE_EXAMEN
from app.models import TypeExamen


def test_tous_les_types_examen_ont_un_organisme_de_tutelle() -> None:
    manquants = [t for t in TypeExamen if t not in ORGANISMES_PAR_TYPE_EXAMEN]

    assert manquants == []
