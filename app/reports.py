from pathlib import Path

import pandas as pd
from openpyxl.styles import Font
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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


def build_summary(results: list[MatchResult], unmatched_receipts: list[Comprobante]) -> dict:
    conciliados = sum(r.estado == "CONCILIADO" for r in results)
    revisar = sum(r.estado == "REVISAR" for r in results)
    sin_comprobante = sum(r.estado == "SIN_COMPROBANTE" for r in results)
    recibidas = sum(float(r.movimiento.importe) for r in results if r.movimiento.tipo == "credito")
    emitidas = sum(float(r.movimiento.importe) for r in results if r.movimiento.tipo == "debito")
    return {
        "movimientos": len(results),
        "conciliados": conciliados,
        "revisar": revisar,
        "sin_comprobante": sin_comprobante,
        "comprobantes_sin_movimiento": len(unmatched_receipts),
        "total_recibido": recibidas,
        "total_emitido": emitidas,
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
    totals = build_summary(results, unmatched_receipts)

    summary = pd.DataFrame(
        [
            {"metrica": "Movimientos analizados", "valor": totals["movimientos"]},
            {"metrica": "Conciliados automáticamente", "valor": totals["conciliados"]},
            {"metrica": "Requieren revisión", "valor": totals["revisar"]},
            {"metrica": "Movimientos sin comprobante", "valor": totals["sin_comprobante"]},
            {"metrica": "Comprobantes sin movimiento", "valor": totals["comprobantes_sin_movimiento"]},
            {"metrica": "Total recibido", "valor": totals["total_recibido"]},
            {"metrica": "Total emitido", "valor": totals["total_emitido"]},
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


def _money(value: float) -> str:
    return "$ {:,.2f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")


def generate_pdf(
    output_path: str | Path,
    results: list[MatchResult],
    unmatched_receipts: list[Comprobante],
    period_label: str = "Cierre mensual",
) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    totals = build_summary(results, unmatched_receipts)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCenter",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        leading=22,
        spaceAfter=8,
    )
    small = ParagraphStyle("Small", parent=styles["BodyText"], fontSize=8, leading=10)

    doc = SimpleDocTemplate(
        str(output),
        pagesize=landscape(A4),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )
    story = [
        Paragraph("Informe de conciliación bancaria", title_style),
        Paragraph(period_label, styles["Heading2"]),
        Spacer(1, 4 * mm),
    ]

    summary_data = [
        ["Movimientos", "Conciliados", "A revisar", "Sin comprobante", "Recibido", "Emitido"],
        [
            totals["movimientos"],
            totals["conciliados"],
            totals["revisar"],
            totals["sin_comprobante"],
            _money(totals["total_recibido"]),
            _money(totals["total_emitido"]),
        ],
    ]
    summary_table = Table(summary_data, repeatRows=1, hAlign="LEFT")
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAEAEA")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDBDBD")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend([summary_table, Spacer(1, 6 * mm)])

    rows = [["Fecha", "Tipo", "Descripción / contraparte", "Importe", "Estado", "Comprobante", "Motivo"]]
    for result in results:
        c = result.comprobante
        rows.append(
            [
                result.movimiento.fecha.strftime("%d/%m/%Y"),
                "Recibida" if result.movimiento.tipo == "credito" else "Emitida",
                Paragraph((c.contraparte if c else result.movimiento.descripcion) or "-", small),
                _money(float(result.movimiento.importe)),
                Paragraph(result.estado.replace("_", " "), small),
                c.id if c else "-",
                Paragraph("; ".join(result.motivos) or "-", small),
            ]
        )

    detail = Table(rows, repeatRows=1, colWidths=[25*mm, 22*mm, 58*mm, 28*mm, 34*mm, 28*mm, 63*mm])
    detail.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAEAEA")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CFCFCF")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (3, 1), (3, -1), "RIGHT"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(detail)

    if unmatched_receipts:
        story.extend([Spacer(1, 6 * mm), Paragraph("Comprobantes sin movimiento bancario", styles["Heading2"])])
        pending_rows = [["ID", "Fecha", "Tipo", "Contraparte", "Importe"]]
        for c in unmatched_receipts:
            pending_rows.append([c.id, c.fecha.strftime("%d/%m/%Y"), c.tipo, c.contraparte, _money(float(c.importe))])
        pending_table = Table(pending_rows, repeatRows=1, hAlign="LEFT")
        pending_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAEAEA")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CFCFCF")),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(pending_table)

    doc.build(story)
    return output
