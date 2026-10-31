from app.matching import reconcile
from app.parsers import load_comprobantes, load_movimientos
from app.reports import build_summary, generate_excel, generate_pdf


def test_summary_and_reports(tmp_path):
    movimientos = load_movimientos("ejemplos/extracto.csv")
    comprobantes = load_comprobantes("ejemplos/comprobantes.csv")
    results, unmatched = reconcile(movimientos, comprobantes)

    summary = build_summary(results, unmatched)
    assert summary["movimientos"] == 4
    assert summary["conciliados"] == 3
    assert summary["sin_comprobante"] == 1
    assert summary["comprobantes_sin_movimiento"] == 1

    xlsx = generate_excel(tmp_path / "informe.xlsx", results, unmatched)
    pdf = generate_pdf(tmp_path / "informe.pdf", results, unmatched, "Demo")

    assert xlsx.exists() and xlsx.stat().st_size > 0
    assert pdf.exists() and pdf.stat().st_size > 0
