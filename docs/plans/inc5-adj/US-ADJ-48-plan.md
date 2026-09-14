# Plan de Implementación: US-ADJ-48 - Docente ve "Desempeño por comisión" con drill-down

**Patrón:** clean-architecture-bc (esta US no toca capas de dominio — frontend puro)
**Producto:** analytics (frontend)

## Componentes a Implementar

### 1. Cliente API
- [x] `frontend/src/lib/analytics-api.ts`
  - Nueva interfaz `DesempenoComisionFilaResponse` (camelCase: `estudianteId`, `nombre`, `porcentajeAciertosAcumulado: number | null`, `actividadesPendientes: number`)
  - Nueva función `obtenerDesempenoPorComision(materiaId, comisionId, signal?)` sobre `GET /analytics/materias/{materiaId}/comisiones/{comisionId}/desempeno` (`US-ADJ-44`, ya expuesto), mapeo snake_case↔camelCase igual que las funciones existentes del archivo

### 2. Componente compartido — habilitar drill-down 2° sin romper usos existentes
- [x] `frontend/src/pages/analytics/DesempenoResumenDetalle.tsx`
  - Agrega prop opcional `onFilaClick?: (evaluacionId: string) => void` a `DesempenoResumenDetalleProps`
  - Si está presente, cada `Card` de `.eval-item` gana `onClick`/rol de botón (cursor pointer, sin cambiar el layout); si no está presente (uso actual de `MiDesempeno.tsx`/`DesempenoPorAlumno.tsx`), el comportamiento no cambia
  - Sin este componente no hay drill-down 2° — evita duplicar la lista de evaluaciones

### 3. Pantalla nueva — nivel 0 (tabla + selectores)
- [x] `frontend/src/pages/analytics/DesempenoPorComision.tsx`
  - Selectores Materia → Comisión, mismo patrón de cascada que `DesempenoPorAlumno.tsx` (`listarMaterias`, `listarComisionesPorMateria`)
  - Al elegir ambos: `obtenerDesempenoPorComision(materiaId, comisionId)` → tabla ordenable por columna (Nombre, % Aciertos, Pendientes), estado `null` de `porcentajeAciertosAcumulado` se renderiza "Sin datos" en cursiva, `actividadesPendientes > 0` resaltado en ámbar
  - Fila clicable → `navigate` a la ruta de drill-down 1° con `materiaId`/`comisionId`/`estudianteId`
  - Estado vacío: comisión sin estudiantes con evaluaciones finalizadas → tabla igual, todas las filas "Sin datos" (el backend ya devuelve `null`, no hace falta lógica de vacío especial)

### 4. Pantalla nueva — drill-down 1° (detalle de estudiante)
- [x] `frontend/src/pages/analytics/DesempenoPorComisionDetalleEstudiante.tsx`
  - Lee `materiaId`/`comisionId`/`estudianteId` de `useParams`
  - Misma lógica de datos que `DesempenoPorAlumno.tsx` (líneas 84-104): `obtenerDesempenoDeEstudiante` + `listarActividades`, `armarFilas`
  - Renderiza `DesempenoResumenDetalle` con `onFilaClick` → navega a la ruta de drill-down 2°
  - Breadcrumb: "Analytics › Desempeño por comisión › {nombre estudiante o "Detalle"}" con link de vuelta a la tabla de la comisión (`materiaId`/`comisionId` en la URL)

### 5. Componente compartido — extraer el contenido visual de revisión
- [x] `frontend/src/pages/actividad-evaluativa/RevisionEvaluacionContenido.tsx` (nuevo)
  - Extrae el JSX de estadísticas + lista de `RevisionEvaluacion.tsx` (líneas 84-107) a un componente puro `RevisionEvaluacionContenido({ revision })`, sin breadcrumb ni fetch — evita duplicar el render entre la pantalla del Estudiante y la del Docente
  - `RevisionEvaluacion.tsx` (Estudiante) pasa a usarlo, sin cambio de comportamiento visible

### 6. Pantalla nueva — drill-down 2° (revisión, acceso Docente)
- [x] `frontend/src/pages/analytics/RevisionEvaluacionDocente.tsx`
  - Lee `evaluacionId` (+ `materiaId`/`comisionId`/`estudianteId` para el breadcrumb de vuelta) de `useParams`
  - Reusa `obtenerRevision` (`@/lib/actividad-evaluativa-api`, ya público al rol docente vía guard ampliado de `US-ADJ-44`) y `RevisionEvaluacionContenido`
  - Breadcrumb: "Analytics › Desempeño por comisión › Detalle del estudiante › Revisión", con link de vuelta al detalle del estudiante

### 7. Integración de rutas y navegación
- [x] `frontend/src/router.tsx`
  - `/analytics/desempeno-por-comision` → `RequireRole rol="docente"` → `DesempenoPorComision`
  - `/analytics/desempeno-por-comision/materias/:materiaId/comisiones/:comisionId/estudiantes/:estudianteId` → `RequireRole rol="docente"` → `DesempenoPorComisionDetalleEstudiante`
  - `/analytics/desempeno-por-comision/materias/:materiaId/comisiones/:comisionId/estudiantes/:estudianteId/evaluaciones/:evaluacionId/revision` → `RequireRole rol="docente"` → `RevisionEvaluacionDocente`
- [x] `frontend/src/components/AppNav.tsx`
  - Entrada "Desempeño por comisión" en el bloque `docente`, antes de "Desempeño por alumno" (mismo orden que la candidata RF-20→21→22→23 del incremento)

**Estado:** ✅ COMPLETADO — 7/7 tareas completadas
**Fecha completado:** 2026-09-14
**Tiempo real:** tracking de Fases 0, 2-5, 7-9. Detalle completo en
`docs/reports/inc5-adj/US-ADJ-48-report.md`.
