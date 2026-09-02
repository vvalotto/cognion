# Plan de Implementación: US-3.4.3 - Docente crea una nueva actividad de período abierto

## Información de la Historia

**US:** US-3.4.3
**Título:** Docente crea una nueva actividad de período abierto
**Prioridad:** Alta — Iteración 4, Incremento 3 (RF-11)
**Puntos:** 3
**Producto:** cognion (frontend)
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-30

---

## Resumen

**Como** Docente
**Quiero** crear una actividad de período abierto indicando ventana de disponibilidad, cantidad
de preguntas e intentos permitidos
**Para** habilitar una evaluación que mis estudiantes puedan rendir sin coordinación en vivo
(RF-11)

Frontend puro — `POST /actividades` ya existe desde `US-3.1.2`, sin cambios de backend.

---

## Componentes a Implementar

### 1. Pantalla `NuevaActividad` (React)

**Ubicación:** `frontend/src/pages/NuevaActividad.tsx`
**Patrón:** Componente de página, mismo estilo que `NuevaMateria.tsx` (form simple) y
`NuevaPreguntaOpcionMultiple.tsx` (resolución de materia por `materiaId` de la URL)

**Tareas:**
- [ ] Resolver `materia` vía `listarMaterias()` + `find(m => m.id === materiaId)` (mismo
      patrón que `Actividades.tsx`/`NuevaPreguntaOpcionMultiple.tsx`) — usa
      `materia.cantidadPreguntasActivas` para el hint de preguntas disponibles.
- [ ] Formulario con 4 campos: Apertura (`datetime-local`), Cierre (`datetime-local`),
      Cantidad de preguntas (`number`, min 1), Intentos permitidos (`number`, min 1, default 1).
      Sin campo de título — el prototipo (`#doc-nueva-actividad`) no lo incluye; la materia es
      implícita por la navegación.
- [ ] Hints estáticos: "No puede superar las N preguntas activas del banco de la materia"
      (interpola `materia.cantidadPreguntasActivas`) y "Cada estudiante recibe un set aleatorio
      distinto".
- [ ] Validación de cliente antes de enviar: `fechaApertura < fechaCierre` (INV-AE-02) e
      intentos ≥ 1 (INV-AE-03, ya cubierto por `min=1` del input pero reforzado en
      `handleSubmit` para el mensaje de error explícito del escenario BDD). Si falla, `setError`
      y `return` sin llamar a `crearActividad`.
- [ ] `handleSubmit`: llama `crearActividad({ materiaId, fechaApertura, fechaCierre,
      cantidadPreguntas, cantidadIntentosPermitidos })` (cliente ya existente en
      `actividad-evaluativa-api.ts`, `US-3.4.1`); éxito → `navigate` al listado de actividades
      de la materia (`/actividad-evaluativa/materias/${materiaId}/actividades`).
- [ ] Manejo de error 422 del backend (`PreguntasInsuficientes`, `PeriodoInvalido`,
      `CantidadIntentosInvalida`): capturar `ApiError`, mostrar `err.message` inline con el
      mismo bloque de alerta (`role="alert"`) usado en `NuevaMateria.tsx`.
- [ ] Breadcrumb: "Mis materias › {materia} › Actividades › Nueva actividad", igual criterio
      que `Actividades.tsx`.

---

### 2. Ruta en el router

**Ubicación:** `frontend/src/router.tsx`
**Patrón:** Reemplazo del placeholder existente

**Tareas:**
- [ ] Importar `NuevaActividad` y reemplazar `<ActividadEvaluativaPlaceholder />` por
      `<NuevaActividad />` en la ruta `/actividad-evaluativa/materias/:materiaId/actividades/nueva`
      (ya protegida con `RequireRole rol="docente"` desde `US-3.4.1`) — sin agregar rutas nuevas.

---

## Tests

### Tests Unitarios (Vitest + Testing Library)

- [ ] `frontend/src/pages/NuevaActividad.test.tsx`
  - Creación exitosa: completa el formulario, envía, verifica llamada a `crearActividad` con
    los datos correctos y navegación al listado.
  - Rechazo de cliente: cierre anterior a apertura → mensaje de error, `crearActividad` NO se
    llama (mock `vi.fn()` sin invocaciones).
  - Rechazo de servidor: mock de `crearActividad` rechaza con `ApiError(422, "...")` → mensaje
    inline visible, sin navegación.
  - Hint muestra `cantidadPreguntasActivas` de la materia resuelta.

**Estimación tests unitarios:** cubiertos en el mismo archivo que la implementación de la
tarea (mismo criterio que US-3.4.1/3.4.2 — no hay Fase 5 de integración backend porque no hay
cambios de backend).

---

## Validación

### Escenarios BDD
- [ ] `tests/features/inc3/US-3.4.3-nueva-actividad.feature` — 3 escenarios (ya generados en
      Fase 1), implementados como steps sobre el mismo `NuevaActividad.test.tsx` o un step file
      dedicado, según convención de BDD frontend ya usada en `US-3.4.2` (a confirmar en Fase 6
      según cómo se resolvió ahí).

### Quality Gates (frontend)
- [ ] `oxlint` 0 errores
- [ ] `tsc --noEmit` 0 errores
- [ ] Cobertura Vitest de `NuevaActividad.tsx` en línea con el resto de pantallas de creación
      (referencia: 90-100% en `NuevaMateria.tsx`/`NuevaPreguntaOpcionMultiple.tsx`)

No aplican los gates de backend (pylint/CC/MI/coverage pytest) — sin cambios en `src/`.

---

## Dependencias

**Historias bloqueantes:** ninguna — `US-3.1.2` (backend) y `US-3.4.2` (navegación de entrada)
ya están cerradas.
**Historias relacionadas:** `US-3.1.2`, `US-3.4.2`, `US-3.4.1` (infraestructura de rutas/cliente
API).
**Componentes externos:** `crearActividad()` y `listarMaterias()`, ya existentes.

---

## Checklist de Progreso

### Implementación
- [ ] `NuevaActividad.tsx` implementado
- [ ] Ruta en `router.tsx` conectada

### Testing
- [ ] Tests unitarios implementados y en verde
- [ ] Escenarios BDD implementados y en verde

### Calidad
- [ ] oxlint 0 errores
- [ ] `tsc --noEmit` 0 errores
- [ ] Cobertura aceptable en `NuevaActividad.tsx`

### Documentación
- [x] Reporte final generado (`docs/reports/inc3/US-3.4.3-report.md`)
- [x] `CLAUDE.md` actualizado al cierre
- [x] `CHANGELOG.md` actualizado

## Lecciones Aprendidas

- ✅ Al reusar `listarMaterias()` (ya expone `cantidadPreguntasActivas`) no hizo falta ningún
  endpoint ni cambio de backend para el hint de "preguntas disponibles" del prototipo.
- ✅ El prototipo (`#doc-nueva-actividad`) no incluye campo de título — se respetó tal cual,
  confiando en el fallback ya existente (`tituloDeActividad()` en `Actividades.tsx`, `US-3.4.2`)
  para las actividades creadas sin título.
