# Demo para mañana

## Objetivo

Mostrar una idea complementaria a la app existente, no reemplazarla.

La propuesta es automatizar el cierre mensual:

`comprobantes cargados -> extracto bancario -> matching automatico -> excepciones -> informe`

## Recorrido de 3 minutos

1. Ejecutar `run_demo.bat`.
2. Dejar marcada la opcion **Usar datos de ejemplo**.
3. Tocar **PROCESAR CIERRE MENSUAL**.
4. Mostrar los indicadores: movimientos, conciliados solos, a revisar y sin comprobante.
5. Mostrar que la tabla principal contiene solo las excepciones.
6. Generar `Informe_Contador.xlsx`.
7. Generar `Informe_Contador.pdf`.

## Pregunta clave para integrar con su aplicacion

En vez de preguntarle si quiere usar este proyecto entero, revisar juntos:

- donde guarda hoy los datos de cada comprobante;
- que datos ya extrae automaticamente;
- como identifica recibidas y emitidas;
- como guarda el link de Drive;
- que formato tiene el extracto bancario que usa;
- que columnas necesita finalmente el contador.

Con esas respuestas se puede tomar solo el motor de matching y el generador de informes.

## Principio

La persona no deberia conciliar movimiento por movimiento.

El sistema deberia resolver lo evidente y mostrar solamente lo dudoso.
