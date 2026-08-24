# Plan de Implementación: US-2.1.11 - Docente carga una pregunta eligiendo su tipo

**Patrón:** Frontend puro (React 19 + TypeScript + Vite) — sin capas Clean Architecture, sin cambios en `src/`
**Producto:** cognion (frontend)
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-16

## Métricas de Tiempo (fases 0-7, tracking real)

| Fase | Tiempo real |
|------|-------------|
| 0 — Validación de Contexto | 72s |
| 1 — Escenarios BDD | 337s |
| 2 — Plan de Implementación | 506s |
| 3 — Implementación | 151s |
| 4 — Tests Unitarios | 245s |
| 5 — Tests de Integración | 4s |
| 6 — Validación BDD | 5s |
| 7 — Quality Gates | 127s |
| **Total** | **~24 min** |

Nota (PRIN-001): estimaciones de duración por tarea son referencia de complejidad relativa,
no tiempo esperado de ejecución del agente.

## Nota de alcance — unidad temática como texto libre

El wireframe (`§2.5`/`§2.6`) y el prototipo HTML muestran "Unidad temática" como `<select>` con
opciones de ejemplo, pero el backend modela `unidad_tematica` como string libre (sin catálogo,
sin endpoint para listar unidades existentes de una materia) — mismo campo que ya se filtra
como texto libre en `Banco.tsx` (`US-2.1.10`). No hay endpoint de origen para poblar un
`<select>` real. Se implementa como `<input type="text">`, igual que el filtro de `Banco.tsx`
— mismo criterio de "excluir del alcance lo que no tiene endpoint" ya aplicado en `US-2.1.8`
(gap de `listarMaterias`). Si Víctor prefiere otro criterio, ajustar antes de Fase 3.

## Componentes a Implementar

### 1. Selección de tipo
- [x] `frontend/src/pages/NuevaPreguntaTipo.tsx`
  - Dos tarjetas clicables ("Opción múltiple" / "Verdadero/Falso"), navegan a
    `/materias/:materiaId/banco/preguntas/nueva/opcion-multiple` o `.../verdadero-falso`
  - Aclaración visible: el tipo no se puede cambiar después de creada la pregunta
  - Botón "Cancelar" → vuelve a `/materias/:materiaId/banco`

### 2. Formulario Opción Múltiple
- [x] `frontend/src/pages/NuevaPreguntaOpcionMultiple.tsx`
  - Campos: texto (textarea), lista de opciones (texto + radio "es correcta", mínimo 2,
    botón "+ Agregar opción", ✕ para quitar salvo que baje de 2), unidad temática (input
    texto), tema (input texto), dificultad (select Alto/Medio/Bajo), importancia (select
    Alto/Medio/Bajo)
  - Validación de cliente antes de enviar (INV-BP-02/03): mínimo 2 opciones, exactamente una
    marcada correcta — si falla, bloquea el envío con mensaje inline, no llama al backend
  - Resuelve `bancoId` vía `listarMaterias()` + `materiaId` de la URL (mismo patrón que
    `Banco.tsx`)
  - Submit → `cargarPreguntaOpcionMultiple()` (`banco-preguntas-api.ts`, ya existe desde
    `US-2.1.8`) → navega a `/materias/:materiaId/banco`
  - Botón "Cancelar" → vuelve al banco sin guardar

### 3. Formulario Verdadero/Falso
- [x] `frontend/src/pages/NuevaPreguntaVerdaderoFalso.tsx`
  - Campos: texto (textarea), selector Verdadero/Falso (dos botones tipo radio, mutuamente
    excluyentes, sin default), mismos metadatos que el formulario de Opción Múltiple
  - Submit → `cargarPreguntaVerdaderoFalso()` → navega a `/materias/:materiaId/banco`
  - Botón "Cancelar" → vuelve al banco sin guardar

### 4. Integración — router
- [x] `frontend/src/router.tsx`
  - Reemplaza `BancoPreguntasPlaceholder` por `NuevaPreguntaTipo` en
    `/materias/:materiaId/banco/preguntas/nueva`
  - Reemplaza `BancoPreguntasPlaceholder` por `NuevaPreguntaOpcionMultiple` en
    `/materias/:materiaId/banco/preguntas/nueva/opcion-multiple`
  - Reemplaza `BancoPreguntasPlaceholder` por `NuevaPreguntaVerdaderoFalso` en
    `/materias/:materiaId/banco/preguntas/nueva/verdadero-falso`
  - Las 3 rutas ya existen con guard `RequireRole rol="docente"` desde `US-2.1.8` — solo
    cambia el elemento renderizado

**Estado:** 4/4 tareas completadas
