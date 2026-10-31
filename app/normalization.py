import re
import unicodedata
from decimal import Decimal, InvalidOperation


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip().upper()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^A-Z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_reference(value: object) -> str:
    return re.sub(r"[^A-Z0-9]", "", normalize_text(value))


def parse_amount(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"))
    if value is None:
        raise ValueError("importe vacío")
    if isinstance(value, (int, float)):
        return Decimal(str(value)).quantize(Decimal("0.01"))

    raw = str(value).strip().replace("$", "").replace(" ", "")
    if "," in raw and "." in raw:
        # Formato AR: 1.234,56
        raw = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        raw = raw.replace(",", ".")
    try:
        return Decimal(raw).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise ValueError(f"importe inválido: {value}") from exc


def normalize_receipt_type(value: object) -> str:
    text = normalize_text(value)
    if text in {"RECIBIDA", "RECIBIDO", "INGRESO", "CREDITO"}:
        return "recibida"
    if text in {"EMITIDA", "EMITIDO", "EGRESO", "DEBITO"}:
        return "emitida"
    raise ValueError(f"tipo de comprobante inválido: {value}")


def normalize_movement_type(value: object) -> str:
    text = normalize_text(value)
    if text in {"CREDITO", "INGRESO", "RECIBIDA", "RECIBIDO"}:
        return "credito"
    if text in {"DEBITO", "EGRESO", "EMITIDA", "EMITIDO"}:
        return "debito"
    raise ValueError(f"tipo de movimiento inválido: {value}")
