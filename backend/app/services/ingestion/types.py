from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any


def valeur_json_safe(valeur: Any) -> Any:
    """Rend une valeur extraite d'Excel/PDF (date, Decimal, ...) sérialisable en JSON."""
    if isinstance(valeur, datetime | date):
        return valeur.isoformat()
    if isinstance(valeur, Decimal):
        return float(valeur)
    return valeur


@dataclass
class LigneExtraite:
    ligne: int
    donnees: dict[str, Any]
    brut: dict[str, Any]
    erreurs: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ligne": self.ligne,
            "donnees": self.donnees,
            "brut": self.brut,
            "erreurs": self.erreurs,
        }


@dataclass
class ResultatExtraction:
    lignes: list[LigneExtraite]
    erreurs_fichier: list[str] = field(default_factory=list)

    @property
    def nombre_lignes(self) -> int:
        return len(self.lignes)

    @property
    def nombre_erreurs(self) -> int:
        return sum(1 for ligne in self.lignes if ligne.erreurs)
