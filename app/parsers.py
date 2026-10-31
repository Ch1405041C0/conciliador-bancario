from pathlib import Path

import pandas as pd

from .models import Comprobante, Movimiento
from .normalization import (
    normalize_movement_type,
    normalize_receipt_type,
    parse_amount,
)


def _read_table(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError(f"formato no soportado: {suffix}. Usar CSV o XLSX")


def load_comprobantes(path: str | Path) -> list[Comprobante]:
    df = _read_table(path).fillna("")
    required = {"id", "fecha", "tipo", "importe", "contraparte"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"faltan columnas en comprobantes: {sorted(missing)}")

    result: list[Comprobante] = []
    for _, row in df.iterrows():
        result.append(
            Comprobante(
                id=str(row["id"]),
                fecha=pd.to_datetime(row["fecha"]).date(),
                tipo=normalize_receipt_type(row["tipo"]),
                importe=parse_amount(row["importe"]),
                contraparte=str(row["contraparte"]),
                referencia=str(row.get("referencia", "")),
                link_comprobante=str(row.get("link_comprobante", "")),
            )
        )
    return result


def load_movimientos(path: str | Path) -> list[Movimiento]:
    df = _read_table(path).fillna("")
    required = {"id", "fecha", "tipo", "importe", "descripcion"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"faltan columnas en extracto: {sorted(missing)}")

    result: list[Movimiento] = []
    for _, row in df.iterrows():
        result.append(
            Movimiento(
                id=str(row["id"]),
                fecha=pd.to_datetime(row["fecha"]).date(),
                tipo=normalize_movement_type(row["tipo"]),
                importe=parse_amount(row["importe"]),
                descripcion=str(row["descripcion"]),
                referencia=str(row.get("referencia", "")),
            )
        )
    return result
