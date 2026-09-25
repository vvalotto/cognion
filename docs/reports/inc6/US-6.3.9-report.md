# Reporte de Implementación: US-6.3.9

## Resumen Ejecutivo

- **Historia de Usuario:** US-6.3.9 — Estudiante responde desde el celular y ve su resultado y el final (Issue #420)
- **Puntos estimados:** 5
- **Tiempo real:** ver `.claude/tracking/US-6.3.9-tracking.json`
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-25
- **Aporta:** completa el flujo del Estudiante en el modo en vivo. Con esta US están todas las pantallas de la
  Iteración 3; sigue la UAT en navegador real y celular real (`US-6.3.10`).
- **No se dividió** (la spec lo permitía): la lógica de etapas en funciones puras dejó el contenedor chico.

---

## Componentes Implementados

### Etapas (`estudiante/vista-estudiante.ts`)

- ✅ `sala` → `espera-opciones` → `pregunta` → `resultado` / `sin-respuesta` → `finalizada`.
- ✅ `calcularVistaEstudiante(estado, { trasRechazo })`: `yaRespondio` → resultado (solo acumulado); pregunta cerrada →
  sin respuesta (`cierre`, H4); sin opciones → espera; con opciones y sin responder → pregunta, o, tras un rechazo, sin
  respuesta (`tiempo`, H5).
- ✅ `aplicarMensajeEstudiante`: `pregunta_presentada`, `opciones_mostradas` (temporizador desde la llegada),
  `pregunta_cerrada` (solo afecta si no respondió), `sesion_finalizada` (ranking), `participantes_actualizados`;
  mensaje de otra pregunta → recalcular. **El celular nunca muestra la correcta ni el ranking antes del final.**
- ✅ `registrarRespuesta`, `contenidoRespuesta` (`{opcion_indice}` / `{valor}`).

### Pantallas (`estudiante/`)

- ✅ `EsperaOpciones` (H3), `PreguntaActiva` (tarjetas `opcionesEnVivo` en 2 columnas, `min-h-[110px]`, la tercera de 3 a
  ancho completo, V/F en `b`/`c`, temporizador, hint del único intento), `ResultadoPregunta` (¡Correcto! / Incorrecto,
  +N, acumulado, sin ranking; "Ya respondiste" tras recargar), `SinRespuesta` (cierre / tiempo), `ResultadoFinal`
  ("Quedaste N° con X puntos", Top 3 con fila propia, fila propia debajo si quedó fuera, "No sumaste puntos").
- ✅ `BarraPregunta` y `Acumulado`: piezas compartidas.

### Contenedor (`SesionEnVivoEstudiante.tsx`)

- ✅ Responder con una sola request en vuelo. `422` → `GET estado` con `trasRechazo`; `404` → reunirse y recalcular;
  otro error → aviso y tarjetas rehabilitadas.
- ✅ Final al recargar: ranking de `GET .../ranking`; posición propia con `obtenerUsuarioId()`.

---

## Gap de contrato resuelto en el cliente

`POST .../responder` devuelve `TiempoAgotado`, `RespuestaYaRegistrada` y `PreguntaYaCerrada` como `422` con `detail`
de texto libre. En vez de parsear el texto, la pantalla sale del estado del servidor. Sin cambios de `src/`. Un código
de error estructurado en el backend sería más limpio: queda como posible `US-ADJ` si se decide.

---

## Métricas de Calidad

| Gate | Resultado |
|---|---|
| `oxlint` / `tsc -b` | 0 errores (6 warnings preexistentes) |
| `npm run test:coverage` | 714/714 (103 archivos) a la primera |
| Cobertura global | 92,47% stmts / 84,08% branches |
| Cobertura archivos de la US | 95,34% stmts / 93,28% branches / 100% líneas |

## Tests Implementados

- `vista-estudiante.test.ts` (21), `Etapas.test.tsx` (19 — las 5 pantallas), `SesionEnVivoEstudiante.test.tsx` (+15
  para responder, rechazos, cierre, siguiente pregunta, recarga, reconexión, final dentro y fuera del Top 3).
- **Escenarios BDD (15):** `tests/features/inc6/US-6.3.9-responder-resultado-estudiante.feature`, validados con Vitest.

## Criterios de Aceptación

✅ los 15 escenarios. ⚠️ Tamaño táctil y el flujo con WebSocket real: se verifican en un celular real en `US-6.3.10`.

## Próximos Pasos

- `US-6.3.10`: UAT en navegador real (Docente + Estudiante en celular real) — cierra la Iteración 3.
- Baseline `BL-011`.

## Lecciones Aprendidas

- Cuando el backend no distingue errores por código, el estado del servidor después del rechazo suele alcanzar para
  decidir la pantalla, sin depender del texto del mensaje.
