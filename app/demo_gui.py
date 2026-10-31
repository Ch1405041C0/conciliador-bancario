from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .matching import reconcile
from .parsers import load_comprobantes, load_movimientos
from .reports import build_summary, generate_excel, generate_pdf

ROOT = Path(__file__).resolve().parents[1]


class ConciliadorDemo(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Conciliador bancario - Demo")
        self.geometry("1100x700")
        self.minsize(900, 600)

        self.extracto_path = tk.StringVar()
        self.comprobantes_path = tk.StringVar()
        self.use_demo = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value="Listo para procesar")
        self.metric_mov = tk.StringVar(value="-")
        self.metric_ok = tk.StringVar(value="-")
        self.metric_review = tk.StringVar(value="-")
        self.metric_missing = tk.StringVar(value="-")
        self.results = None
        self.unmatched = None

        self._build_ui()
        self._toggle_inputs()

    def _build_ui(self) -> None:
        header = ttk.Frame(self, padding=16)
        header.pack(fill="x")
        ttk.Label(header, text="Conciliador bancario", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(
            header,
            text="Subí el extracto y los comprobantes. El sistema concilia lo claro y te muestra sólo lo que requiere revisión.",
        ).pack(anchor="w", pady=(4, 0))

        controls = ttk.LabelFrame(self, text="1. Archivos", padding=12)
        controls.pack(fill="x", padx=16, pady=(0, 10))
        ttk.Checkbutton(
            controls,
            text="Usar datos de ejemplo para la demo",
            variable=self.use_demo,
            command=self._toggle_inputs,
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        ttk.Label(controls, text="Extracto:").grid(row=1, column=0, sticky="w")
        self.extract_entry = ttk.Entry(controls, textvariable=self.extracto_path)
        self.extract_entry.grid(row=1, column=1, sticky="ew", padx=8)
        self.extract_btn = ttk.Button(controls, text="Elegir", command=self._choose_extracto)
        self.extract_btn.grid(row=1, column=2)

        ttk.Label(controls, text="Comprobantes:").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.receipt_entry = ttk.Entry(controls, textvariable=self.comprobantes_path)
        self.receipt_entry.grid(row=2, column=1, sticky="ew", padx=8, pady=(8, 0))
        self.receipt_btn = ttk.Button(controls, text="Elegir", command=self._choose_comprobantes)
        self.receipt_btn.grid(row=2, column=2, pady=(8, 0))
        controls.columnconfigure(1, weight=1)

        ttk.Button(self, text="PROCESAR CIERRE MENSUAL", command=self._process).pack(fill="x", padx=16, pady=(0, 12))

        metrics = ttk.Frame(self, padding=(16, 0))
        metrics.pack(fill="x")
        self._metric(metrics, "Movimientos", self.metric_mov, 0)
        self._metric(metrics, "Conciliados solos", self.metric_ok, 1)
        self._metric(metrics, "A revisar", self.metric_review, 2)
        self._metric(metrics, "Sin comprobante", self.metric_missing, 3)
        for i in range(4):
            metrics.columnconfigure(i, weight=1)

        table_box = ttk.LabelFrame(self, text="2. Excepciones - esto es lo único que debería revisar la persona", padding=8)
        table_box.pack(fill="both", expand=True, padx=16, pady=12)

        columns = ("fecha", "tipo", "importe", "descripcion", "estado", "score", "comprobante", "motivos")
        self.tree = ttk.Treeview(table_box, columns=columns, show="headings", height=12)
        labels = {
            "fecha": "Fecha", "tipo": "Tipo", "importe": "Importe", "descripcion": "Descripción",
            "estado": "Estado", "score": "Score", "comprobante": "Comprobante", "motivos": "Motivos"
        }
        widths = {"fecha": 90, "tipo": 80, "importe": 100, "descripcion": 220, "estado": 125, "score": 60, "comprobante": 100, "motivos": 280}
        for col in columns:
            self.tree.heading(col, text=labels[col])
            self.tree.column(col, width=widths[col], anchor="w")
        scroll = ttk.Scrollbar(table_box, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        footer = ttk.Frame(self, padding=16)
        footer.pack(fill="x")
        ttk.Button(footer, text="Generar Excel para contador", command=self._export_excel).pack(side="left")
        ttk.Button(footer, text="Generar PDF de cierre", command=self._export_pdf).pack(side="left", padx=8)
        ttk.Label(footer, textvariable=self.status).pack(side="right")

    def _metric(self, parent: ttk.Frame, title: str, variable: tk.StringVar, column: int) -> None:
        box = ttk.LabelFrame(parent, text=title, padding=10)
        box.grid(row=0, column=column, sticky="nsew", padx=4)
        ttk.Label(box, textvariable=variable, font=("Segoe UI", 18, "bold")).pack()

    def _toggle_inputs(self) -> None:
        state = "disabled" if self.use_demo.get() else "normal"
        self.extract_entry.configure(state=state)
        self.receipt_entry.configure(state=state)
        self.extract_btn.configure(state=state)
        self.receipt_btn.configure(state=state)
        if self.use_demo.get():
            self.extracto_path.set(str(ROOT / "ejemplos" / "extracto.csv"))
            self.comprobantes_path.set(str(ROOT / "ejemplos" / "comprobantes.csv"))
        else:
            self.extracto_path.set("")
            self.comprobantes_path.set("")

    def _choose_extracto(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Extractos", "*.csv *.xlsx")])
        if path:
            self.extracto_path.set(path)

    def _choose_comprobantes(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Comprobantes", "*.csv *.xlsx")])
        if path:
            self.comprobantes_path.set(path)

    def _process(self) -> None:
        try:
            movimientos = load_movimientos(self.extracto_path.get())
            comprobantes = load_comprobantes(self.comprobantes_path.get())
            self.results, self.unmatched = reconcile(movimientos, comprobantes)
            summary = build_summary(self.results, self.unmatched)
        except Exception as exc:
            messagebox.showerror("No se pudo procesar", str(exc))
            return

        self.metric_mov.set(str(summary["movimientos"]))
        self.metric_ok.set(str(summary["conciliados"]))
        self.metric_review.set(str(summary["revisar"]))
        self.metric_missing.set(str(summary["sin_comprobante"]))

        for item in self.tree.get_children():
            self.tree.delete(item)

        exceptions = [r for r in self.results if r.estado != "CONCILIADO"]
        for result in exceptions:
            c = result.comprobante
            self.tree.insert(
                "",
                "end",
                values=(
                    result.movimiento.fecha.strftime("%d/%m/%Y"),
                    "Recibida" if result.movimiento.tipo == "credito" else "Emitida",
                    f"$ {float(result.movimiento.importe):,.2f}",
                    result.movimiento.descripcion,
                    result.estado,
                    result.score,
                    c.id if c else "-",
                    "; ".join(result.motivos),
                ),
            )

        pending = summary["revisar"] + summary["sin_comprobante"]
        self.status.set(
            f"{summary['conciliados']} de {summary['movimientos']} resueltos automáticamente; {pending} requieren revisión."
        )

    def _ensure_processed(self) -> bool:
        if self.results is None or self.unmatched is None:
            messagebox.showinfo("Primero procesá", "Procesá el cierre mensual antes de generar el informe.")
            return False
        return True

    def _export_excel(self) -> None:
        if not self._ensure_processed():
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", initialfile="Informe_Contador.xlsx", filetypes=[("Excel", "*.xlsx")]
        )
        if path:
            generate_excel(path, self.results, self.unmatched)
            self.status.set(f"Excel generado: {path}")
            messagebox.showinfo("Listo", "Informe Excel generado correctamente.")

    def _export_pdf(self) -> None:
        if not self._ensure_processed():
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", initialfile="Informe_Contador.pdf", filetypes=[("PDF", "*.pdf")]
        )
        if path:
            generate_pdf(path, self.results, self.unmatched, period_label="Cierre mensual")
            self.status.set(f"PDF generado: {path}")
            messagebox.showinfo("Listo", "Informe PDF generado correctamente.")


def main() -> None:
    app = ConciliadorDemo()
    app.mainloop()


if __name__ == "__main__":
    main()
