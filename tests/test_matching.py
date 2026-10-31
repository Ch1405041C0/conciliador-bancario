from datetime import date
from decimal import Decimal

from app.matching import reconcile, score_pair
from app.models import Comprobante, Movimiento


def test_exact_match_scores_high():
    movimiento = Movimiento(
        id="M1",
        fecha=date(2026, 10, 2),
        tipo="credito",
        importe=Decimal("150000.00"),
        descripcion="TRANSFERENCIA CLIENTE UNO",
        referencia="ABC123",
    )
    comprobante = Comprobante(
        id="C1",
        fecha=date(2026, 10, 2),
        tipo="recibida",
        importe=Decimal("150000.00"),
        contraparte="Cliente Uno",
        referencia="ABC123",
    )

    score, reasons = score_pair(movimiento, comprobante)

    assert score >= 100
    assert "importe exacto" in reasons
    assert "referencia exacta" in reasons


def test_wrong_amount_is_not_candidate():
    movimiento = Movimiento(
        id="M1",
        fecha=date(2026, 10, 2),
        tipo="credito",
        importe=Decimal("100.00"),
        descripcion="CLIENTE",
    )
    comprobante = Comprobante(
        id="C1",
        fecha=date(2026, 10, 2),
        tipo="recibida",
        importe=Decimal("101.00"),
        contraparte="CLIENTE",
    )

    score, _ = score_pair(movimiento, comprobante)
    assert score == 0


def test_same_receipt_cannot_be_used_twice():
    comprobante = Comprobante(
        id="C1",
        fecha=date(2026, 10, 2),
        tipo="recibida",
        importe=Decimal("100.00"),
        contraparte="Cliente Uno",
        referencia="ABC",
    )
    movimientos = [
        Movimiento("M1", date(2026, 10, 2), "credito", Decimal("100.00"), "CLIENTE UNO", "ABC"),
        Movimiento("M2", date(2026, 10, 2), "credito", Decimal("100.00"), "CLIENTE UNO", "ABC"),
    ]

    results, _ = reconcile(movimientos, [comprobante])

    assert results[0].estado == "CONCILIADO"
    assert results[1].estado == "SIN_COMPROBANTE"
