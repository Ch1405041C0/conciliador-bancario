from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Comprobante:
    id: str
    fecha: date
    tipo: str
    importe: Decimal
    contraparte: str
    referencia: str = ""
    link_comprobante: str = ""


@dataclass(frozen=True)
class Movimiento:
    id: str
    fecha: date
    tipo: str
    importe: Decimal
    descripcion: str
    referencia: str = ""


@dataclass
class MatchResult:
    movimiento: Movimiento
    comprobante: Comprobante | None
    score: int
    estado: str
    motivos: list[str]
