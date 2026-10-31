# Conciliador bancario — MVP

Automatiza el cierre mensual entre comprobantes de transferencias y extractos bancarios.

## Objetivo

Reducir al mínimo la tarea manual:

1. Durante el mes se cargan comprobantes ya validados.
2. Al cierre se sube el extracto bancario.
3. El motor intenta vincular cada movimiento con su comprobante.
4. Los casos claros se concilian automáticamente.
5. Sólo los casos dudosos o faltantes aparecen como excepciones.
6. Se genera un Excel listo para revisar o enviar al contador.

La idea no es reemplazar un sistema contable: es eliminar trabajo repetitivo.

## Flujo ideal

`comprobantes → extracto → matching automático → excepciones → informe`

### Qué automatiza este MVP

- Normalización de fechas, importes, referencias y nombres.
- Matching por importe, tipo, cercanía de fecha, referencia y contraparte.
- Prevención de doble asignación de un mismo comprobante.
- Clasificación automática:
  - `CONCILIADO`
  - `REVISAR`
  - `SIN_COMPROBANTE`
- Detección de comprobantes que no aparecen en el extracto.
- Reporte Excel con resumen y hojas de excepciones.
- Conserva el `link_comprobante` para abrir el archivo guardado en Drive.

## Formato de comprobantes

CSV con columnas:

```csv
id,fecha,tipo,importe,contraparte,referencia,link_comprobante
C001,2026-10-02,recibida,150000,Cliente Uno,ABC123,https://drive.google.com/...
```

`tipo` puede ser:
- `recibida`
- `emitida`

## Formato de extracto

CSV o XLSX con columnas:

```csv
id,fecha,tipo,importe,descripcion,referencia
M001,2026-10-02,credito,150000,TRANSFERENCIA CLIENTE UNO,ABC123
```

`tipo` puede ser:
- `credito` / `ingreso`
- `debito` / `egreso`

## Uso

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.cli --extracto ejemplos/extracto.csv --comprobantes ejemplos/comprobantes.csv --salida salida/informe_conciliacion.xlsx
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python -m app.cli --extracto ejemplos/extracto.csv --comprobantes ejemplos/comprobantes.csv --salida salida/informe_conciliacion.xlsx
```

## Regla de matching actual

El score se arma con señales simples y auditables:

- importe exacto: +50
- tipo compatible: +15
- fecha exacta: +20
- diferencia de 1 día: +15
- diferencia de hasta 3 días: +10
- referencia exacta: +30
- nombre/descripcion parecido: hasta +15

Clasificación:

- `>= 75`: conciliación automática
- `55–74`: revisar
- `< 55`: no se asigna

Estas reglas son configurables en `app/matching.py`.

## Qué falta para integrarlo en la app real

- Leer extractos PDF de bancos específicos.
- Conectar Google Drive para mover/renombrar archivos automáticamente.
- Persistencia en base de datos.
- UI para resolver sólo las excepciones.
- Aprender aliases habituales de clientes/proveedores.
- Reconciliación parcial o agrupada (ej. una transferencia corresponde a varias facturas).

## Principio de producto

La pantalla principal no debería pedir que Julieta “haga conciliaciones”. Debería decir algo parecido a:

> 84 movimientos analizados · 76 conciliados automáticamente · 8 requieren revisión

Y mostrarle directamente esas 8 excepciones.
