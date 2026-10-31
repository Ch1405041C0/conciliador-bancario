from difflib import SequenceMatcher

from .models import Comprobante, MatchResult, Movimiento
from .normalization import normalize_reference, normalize_text

AUTO_MATCH_SCORE = 75
REVIEW_SCORE = 55
AMBIGUITY_MARGIN = 8


def compatible_type(movimiento: Movimiento, comprobante: Comprobante) -> bool:
    return (
        movimiento.tipo == "credito" and comprobante.tipo == "recibida"
    ) or (
        movimiento.tipo == "debito" and comprobante.tipo == "emitida"
    )


def score_pair(movimiento: Movimiento, comprobante: Comprobante) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []

    if movimiento.importe != comprobante.importe:
        return 0, ["importe distinto"]

    score += 50
    reasons.append("importe exacto")

    if compatible_type(movimiento, comprobante):
        score += 15
        reasons.append("tipo compatible")
    else:
        return 0, ["tipo incompatible"]

    days = abs((movimiento.fecha - comprobante.fecha).days)
    if days == 0:
        score += 20
        reasons.append("fecha exacta")
    elif days == 1:
        score += 15
        reasons.append("fecha ±1 día")
    elif days <= 3:
        score += 10
        reasons.append("fecha ±3 días")
    else:
        reasons.append(f"fecha distante ({days} días)")

    mov_ref = normalize_reference(movimiento.referencia)
    comp_ref = normalize_reference(comprobante.referencia)
    if mov_ref and comp_ref and mov_ref == comp_ref:
        score += 30
        reasons.append("referencia exacta")

    description = normalize_text(movimiento.descripcion)
    counterparty = normalize_text(comprobante.contraparte)
    if description and counterparty:
        if counterparty in description:
            score += 15
            reasons.append("contraparte contenida en descripción")
        else:
            similarity = SequenceMatcher(None, description, counterparty).ratio()
            if similarity >= 0.80:
                score += 15
                reasons.append("contraparte muy similar")
            elif similarity >= 0.60:
                score += 8
                reasons.append("contraparte similar")

    return score, reasons


def reconcile(
    movimientos: list[Movimiento], comprobantes: list[Comprobante]
) -> tuple[list[MatchResult], list[Comprobante]]:
    used_receipts: set[str] = set()
    results: list[MatchResult] = []

    for movimiento in movimientos:
        candidates: list[tuple[int, Comprobante, list[str]]] = []
        for comprobante in comprobantes:
            if comprobante.id in used_receipts:
                continue
            score, reasons = score_pair(movimiento, comprobante)
            if score >= REVIEW_SCORE:
                candidates.append((score, comprobante, reasons))

        candidates.sort(key=lambda item: item[0], reverse=True)

        if not candidates:
            results.append(
                MatchResult(
                    movimiento=movimiento,
                    comprobante=None,
                    score=0,
                    estado="SIN_COMPROBANTE",
                    motivos=["sin candidato suficiente"],
                )
            )
            continue

        best_score, best_receipt, best_reasons = candidates[0]
        second_score = candidates[1][0] if len(candidates) > 1 else None

        ambiguous = (
            second_score is not None and best_score - second_score < AMBIGUITY_MARGIN
        )

        if best_score >= AUTO_MATCH_SCORE and not ambiguous:
            used_receipts.add(best_receipt.id)
            results.append(
                MatchResult(
                    movimiento=movimiento,
                    comprobante=best_receipt,
                    score=best_score,
                    estado="CONCILIADO",
                    motivos=best_reasons,
                )
            )
        else:
            reasons = list(best_reasons)
            if ambiguous:
                reasons.append("hay más de un candidato parecido")
            results.append(
                MatchResult(
                    movimiento=movimiento,
                    comprobante=best_receipt,
                    score=best_score,
                    estado="REVISAR",
                    motivos=reasons,
                )
            )

    unmatched_receipts = [c for c in comprobantes if c.id not in used_receipts]
    return results, unmatched_receipts
