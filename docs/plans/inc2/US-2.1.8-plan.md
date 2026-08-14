# Plan de Implementación: US-2.1.8 - Infraestructura de frontend del Banco de Preguntas

**Patrón:** React 19 + TypeScript + Vite (sin Clean Architecture — no aplica a frontend)
**Producto:** banco_preguntas (frontend)
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-14

## Métricas de Tiempo

| Fase | Tiempo real |
|------|-------------|
| 0 — Análisis de spec | 107s |
| 1 — Escenarios BDD | 22s |
| 2 — Plan de implementación | 136s |
| 3 — Implementación | 146s |
| 4 — Tests unitarios | 345s |
| 5 — Tests de integración | 23s |
| 6 — Validación BDD | 5s |
| 7 — Quality Gates | 30s |
| **Total (fases 0-7)** | **~14 min** |

> Sin comparación contra estimación humana (PRIN-001) — el tracking registra tiempo real de
> ejecución del agente, no tiempo humano equivalente.

## Lecciones Aprendidas

- ✅ Fase 2 detectó a tiempo que el backend no expone `GET /materias` (la spec de `US-2.1.9`
  lo asumía existente) — se excluyó `listarMaterias` del alcance de esta US en vez de
  descubrirlo recién al implementar `US-2.1.9`.
- ✅ Mapeo explícito snake_case↔camelCase en `banco-preguntas-api.ts` (en vez de pasar los
  schemas del backend tal cual) mantiene el frontend con convenciones TS idiomáticas sin
  acoplarse a los nombres de los schemas Pydantic.

## Alcance ajustado (gap detectado en esta fase)

El backend no expone `GET /materias` (listado) — solo `POST /materias` (`US-2.1.1`). La spec
de `US-2.1.9` asumía que ya existía, pero no es así. Decisión de Víctor: **excluir
`listarMaterias` de esta US**. `US-2.1.9` queda bloqueada hasta que ese endpoint exista
(se documenta en el reporte de cierre y en el `## Próximo paso` de `CLAUDE.md`).

## Componentes a Implementar

### 1. Cliente API del dominio
- [x] `frontend/src/lib/banco-preguntas-api.ts`
  - Funciones tipadas que envuelven `apiFetch` (reutilizan JWT/401/403 de `api-client.ts`,
    sin duplicar esa lógica):
    - `crearMateria(nombre: string)` → `POST /materias`
    - `filtrarBanco(bancoId: string, filtros?: { unidad?, tema?, dificultad?, importancia? })`
      → `GET /bancos/{banco_id}/preguntas?...` (query string con los filtros presentes)
    - `cargarPreguntaOpcionMultiple(body)` → `POST /preguntas/opcion-multiple`
    - `cargarPreguntaVerdaderoFalso(body)` → `POST /preguntas/verdadero-falso`
    - `editarPregunta(preguntaId: string, body)` → `PUT /preguntas/{pregunta_id}`
    - `eliminarPregunta(preguntaId: string)` → `DELETE /preguntas/{pregunta_id}`
  - Tipos de request/response reflejan los schemas Pydantic de
    `src/banco_preguntas/frameworks/api/schemas.py` (`Dificultad`/`Importancia` como union de
    strings literales, no enums — no hay codegen en este proyecto)

### 2. Placeholder de pantalla
- [x] `frontend/src/pages/_placeholders.tsx`
  - Agregar `BancoPreguntasPlaceholder` (mismo criterio que `InicioPlaceholder`) — destino
    temporal de todas las rutas nuevas hasta que `US-2.1.9` a `US-2.1.13` las reemplacen

### 3. Routing
- [x] `frontend/src/router.tsx`
  - Rutas nuevas dentro de `AppLayout`, todas envueltas en `RequireRole rol="docente"`
    (mismo patrón que `/docentes/nuevo` en `US-1.1.9`):
    - `/materias` (US-2.1.9)
    - `/materias/nueva` (US-2.1.9)
    - `/materias/:materiaId/banco` (US-2.1.10)
    - `/materias/:materiaId/banco/preguntas/nueva` (US-2.1.11 — elegir tipo)
    - `/materias/:materiaId/banco/preguntas/nueva/opcion-multiple` (US-2.1.11)
    - `/materias/:materiaId/banco/preguntas/nueva/verdadero-falso` (US-2.1.11)
    - `/materias/:materiaId/banco/preguntas/:preguntaId/editar` (US-2.1.12)
  - `US-2.1.13` (eliminar) no agrega ruta propia — confirmación embebida en `#banco`
    (wireframe §2.8), sin ruta dedicada

### 4. Integración
- [x] Ninguna dependencia nueva — reutiliza `apiFetch`/`ApiError` (`api-client.ts`, `US-1.1.6`)
  y `RequireRole` (`US-1.1.9`) sin cambios

**Estado:** 0/4 tareas completadas
