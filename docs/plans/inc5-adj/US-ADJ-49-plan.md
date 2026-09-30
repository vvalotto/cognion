# Plan de Implementación: US-ADJ-49 - Docente ve la evolución temporal de un estudiante y de su comisión

**Patrón:** clean-architecture-bc (esta US no toca capas de dominio — frontend puro)
**Producto:** analytics (frontend)

## Componentes a Implementar

### 1. Cliente API
- [x] `frontend/src/lib/analytics-api.ts`
  - Nuevas interfaces `EvolucionTemporalPuntoResponse` (`actividadId`, `tituloActividad`, `finalizadaEn`, `porcentajeAcierto`) y `EvolucionTemporalComisionPuntoResponse` (`actividadId`, `tituloActividad`, `porcentajeAciertosPromedio`)
  - `obtenerEvolucionTemporalEstudiante(materiaId, estudianteId, signal?)` sobre `GET /analytics/materias/{id}/estudiantes/{id}/evolucion-temporal`
  - `obtenerEvolucionTemporalComision(materiaId, comisionId, signal?)` sobre `GET /analytics/materias/{id}/comisiones/{id}/evolucion-temporal`

### 2. Pantalla nueva — gráfico de evolución temporal
- [x] `frontend/src/pages/analytics/EvolucionTemporal.tsx`
  - Lee `materiaId`/`comisionId`/`estudianteId` de `useParams`
  - `Promise.all([obtenerEvolucionTemporalEstudiante, obtenerEvolucionTemporalComision])`
  - Eje X = unión de `tituloActividad` de ambas series en orden cronológico (por `finalizada_en` de la serie individual cuando esté, si no por el orden que ya trae el backend — ambos endpoints devuelven orden cronológico real, `US-ADJ-45`); cada serie dibuja solo sus propios puntos, sin interpolar huecos
  - SVG hecho a mano (sin librería, mismo criterio de la spec): eje Y fijo 0–100%, polyline azul sólida (estudiante), polyline punteada verde (comisión); un solo punto (sin `<polyline>`) si la serie tiene 1 elemento
  - Leyenda con color + nombre de cada serie
  - Estado vacío: ninguna serie con datos → mensaje, sin ejes
  - Breadcrumb de 4 niveles: "Analytics › Desempeño por comisión › Detalle del estudiante › Evolución temporal"

### 3. Integración desde el drill-down de `US-ADJ-48`
- [x] `frontend/src/pages/analytics/DesempenoPorComisionDetalleEstudiante.tsx`
  - Agrega un link/botón "Ver evolución temporal" hacia la ruta nueva (no toca `DesempenoResumenDetalle.tsx`, que es compartido con `US-4.1.3`/`US-4.2.5` — el link vive en la página wrapper, no en el componente compartido)

### 4. Integración de rutas
- [x] `frontend/src/router.tsx`
  - `/analytics/desempeno-por-comision/materias/:materiaId/comisiones/:comisionId/estudiantes/:estudianteId/evolucion` → `RequireRole rol="docente"` → `EvolucionTemporal`
  - Sin entrada en `AppNav.tsx` (solo alcanzable desde el drill-down, según la spec)

**Estado:** ✅ COMPLETADO — 4/4 tareas completadas
**Fecha completado:** 2026-09-14
**Tiempo real:** tracking de Fases 0, 2-5, 7-9. Detalle completo en
`docs/reports/inc5-adj/US-ADJ-49-report.md`.
