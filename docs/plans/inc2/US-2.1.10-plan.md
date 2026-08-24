# Plan de Implementación: US-2.1.10 - Docente ve y filtra el banco de preguntas de una materia

**Patrón:** React 19 + TypeScript + Vite (frontend puro, sin cambios de backend)
**Producto:** banco_preguntas
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-16

## Métricas de Tiempo

| Fase | Tiempo real |
|------|-------------|
| 0 — Validación de contexto | 111s |
| 1 — Escenarios BDD | 47s |
| 2 — Plan de implementación | 323s |
| 3 — Implementación | 132s |
| 4 — Tests unitarios | 205s |
| 5 — Tests de integración | 77s |
| 6 — Validación BDD | 9s |
| 7 — Quality Gates | 132s |
| **Total (fases 0-7)** | **~17 min** |

> Sin comparación contra estimación humana (PRIN-001).

## Lecciones Aprendidas

- ✅ Reutilizar `listarMaterias()` (ya existente desde `US-2.1.9`) para resolver
  `materiaId → nombre/bancoId` evitó agregar un endpoint `GET /materias/{id}` — mismo
  criterio de "sin ensanchar el backend" ya aplicado en US previas.
- ⚠️ Ajuste respecto del plan original: el botón "Eliminar" por fila no navega a una ruta
  de confirmación (esa ruta todavía no existe — la crea `US-2.1.13`). Quedó deshabilitado
  con un `title` explicativo en vez de apuntar a una ruta placeholder inexistente.
- ⚠️ Las columnas de dificultad/importancia se muestran como texto simple, no como "tag por
  color" (wireframe §2.3) — no hay un sistema de color de tags definido todavía en el
  proyecto; se prioritizó no introducir una convención de color ad hoc sin acordarla. Queda
  como posible ajuste visual menor a futuro, no bloqueante.
- ✅ Usar `fireEvent.change` en vez de `userEvent.type` para los filtros de texto evitó
  disparar una consulta por cada tecla (cada `onChange` dispara `filtrarBanco`), que producía
  "Unhandled Rejection" por mocks de `fetch` agotados en los tests.

## Componentes a Implementar

### 1. Frontend — pantalla
- [x] `frontend/src/pages/Banco.tsx`
  - Resuelve `materiaId` (param de ruta) contra `listarMaterias()` (ya existente, `US-2.1.9`)
    para obtener `nombre` (breadcrumb) y `bancoId` (necesario para `filtrarBanco`) — sin
    endpoint nuevo, mismo criterio de "sin ensanchar el backend" que `US-2.1.9`
  - Barra de filtros: unidad temática (texto libre), tema (texto libre), dificultad
    (`select` nativo Alto/Medio/Bajo/Todos), importancia (`select` nativo, mismas opciones) —
    sin componente `Select` de shadcn/ui nuevo, ya que no está instalado y un `<select>`
    nativo cubre el wireframe sin ampliar dependencias
  - Cambiar cualquier filtro dispara `filtrarBanco(bancoId, filtros)` y refresca la tabla
    (`useEffect` con los filtros como dependencia)
  - Tabla: columnas texto (truncado con `line-clamp`/`truncate`), tipo (tag derivado de
    `"opciones" in pregunta` para diferenciar Opción Múltiple / Verdadero-Falso), unidad/tema,
    dificultad (tag por color), importancia (tag por color), acciones
  - Acciones por fila: "Editar" → navega a
    `/materias/:materiaId/banco/preguntas/:preguntaId/editar` (ruta ya placeholder desde
    `US-2.1.8`, la reemplaza `US-2.1.12`); "Eliminar" → navega a la ruta de confirmación
    correspondiente (placeholder, la reemplaza `US-2.1.13`) — sin lógica propia en esta US,
    solo el punto de entrada visual pedido por el wireframe §2.3
  - Botón "+ Nueva pregunta" → navega a `/materias/:materiaId/banco/preguntas/nueva`
    (placeholder, la reemplaza `US-2.1.11`)
  - Combinación de filtros sin resultados → tabla vacía sin mensaje de error (resultado
    válido, no excepción — igual criterio que el backend en `US-2.1.7`)
  - Contador de preguntas activas visibles en el breadcrumb (`preguntas.length`)

### 2. Integración — routing
- [x] `frontend/src/router.tsx`
  - Reemplazar el placeholder `BancoPreguntasPlaceholder` de la ruta
    `/materias/:materiaId/banco` por `<Banco />`
  - Las demás rutas placeholder de banco (`nueva`, `nueva/opcion-multiple`,
    `nueva/verdadero-falso`, `:preguntaId/editar`) quedan sin tocar — corresponden a
    `US-2.1.11` a `US-2.1.13`

**Sin cambios de cliente API** — `filtrarBanco()` y `listarMaterias()` ya existen en
`frontend/src/lib/banco-preguntas-api.ts` desde `US-2.1.7`/`US-2.1.9` respectivamente.

**Estado:** 2/2 tareas completadas
