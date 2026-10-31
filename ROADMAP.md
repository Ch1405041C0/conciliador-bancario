# Roadmap orientado a automatización

## Fase 1 — MVP

- [x] Importar comprobantes validados.
- [x] Importar extracto CSV/XLSX.
- [x] Matching automático por reglas.
- [x] Separar conciliados de excepciones.
- [x] Generar informe Excel.
- [x] Mantener link al comprobante.

## Fase 2 — Integración con la app de Julieta

- [ ] Guardar comprobantes y metadatos en base de datos.
- [ ] Ejecutar conciliación desde un botón “Cerrar mes”.
- [ ] Pantalla que muestre sólo excepciones.
- [ ] Confirmar/corregir un match sugerido.
- [ ] Reprocesar automáticamente después de corregir.

## Fase 3 — Automatización documental

- [ ] Google Drive API.
- [ ] Crear carpetas por año/mes/tipo.
- [ ] Renombrar comprobantes.
- [ ] Guardar el link en la base.
- [ ] Detectar duplicados por hash + referencia + importe.

## Fase 4 — Extractos reales

- [ ] Adaptadores por banco.
- [ ] CSV/XLSX nativos primero.
- [ ] PDF sólo donde sea necesario.
- [ ] Registro de formato/banco detectado.

## Fase 5 — Matching avanzado

- [ ] Alias de contrapartes.
- [ ] Matching por CBU/CVU/CUIT cuando esté disponible.
- [ ] Agrupaciones 1:N y N:1.
- [ ] Reglas aprendidas de correcciones anteriores.
- [ ] Score explicable y auditable.

## Regla de UX

Si el sistema está seguro, no preguntar.

Si no está seguro, mostrar sólo:
- movimiento,
- candidato sugerido,
- motivo de la duda,
- acciones “Confirmar / Cambiar / Sin comprobante”.
