# Plan de Implementación — US-8.6.3

## Tareas
1. Redactar `docs/plans/DESPLIEGUE-GCP.md`: pasos con comandos, resultado esperado, criterio de éxito y puerta de confirmación; quién hace
   cada cosa; control de costos; desmontaje; qué hacer si algo falla.
2. Ajustar `.github/workflows/imagen-smoke.yml` para que, además de verificar, **exporte la imagen como artefacto** (`docker save` + `upload-artifact`,
   retención de 1 día). Es la forma de llevar la imagen a la VM sin registro ni costo en esta prueba; el registro definitivo se decide en `US-8.6.4`.
3. Verificar el cambio de CI (el workflow corre al hacer push; debe seguir en verde y publicar el artefacto).
4. **Revisión del plan con Víctor** (Fase 8). No se ejecuta nada hasta su aprobación.
5. Tras la aprobación: **ejecución manual** del plan con bitácora (`quality/reports/uat/inc8-gcp/bitacora-despliegue.md`).
6. Cierre: reporte, ajustes a `deploy/gcp/` y lista de lo que `US-8.6.4` debe automatizar.

## Riesgos
- **Costo real:** cuenta paga sin créditos. La IPv4 pública se cobra (≈0,005 USD/hora, ~3,65 USD/mes) y las fuentes no coinciden en si la capa gratuita la cubre.
- **Memoria en 1 GB con sistema operativo y Docker:** puede no alcanzar; el plan define cuándo detenerse.
- **Imagen sin registro:** el artefacto de CI vence a las 24 h y exige descargarlo y subirlo a la VM; es una solución de prueba.
- **Resultados que invalidan el diseño:** se registran y se decide en un ADR; no se parchea en silencio.
