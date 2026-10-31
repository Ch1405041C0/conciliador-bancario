from pathlib import Path

import pandas as pd
from openpyxl.styles import Font

from .models import Comprobante, MatchResult


def _result_row(result: MatchResult) -> dict:
    c = result.comprobante
    return {
        "movimiento_id": result.movimiento.id,
        "fecha_extracto": result.movimiento.fecha.isoformat(),
        "tipo_extracto": result.movimiento.tipo,
        "importe": float(result.movimiento.importe),
        "descripcion": result.movimiento.descripcion,
        "referencia_extracto": result.movimiento.referencia,
        "estado": result.estado,
        "score": result.score,
        "comprobante_id": c.id if c else "",
        "fecha_comprobante": c.fecha.isoformat() if c else "",
        "contraparte": c.contraparte if c else "",
        "referencia_comprobante": c.referencia if c else "",
        "link_comprobante": c.link_comprobante if c else "",
        "motivos": "; ".join(result.motivos),
    }


def _receipt_row(c: Comprobante) -> dict:
    return {
        "comprobante_id": c.id,
        "fecha": c.fecha.isoformat(),
        "tipo": c.tipo,
        "importe": float(c.importe),
        "contraparte": c.contraparte,
        "referencia": c.referencia,
        "link_comprobante": c.link_comprobante,
    }


def generate_excel(
    output_path: str | Path,
    results: list[MatchResult],
    unmatched_receipts: list[Comprobante],
) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    all_rows = [_result_row(r) for r in results]
    reconciled = [row for row in all_rows if row["estado"] == "CONCILIADO"]
    exceptions = [row for row in all_rows if row["estado"] != "CONCILIADO"]

    summary = pd.DataFrame(
        [
            {"metrica": "Movimientos analizados", "valor": len(results)},
            {"metrica": "Conciliados automáticamente", "valor": len(reconciled)},
            {"metrica": "Requieren revisión", "valor": sum(r["estado"] == "REVISAR" for r in all_rows)},
            {"metrica": "Movimientos sin comprobante", "valor": sum(r["estado"] == "SIN_COMPROBANTE" for r in all_rows)},
            {"metrica": "Comprobantes sin movimiento", "valor": len(unmatched_receipts)},
        ]
    )

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Resumen", index=False)
        pd.DataFrame(reconciled).to_excel(writer, sheet_name="Conciliados", index=False)
        pd.DataFrame(exceptions).to_excel(writer, sheet_name="Excepciones", index=False)
        pd.DataFrame([_receipt_row(c) for c in unmatched_receipts]).to_excel(
            writer, sheet_name="Comprobantes_sin_mov", index=False
        )

        for ws in writer.book.worksheets:
            for cell in ws[1]:
                cell.font = Font(bold=True)
            ws.freeze_panes = "A2"
            for column_cells in ws.columns:
                width = min(max(len(str(cell.value or "")) for cell in column_cells) + 2, 55)
                ws.column_dimensions[column_cells[0].column_letter].width = width

    return output
