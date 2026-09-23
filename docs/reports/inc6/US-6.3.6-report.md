# Reporte de Implementación: US-6.3.6

## Resumen Ejecutivo

- **Historia de Usuario:** US-6.3.6 — Docente proyecta la pregunta, muestra las opciones y la cierra
- **Puntos estimados:** 5
- **Tiempo real:** ~19 min (tracker, Fases 0 a 9). Detalle en `.claude/tracking/US-6.3.6-tracking.json`
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-23
- **Aporta:** primera mitad de la pantalla de proyección del modo en vivo. El Docente ve la pregunta
  sola, muestra las opciones (arranca el temporizador), ve el conteo de respuestas en vivo y cierra la
  pregunta. Crea el contenedor `ProyeccionSesionEnVivo` sobre el que `US-6.3.7` agrega las etapas de
  resultado.

---

## Componentes Implementados

### Contenedor y máquina de etapas (`ProyeccionSesionEnVivo.tsx`, nuevo)

- ✅ Etapa calculada desde `GET estado` al montar y en cada `onReconectado`
  (`vista-proyeccion.ts`: `calcularVista`, función pura); `EnEspera` redirige a la sala
- ✅ Etapa mantenida con los mensajes del canal (`aplicarMensaje`, función pura): un mensaje de otra
  pregunta o de una pregunta cerrada que no encaja dispara recálculo desde el servidor
- ✅ "Mostrar opciones" / "Cerrar pregunta": una sola request en vuelo (doble click seguro); la
  etapa siguiente llega por el canal y, si en 2 s no llegó, se recalcula con `GET estado`;
  `422` (`OpcionesYaMostradas`/`PreguntaYaCerrada`) también recalcula
- ✅ `AbortController` creado en `useEffect` (lección `US-ADJ-20`)
- ✅ Etapas `cerrada`/`finalizada`: texto mínimo, punto de extensión para `US-6.3.7`; el resultado
  (`respuestaCorrecta`, distribución, ranking) ya queda guardado en la vista

### Etapas (`proyeccion/`)

- ✅ `StagePreguntaSola`: enunciado ≥ 40 px, eyebrow "Pregunta N de total", sin opciones
- ✅ `StagePreguntaOpciones`: cajas de color sólido sin ícono ni marca de correcta, temporizador
  (`role="timer"`) con barra de progreso, conteo "N / total ya respondieron", "Cerrar pregunta"
  destructivo; con el temporizador en 0 no cierra nada

### Librerías compartidas (con `US-6.3.9`)

- ✅ `lib/opciones-en-vivo.ts`: color por opción; Verdadero/Falso = `b`/`c` (H1); N opciones cíclico
  `a,b,c,d` (H2); texto oscuro sobre amarillo
- ✅ `lib/temporizador-pregunta.ts`: `segundosRestantes` acotado a ≥ 0, `formatearTemporizador`,
  hook `useSegundosRestantes`

### Componente compartido

- ✅ `components/IndicadorConexion.tsx` (H8): segundo consumidor → extraído; `SalaEsperaDocente`
  pasa a usarlo sin cambio de comportamiento

### Rutas

- ✅ `router.tsx`: reemplaza el placeholder de proyección (dentro de `StageLayout`, rol `docente`)

---

## Sin gap de backend

`mostrarOpciones`, `cerrarPregunta`, `obtenerEstadoSesion` y los mensajes del canal ya existían
(`US-6.2.x`, `US-6.3.3`, `US-6.3.4`). Sin cambios de `src/`. `preguntaActualIndice` es 0-based, por eso
el eyebrow muestra `indice + 1`.

---

## Métricas de Calidad

| Gate | Resultado |
|---|---|
| `oxlint` | 0 errores (6 warnings preexistentes) |
| `tsc -b` | 0 errores |
| Vitest | 610/610 (95 archivos), con `--testTimeout=20000` |
| Cobertura global | 92,19% stmts / 82,64% branches (umbral 80%) |
| Cobertura archivos nuevos | 97,61% stmts / 92,94% branches / 100% líneas |

`NuevaPreguntaOpcionMultiple.test.tsx` (flake preexistente) expira a 5 s bajo la carga del suite
completo sin `--testTimeout`; pasa aislado.

---

## Tests Implementados

- **Unitarios:** `opciones-en-vivo`, `temporizador-pregunta` (fake timers), `IndicadorConexion`,
  `vista-proyeccion` (todas las etapas y todos los mensajes), `StagePreguntaSola`,
  `StagePreguntaOpciones`.
- **Integración:** `ProyeccionSesionEnVivo.test.tsx` (canal falso, fetch mockeado) — 19 casos.
- **Escenarios BDD (10):** `tests/features/inc6/US-6.3.6-proyeccion-pregunta-opciones.feature`,
  validados con Vitest (sin step_defs). Casos extra: etapa por estado, `422`, mensaje que no encaja,
  error inesperado.

---

## Criterios de Aceptación

- ✅ Pregunta sola sin opciones · ✅ mostrar opciones arranca el temporizador · ✅ no revela la
  correcta · ✅ Verdadero/Falso · ✅ conteo en vivo · ✅ temporizador en 0 no cierra · ✅ cerrar
  pregunta · ✅ recarga descuenta el tiempo · ✅ doble click una sola request · ✅ reconexión
- ⚠️ **Tamaños de fuente y contraste (§1.1):** aplicados con clases/tokens, **no verificables en
  jsdom** — se verifican en navegador real en `US-6.3.10`.

---

## Próximos Pasos

- `US-6.3.7`: histograma, ranking Top 3 y podio sobre el mismo contenedor (etapas `cerrada`/`finalizada`).
- `US-6.3.9`: reutiliza `opciones-en-vivo.ts` y `temporizador-pregunta.ts`.
- `US-6.3.10`: verificar tipografía, contraste y ausencia de scroll en el proyector real.

## Lecciones Aprendidas

- Poner la lógica de etapas en funciones puras (`calcularVista`/`aplicarMensaje`) dejó el
  contenedor fino y los escenarios testeables sin canal ni timers.
- Un test con `renderHook(() => hook(..., Date.now()))` recalcula el inicio en cada render: el
  tiempo de referencia va fuera del callback.
