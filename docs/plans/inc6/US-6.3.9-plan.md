# Plan de Implementación: US-6.3.9 - Estudiante responde desde el celular y ve su resultado y el final

**Patrón:** React 19 + TypeScript + Vite, sobre el contenedor de `US-6.3.8` (sin cambios de `src/`)
**Producto:** Cognion — frontend

## Alcance

No se divide (la spec lo permitía si se pasaba de alcance): la lógica de etapas vive en funciones puras
(`vista-estudiante.ts`, mismo criterio que `vista-proyeccion.ts`) y las 5 pantallas son presentacionales, así que el
contenedor queda chico. Si en la Fase 3 aparece algo que no entra, se avisa antes de seguir.

## Decisiones de diseño (Fase 2)

- **Etapas** (`estudiante/vista-estudiante.ts`): `sala` | `espera-opciones` | `pregunta` | `resultado` | `sin-respuesta`
  | `finalizada`. La vista guarda la pregunta actual (índice 0-based, total, `preguntaId`, enunciado, tipo, opciones,
  tiempo límite, inicio del temporizador), `puntajeAcumulado`, el resultado de la última respuesta (`{esCorrecta,
  puntaje}` o `null` si no se conoce), el motivo de "sin respuesta" (`cierre` / `tiempo`) y el ranking final.
- **`calcularVistaEstudiante(estado, { trasRechazo })`** (al montar, al reconectar y tras un rechazo):
  `en_espera` → sala; `finalizada` → final; `en_curso` → `yaRespondio` → resultado (solo acumulado);
  `preguntaActualCerrada` → sin respuesta (`cierre`); sin opciones → espera de opciones; con opciones y sin responder →
  pregunta, **salvo** `trasRechazo` → sin respuesta (`tiempo`, H5). Así el `422` de texto libre no se parsea
  (contexto §Notas).
- **`aplicarMensajeEstudiante`**: `pregunta_presentada` → espera de opciones de la nueva pregunta (limpia resultado);
  `opciones_mostradas` → pregunta, temporizador desde la llegada; `pregunta_cerrada` → si estaba en `pregunta`, sin
  respuesta (`cierre`), si ya respondió no cambia — **nunca muestra la correcta ni el ranking**;
  `sesion_finalizada` → final con el ranking; `participantes_actualizados` → conteo. Mensaje de otra pregunta →
  `"recalcular"` (como la proyección).
- **Responder** (contenedor): una sola request en vuelo (las tarjetas se deshabilitan al primer toque).
  `{opcion_indice: i}` o `{valor: true|false}`. `200` → resultado con `esCorrecta`/`puntaje`/`puntajeAcumulado`.
  `422` → `GET estado` con `trasRechazo`. `404` → `unirseASesion` y `GET estado`. Otro error → aviso y las tarjetas se
  rehabilitan.
- **Final:** ranking del mensaje o, al recargar, de `GET .../ranking`. Posición propia buscando `obtenerUsuarioId()`.
  Top 3 (`top3`) con la fila propia resaltada; si quedó fuera, su fila debajo con su posición. Si no está en el ranking:
  "No sumaste puntos en esta sesión".
- **Pantallas** (`estudiante/`), identidad estándar (no `stage-*`), pensadas para pulgar:
  - `EsperaOpciones` — barra de progreso, "Pregunta N de total", enunciado, "Esperá a que el Docente muestre las opciones".
  - `PreguntaActiva` — barra, "Pregunta N de total" + temporizador (`useSegundosRestantes`), enunciado, tarjetas
    `opcionesEnVivo` en grilla 2 columnas, `min-h-[110px]` (≥ 44 px), la tercera de 3 a ancho completo, hint del
    único intento.
  - `ResultadoPregunta` — ✅ / ❌, "¡Correcto!" / "Incorrecto", "+N puntos en esta pregunta" (si se conoce),
    "Llevás acumulados: X pts", "el ranking se ve recién al final".
  - `SinRespuesta` — "Se cerró la pregunta — No respondiste (+0)" o "Se acabó el tiempo antes de tu respuesta (+0)",
    acumulado.
  - `ResultadoFinal` — 🏆, "¡Terminó la sesión!", "Quedaste N° con X puntos", lista Top 3 + fila propia.

## Componentes a Implementar

- [ ] `estudiante/vista-estudiante.ts` — etapas nuevas (+ tests)
- [ ] `estudiante/EsperaOpciones.tsx`, `PreguntaActiva.tsx`, `ResultadoPregunta.tsx`, `SinRespuesta.tsx`, `ResultadoFinal.tsx` (+ tests)
- [ ] `SesionEnVivoEstudiante.tsx` — etapas, responder, rechazos, ranking final al recargar (+ tests)
- [ ] Validar los 15 escenarios de `tests/features/inc6/US-6.3.9-responder-resultado-estudiante.feature` con Vitest

**Estado:** 0/4 tareas completadas
