# Evidencia UAT — Incremento 6 "Sesión en vivo", Iteración 3

| Campo | Valor |
|-------|-------|
| Diseño | `quality/reports/uat/inc6/design-iteracion3.md` |
| Fecha ejecución | 2026-09-25 |
| Ejecutor | Tramo 1: sesión de Claude Code (circuitos Playwright, sin intervención). Tramo 2: Víctor en persona — **pendiente** (`guion-validacion-iteracion3.md`) |
| Estado | Tramo 1 aprobado · Tramo 2 pendiente |

---

## Tramo 1 — circuitos E2E (Playwright)

`cd frontend && npm run test:e2e` — backend (`uvicorn`) y frontend (`npm run dev`, `StrictMode`) reales,
PostgreSQL local, un contexto de navegador aislado por actor.

| Corrida | Resultado | Duración |
|---|---|---|
| 1 (con reporte HTML/JSON) | 10/10 ✓ | 2,1 min |
| 2 | 10/10 ✓ | 2,3 min |
| 3 | 10/10 ✓ | 2,0 min |
| 4 — **a través del proxy de desarrollo** (`VITE_API_BASE_URL=http://localhost:5173/api`) | 10/10 ✓ | 2,0 min |

Los 10 tests cubren los 8 circuitos de `design-iteracion3.md` (el 2 y el 7 tienen dos casos cada uno). Sin
tests inestables en las 4 corridas. Reporte navegable: `playwright-report/` (con capturas de cada pantalla
clave); datos: `playwright-resultados.json`.

### Mediciones

| Qué | Valor | Criterio |
|---|---|---|
| Histograma (con ranking) desde "Cerrar pregunta" | 112, 101, 123 ms | < 1 s ✓ |
| Enunciado, pregunta sola | 40 px, contraste 17,46:1 | ≥ 40 px, ≥ 7:1 ✓ |
| Eyebrow "Pregunta N de total" | 20 px, mayúsculas, 8,05:1 | ≥ 18 px ✓ |
| Temporizador | 60 px, 17,46:1 | ≥ 26 px ✓ |
| Opciones (texto de las cajas) | 28 px | ≥ 26 px ✓ |
| Conteo / cierre | 28 px, 17,46:1 | ✓ |
| Enunciado con opciones a la vista | 30 px | informado (H4) |
| Contraste de las cajas de color | a 5,05 · b 3,57 · c 7,29 · d 3,73 : 1 | informado (H3) |
| Scroll a 1920×1080 | ninguno en pregunta, opciones, histograma, ranking ni podio | ✓ |
| Tarjeta táctil (celular 375×812) | 110 × 157,5 px, sin scroll horizontal | ≥ 44 px ✓ |
| Sockets por pantalla con `StrictMode` | ≤ 1 abierto al final, sin reconexiones en bucle | ✓ |

## Capa 1 — regresión del frontend

```
cd frontend && npm run test:coverage   →  103 archivos, 717/717 (92,48% stmts / 84% branches)
npx tsc -b                             →  0 errores
npx oxlint src e2e                     →  0 errores (6 warnings preexistentes en src/)
```

Backend sin cambios en esta iteración de UAT: sin `pytest` contra la base local (la vaciaría); lo corre el CI.

---

## Hallazgos

| Id | Severidad | Qué | Estado |
|---|---|---|---|
| H1 | 🔴 Bloqueante | **Estado de la sesión con otro formato que el del backend.** El cliente (`US-6.3.4`) tipaba `en_espera`/`en_curso`/`finalizada`; el backend manda `EnEspera`/`EnCurso`/`Finalizada`. Ninguna comparación de estado funcionaba en el navegador: el Estudiante veía una pregunta vacía en la sala, las sesiones finalizadas seguían como activas, la sala del Docente no redirigía, sin podio al recargar. Invisible a Vitest: los mocks usaban el formato del cliente | ✅ Corregido (`17d93d7`): traducción en `sesion-en-vivo-api.ts`, mocks con el formato real. Track informal (solo `frontend/`) |
| H2 | 🔴 Bloqueante | **Mensajes del WebSocket en snake_case, parser en camelCase.** Todos los campos llegaban vacíos ("Pregunta NaN de 3", sin temporizador, ranking sin ids). Mismo origen que H1 | ✅ Corregido (`c7263ca`): el parser traduce cada mensaje; tests del canal con el formato real |
| H3 | 🟡 Observación | Contraste de las cajas de opción azul (3,57:1) y verde (3,73:1), y roja (5,05:1), bajo el 7:1 de §1.1. Colores del prototipo aprobado; texto de 28 px en negrita | Decisión de Víctor (guion §5) |
| H4 | ⚪ Estético | Enunciado de 30 px con las opciones a la vista (40 px con la pregunta sola), como en el prototipo | Decisión de Víctor (guion §5) |
| H5 | 🟡 Observación | Un celular de la red no podía usar la app en desarrollo: el frontend apunta a `localhost:8000` y el CORS del backend solo admite `localhost:5173` | ✅ Resuelto sin tocar `src/`: proxy de desarrollo de Vite (`/api`, HTTP + WS); verificado con la corrida 4 |

**Lección (H1, H2):** los clientes de `US-6.3.4` se escribieron contra el contrato de la spec, no contra el
backend real, y los tests de Vitest heredaron el mismo supuesto — cada capa confirmaba a la otra. Los
circuitos E2E contra el backend real son la red que faltaba; quedan en el repo para regresión.

---

## Tramo 2 — validación de Víctor

Pendiente. Guion: `guion-validacion-iteracion3.md` (proyección + celular real, decisiones H3/H4).
