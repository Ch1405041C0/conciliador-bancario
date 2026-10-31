import argparse

from .matching import reconcile
from .parsers import load_comprobantes, load_movimientos
from .reports import generate_excel


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Conciliación automática de extractos y comprobantes"
    )
    parser.add_argument("--extracto", required=True, help="CSV/XLSX del extracto bancario")
    parser.add_argument("--comprobantes", required=True, help="CSV/XLSX de comprobantes")
    parser.add_argument("--salida", default="salida/informe_conciliacion.xlsx")
    args = parser.parse_args()

    movimientos = load_movimientos(args.extracto)
    comprobantes = load_comprobantes(args.comprobantes)
    results, unmatched = reconcile(movimientos, comprobantes)
    output = generate_excel(args.salida, results, unmatched)

    auto = sum(r.estado == "CONCILIADO" for r in results)
    review = sum(r.estado == "REVISAR" for r in results)
    missing = sum(r.estado == "SIN_COMPROBANTE" for r in results)

    print(f"Movimientos analizados: {len(results)}")
    print(f"Conciliados automáticamente: {auto}")
    print(f"Requieren revisión: {review}")
    print(f"Sin comprobante: {missing}")
    print(f"Comprobantes sin movimiento: {len(unmatched)}")
    print(f"Informe generado: {output}")


if __name__ == "__main__":
    main()
