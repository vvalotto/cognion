# Plan de Implementación: US-4.1.3 - Estudiante ve la pantalla "Mi desempeño"

**Patrón:** React 19 + TypeScript + Vite (frontend puro, sin capas Clean Architecture)
**Producto:** cognion (frontend)
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-05

## Métricas de Tiempo

Tiempo real por fase (`.claude/tracking/US-4.1.3-tracking.json`) — las estimaciones humanas de
la tabla del skill no aplican a la ejecución del agente (PRIN-001, ver `skill.md`).

| Fase | Tiempo real |
|------|-------------|
| 0 — Validación de contexto | 59s |
| 1 — Escenarios BDD | 26s |
| 2 — Plan de implementación | 40s |
| 3 — Implementación (3 tareas) | 119s |
| 4 — Tests unitarios | 114s |
| 5 — Tests de integración | 22s |
| 6 — Validación BDD | 0s (mapeo directo a Vitest) |
| 7 — Quality gates | 542s (incluye detectar y corregir el ajuste de cobertura de branches, ver Lecciones Aprendidas) |
| **Total (fases 0-7)** | **~24 min** |

## Lecciones Aprendidas

- ⚠️ El umbral global de cobertura de branches (80%, `vite.config.ts`) es sensible a pantallas
  nuevas con ramas poco ejercitadas — `MiDesempeno.tsx` con 76% de cobertura de branches bajó
  el global de 80.12% a 79.97%, bloqueando la Fase 7. Se detectó comparando contra un baseline
  real (`git stash` + correr la suite completa en `develop`) en vez de asumir que el fallo era
  preexistente.
- 💡 Agregar un test que ejercite ambas ramas del comparador de orden (`sort`) y un caso donde
  el lookup `actividad_id → titulo` no encuentra match (fallback) resolvió la mayor parte del
  gap de cobertura de branches de una sola vez.
- 💡 Reutilizar `listarActividadesVisibles(materiaId)` (`US-3.4.5`) para resolver el título de
  la actividad evitó backend nuevo — mismo criterio de resolución client-side ya validado en
  `MisMaterias.tsx`/`MisActividades.tsx`.

## Decisión de Fase 2 — resolución del título de actividad

`GET /analytics/materias/{materia_id}/mi-desempeno` (`US-4.1.2`) devuelve `actividad_id` por
evaluación, pero no el título de la actividad — el prototipo (`analytics-portal-desempeno.html`
§`est-desempeno`) sí lo muestra en cada `.eval-item` (ej. "Parcial 1 — Unidades 1 a 3").
Mismo criterio que `MisMaterias.tsx`/`MisActividades.tsx` (`US-3.4.5`): sin backend nuevo,
resolver del lado del cliente. `listarActividadesVisibles(materiaId)`
(`actividad-evaluativa-api.ts`, ya existente) devuelve `id` + `titulo` de todas las actividades
visibles de la materia, incluidas las finalizadas — alcanza para armar un lookup
`actividad_id → titulo` sin pedir nada nuevo al backend.

## Componentes a Implementar

### 1. Cliente API — `frontend/src/lib/analytics-api.ts` (nuevo)
- [x] `obtenerMiDesempeno(materiaId, signal?)` sobre `apiFetch`/`ApiError`
  - `GET /analytics/materias/{materia_id}/mi-desempeno`
  - Mapea snake_case (`evaluacion_id`, `actividad_id`, `finalizada_en`,
    `cantidad_correctas`, `cantidad_incorrectas`, `total_correctas`, `total_incorrectas`,
    `porcentaje_acierto`, `cantidad_evaluaciones`) a camelCase, mismo criterio que
    `actividad-evaluativa-api.ts`/`banco-preguntas-api.ts`
  - Tipos exportados: `EvaluacionDesempenoResponse`, `ResumenDesempenoResponse`,
    `DesempenoEstudianteResponse`

### 2. Pantalla — `frontend/src/pages/analytics/MiDesempeno.tsx` (nueva)
- [x] Estructura general: `Breadcrumb` ("Analytics" › "Mi desempeño"), título, subtítulo
      (mismo patrón visual que `MisActividades.tsx`/`RevisionEvaluacion.tsx`)
- [x] Carga de materias: `listarMisMaterias()` — si el resultado tiene 1 sola materia, se
      selecciona automáticamente y **no se muestra** el `<select>`; si tiene más de 1, se
      muestra el `<select>` con la primera como default (mismo criterio de "selector oculto
      con una sola opción" que el resto del proyecto)
- [x] Al cambiar la materia seleccionada (o al montar, con la materia inicial): pide
      `obtenerMiDesempeno(materiaId)` y `listarActividadesVisibles(materiaId)` en paralelo,
      arma el lookup `actividad_id → titulo` y construye la lista de filas a renderizar
- [x] `.summary-bar`: correctas/incorrectas acumuladas, % acierto, cantidad de evaluaciones —
      solo si `evaluaciones.length > 0`
- [x] Lista de `.eval-item` por evaluación — más reciente primero (ordenar por
      `finalizadaEn` descendente, el backend no garantiza orden), título resuelto vía el
      lookup (fallback a un texto genérico si no aparece, no debería pasar en el flujo normal)
- [x] Estado vacío (`evaluaciones` vacío): mensaje "Todavía no finalizaste ninguna evaluación
      de esta materia", sin `.summary-bar` ni lista
- [x] Error de red/servidor: mensaje de error genérico (`catch` que setea un estado de error,
      distinguiendo `AbortError` real de un error de red/servidor)
- [x] Estilos `.summary-bar`/`.eval-item` con Tailwind, siguiendo la paleta del prototipo
      (verde `emerald-700` para correctas, `destructive` para incorrectas — mismo criterio ya
      usado en `RevisionEvaluacion.tsx`)

### 3. Integración — `frontend/src/router.tsx`
- [x] Import de `MiDesempeno` desde `@/pages/analytics/MiDesempeno`
- [x] Ruta nueva `/analytics/mi-desempeno`, protegida con `<RequireRole rol="estudiante">`
      (mismo bloque de rutas de estudiante, junto a `/mis-actividades/*`)

**Estado:** 3/3 tareas completadas
