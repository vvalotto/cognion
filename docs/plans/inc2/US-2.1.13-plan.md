# Plan de Implementación: US-2.1.13 - Docente elimina una pregunta desde la UI, con confirmación previa

**Patrón:** React 19 + TypeScript + Vite (frontend puro, sin capas Clean Architecture)
**Producto:** frontend/banco-preguntas
**Estado:** ✅ COMPLETADO
**Tiempo real (tracker):** ~15 min efectivos

## Componentes a Implementar

### 1. Pantalla de confirmación de eliminación
- [x] `frontend/src/pages/EliminarPregunta.tsx`
  - Resuelve `materia` vía `listarMaterias()` + `materiaId` de la ruta (mismo patrón que
    `EditarPregunta.tsx`)
  - Resuelve `pregunta` vía `filtrarBanco(materia.bancoId)` + `preguntaId` de la ruta (ya
    existe `eliminarPregunta(preguntaId)` en `banco-preguntas-api.ts`, sin cambios de cliente
    API necesarios)
  - Muestra el texto de la pregunta a eliminar y un mensaje explícito de que es baja lógica
    (no afecta sesiones pasadas) — `wireframes-banco-preguntas.md` §2.8
  - Acción primaria "Sí, eliminar" (destructiva) → `eliminarPregunta(preguntaId)` →
    `navigate(/materias/:materiaId/banco)`
  - Acción secundaria "Cancelar" → `navigate(/materias/:materiaId/banco)` sin llamar al backend
  - Estados de carga ("Cargando…") y de pregunta no encontrada, mismo criterio que
    `EditarPregunta.tsx`

### 2. Integración con routing y con `Banco.tsx`
- [x] `frontend/src/router.tsx`
  - Nueva ruta `/materias/:materiaId/banco/preguntas/:preguntaId/eliminar` → `EliminarPregunta`
    (reemplaza el placeholder, mismo criterio que `US-2.1.11`/`US-2.1.12`)
- [x] `frontend/src/pages/Banco.tsx`
  - Habilita el botón "Eliminar" de la tabla (actualmente `disabled` con
    `title="Disponible en US-2.1.13"`) — navega a la ruta de confirmación en vez de estar
    deshabilitado

**Estado:** 2/2 tareas completadas

## Lecciones Aprendidas

- ✅ El patrón de resolución de `materia`/`pregunta` establecido por `EditarPregunta.tsx`
  (`US-2.1.12`) se reutilizó sin ajustes — misma forma de obtener la pregunta vía
  `filtrarBanco()`, mismo criterio de "Cargando…"/"no encontrada".
- ✅ Cierra completa la Iteración 1 del Incremento 2 (`US-2.1.10` a `US-2.1.13`) sin desvíos de
  alcance respecto al plan de `docs/plans/inc2/inc2-candidatas.md`.
