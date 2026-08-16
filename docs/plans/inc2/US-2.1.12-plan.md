# Plan de Implementación: US-2.1.12 - Docente edita una pregunta existente desde la UI

**Patrón:** React 19 + TypeScript + Vite (frontend puro, sin capas Clean Architecture)
**Producto:** cognion-frontend

## Componentes a Implementar

### 1. Pantalla de edición

- [x] `frontend/src/pages/EditarPregunta.tsx`
  - Lee `materiaId` y `preguntaId` de la ruta (`useParams`)
  - Resuelve `materia` con `listarMaterias()` (mismo patrón que `Banco.tsx`/`NuevaPregunta*.tsx`)
  - Obtiene la pregunta a editar con `filtrarBanco(materia.bancoId)` y busca por `preguntaId`
    en el resultado — sin endpoint `GET /preguntas/{id}` nuevo (no existe; reutiliza
    `US-2.1.7`, mismo criterio "sin cambios de backend" de la spec)
  - Determina el tipo concreto (`"opciones" in pregunta`, mismo helper que `Banco.tsx`) y
    renderiza el formulario correspondiente, prellenado con los valores actuales
  - Formulario de Opción Múltiple: mismos campos/validación de cliente que
    `NuevaPreguntaOpcionMultiple.tsx` (mínimo 2 opciones, exactamente una correcta), inicializado
    con `pregunta.opciones`
  - Formulario de Verdadero/Falso: mismos campos que `NuevaPreguntaVerdaderoFalso.tsx`,
    inicializado con `pregunta.respuestaCorrecta`
  - Sin selector de tipo (fijo, no editable — mismo criterio que el backend `US-2.1.5` y que
    `#nueva-pregunta-tipo`)
  - Botón primario "Guardar cambios" (en vez de "Guardar pregunta") → llama
    `editarPregunta(preguntaId, body)` (ya existe en `banco-preguntas-api.ts`, sin cambios) →
    `navigate` de vuelta a `/materias/{materiaId}/banco`
  - Botón secundario "Cancelar" → mismo destino, sin guardar
  - Estados de carga: "Cargando…" mientras se resuelve `materia`/`pregunta`; si `preguntaId` no
    aparece en el resultado de `filtrarBanco` (pregunta inexistente o dada de baja), mostrar
    mensaje de error simple en vez de formulario — sin pantalla dedicada (mismo criterio de
    simplicidad del wireframe §4 para otros errores)

### 2. Integración

- [x] `frontend/src/router.tsx`
  - Reemplazar el placeholder de la ruta
    `/materias/:materiaId/banco/preguntas/:preguntaId/editar` (ya declarada desde `US-2.1.8`,
    protegida con `RequireRole rol="docente"`) por `<EditarPregunta />`

**Estado:** 2/2 tareas completadas
