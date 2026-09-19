# Incremento 6 — Sesión en Vivo — US candidatas

> Estado documental: **Iteración 0 (Modelado) e Iteración 1 (RF-08 + infraestructura
> WebSockets) cerradas; Iteración 2 (RF-09, RF-10) especificada 2026-09-19.** Spike del
> algoritmo de puntaje (RF-10) resuelto con Víctor 2026-09-17 (detalle más abajo). Milestone
> [`Incremento 6 — Sesión en Vivo`](https://github.com/vvalotto/cognion/milestone/8).
>
> Fuente: `docs/rf/PLAN_v1.md` §Incremento 6, `docs/rf/RF_v1.md` (RF-08, RF-09, RF-10),
> `docs/rf/RNF_v1.md` (Rendimiento, Escenario 1 — ranking en vivo), `ADR-015` (BC Actividad
> Evaluativa cubre ambos modos, en vivo y período abierto — un solo BC, agregado nuevo, no BC
> aparte), `docs/design/domain/BC-actividad-evaluativa-modelo.md` (agregado
> `ActividadEvaluativaPeriodoAbierto` ya existente, patrón de Event Sourcing + CQRS a seguir
> para el agregado nuevo `ActividadEvaluativaEnVivo`).

---

## Nota de contexto — qué cambia respecto de los BCs/agregados anteriores

Mismo BC (`Actividad Evaluativa`) que el Incremento 3 — **no se crea un BC nuevo**. `ADR-015`
ya había reservado el nombre `ActividadEvaluativaEnVivo` como agregado hermano de
`ActividadEvaluativaPeriodoAbierto` al renombrar el BC, antes incluso de empezar a modelarlo
("cubre ambos modos... igual de bien que 'Sesión'"). Reutiliza el mismo lenguaje ubicuo
(pregunta, respuesta, estudiante, comisión, corrección) y los mismos puertos ya existentes
hacia Banco de Preguntas e Identidad — sin duplicar esa integración ni el puerto de consulta
que usa Analytics para proyectar desempeño.

Lo que sí es genuinamente nuevo, y exige su propio event storming (no una simple extensión de
lo ya modelado):

- **Dinámica sincrónica multi-participante**: todos los estudiantes conectados ven la misma
  pregunta al mismo tiempo (RF-09) — invariante sin equivalente en
  `ActividadEvaluativaPeriodoAbierto`, pensado para el ritmo individual y asíncrono de un solo
  estudiante (suspender/reanudar propio, sin coordinación con otros).
- **Eventos de tiempo real** sin equivalente en el agregado actual: creación de la sesión en
  vivo, un estudiante uniéndose, presentación/cierre de cada pregunta, actualización de
  ranking tras cada cierre.
- **Cálculo de puntaje server-side** (ver spike RF-10 más abajo) — el puntaje nunca lo calcula
  ni lo envía el cliente, se deriva en el servidor al cerrar cada pregunta a partir de
  `tiempo_respuesta`, corrección, dificultad e importancia.
- **Capa de `frameworks/` con WebSockets** — no existe hoy en el proyecto; primer uso real del
  mecanismo de transporte ya prometido en `ARQ_v1.md`/`ADR-002` pero nunca implementado.
- **Umbral de rendimiento duro**: procesamiento server-side (cálculo de ranking + broadcast)
  ≤ 100ms (`RNF_v1.md`, Rendimiento Escenario 1) — primer RNF de esta magnitud que el proyecto
  verifica con datos reales, no solo lo documenta.

Incremento de mayor riesgo técnico del proyecto (`PLAN_v1.md`) — se llega a él con el resto de
la arquitectura ya validada en producción (BL-001 a BL-010).

---

## Spike RF-10 — Algoritmo de puntaje en sesión en vivo

**Resuelto con Víctor 2026-09-17**, antes de arrancar el event storming (mismo criterio que
`PLAN_v1.md` exige: "se resuelve... junto al docente, antes de tocar código"). Cuatro
decisiones de producto, cada una con su alternativa considerada:

1. **Tiempo límite por pregunta**: fijo por sesión, campo obligatorio que el docente define al
   crear la sesión en vivo — **sin valor por defecto**. Descartado: configurable pregunta por
   pregunta (agrega coordinación innecesaria con Banco de Preguntas) y sesión sin timer con
   cierre manual del docente (vuelve el puntaje por velocidad impredecible para el alumno).
2. **Respuesta incorrecta o sin responder a tiempo**: **0 puntos**, sin penalización. Descartado:
   puntaje negativo (desalienta la participación, uso pedagógico del sistema).
3. **Dificultad e importancia**: **sí multiplican el puntaje** de una respuesta correcta — una
   pregunta ALTA vale más que una BAJA. Descartado: dejarlas solo como metadato de
   clasificación/Analytics sin efecto en el puntaje en vivo.
4. **Ranking de la sesión**: **suma simple** del puntaje de cada pregunta. Descartado: bonus
   por racha de aciertos consecutivos (agrega estado e invariantes nuevas sin pedido explícito
   de RF-09/RF-10).

### Fórmula resultante

```
Puntaje = 1000 × FactorTiempo × FactorDificultad × FactorImportancia   (solo si es correcta; si no, 0)

FactorTiempo       = 0.5 + 0.5 × (1 − tiempo_respuesta / tiempo_límite_sesión)
                     → rango [0.5, 1.0]: 1.0 si responde al instante, 0.5 si responde justo al límite
FactorDificultad   = {BAJO: 1.0, MEDIO: 1.5, ALTO: 2.0}
FactorImportancia  = {BAJO: 1.0, MEDIO: 1.5, ALTO: 2.0}

Ranking = suma simple del puntaje de cada pregunta de la sesión
```

Rango por pregunta: 500 (correcta, justo al límite de tiempo, dificultad/importancia BAJO) a
4000 (correcta, instantánea, dificultad/importancia ALTO) — con `PUNTAJE_BASE = 1000` y
multiplicadores `1.0/1.5/2.0` confirmados por Víctor sin ajuste.

**Consecuencia directa para el event storming**: el evento de cierre de pregunta necesita
`tiempo_respuesta` por participante (medido server-side, no confiar en el cliente) y la
dificultad/importancia de la pregunta ya resueltas al momento del cálculo — no se recalculan
después. `tiempo_límite_sesión` es un dato de la sesión en vivo, fijado en su creación,
inmutable durante la sesión.

---

## Iteración 0 — Modelado

| US | Tipo | Descripción | Postcondición (DoD) | Path del artefacto | Issue |
|---|---|---|---|---|---|
| US-6.0.1 | Modelado | Event storming de `ActividadEvaluativaEnVivo`: eventos de tiempo real, invariantes de sincronización y de ranking, incorporando la fórmula de puntaje ya resuelta arriba | Víctor aprueba el modelo en el comentario de cierre del Issue | `docs/design/domain/BC-actividad-evaluativa-modelo.md` §§10-18 (sección nueva — no se reescribe la de `ActividadEvaluativaPeriodoAbierto`) | [#379](https://github.com/vvalotto/cognion/issues/379) |
| US-6.0.2 | UX | Wireframes/prototipo de la pantalla en vivo (estudiante) y de proyección (aula) | Víctor aprueba el artefacto en el comentario de cierre del Issue | `docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` + prototipo HTML | [#380](https://github.com/vvalotto/cognion/issues/380) |

~~US-6.0.1~~ Cerrada 2026-09-17, Issue #379 — 4 hot spots confirmados en una única ronda (sala
de espera, unión tardía permitida, un solo intento por pregunta, avance en dos pasos).

~~US-6.0.2~~ Cerrada 2026-09-17, Issue #380 — seis rondas de ajuste con Víctor: histograma +
ranking separados; presentar pregunta y mostrar opciones en dos pasos manuales (color sólido,
sin ícono); tarjetas táctiles de color también en el celular del Estudiante, respuesta
inmediata al tocar; feedback personal sin ranking hasta el resultado final; y el cambio más
importante de modelo — la sesión se crea desde **una** Comisión puntual (`comision_id` única y
obligatoria vía `ComisionDetalleDocente.tsx`), no desde la Materia con comisiones opcionales
como período abierto. **Cierra completa la Iteración 0 del Incremento 6.**

Al cerrar la Iteración 0: actualizar `docs/traceability/matrix.md` — RF-08, RF-09 y RF-10
pasan de *Planificado* a *Especificado*.

---

## Iteración 1 — RF-08: creación de sesión en vivo + infraestructura WebSockets

Backend únicamente — mismo criterio de diferir frontend que la Iteración 1 del Incremento 3
(sin frontend propio todavía en `inc6-candidatas.md`). Alcance: hasta que la sesión queda
`EnCurso` con el enunciado de la primera pregunta transmitido — mostrar opciones, responder,
cerrar, avanzar, finalizar y el cálculo de puntaje/ranking quedan en la Iteración 2 (RF-09,
RF-10).

| US | Tipo | Comando/Evento | Actor | Invariantes | Issue |
|---|---|---|---|---|---|
| **US-6.1.1** *(técnica)* | Infraestructura: canal WebSocket por `sesion_id` (`CanalTiempoRealPort`), autenticación JWT sobre WS por query param, `ComisionConsultaPort` nuevo (Actividad Evaluativa → Identidad) para resolver `materia_id` desde `comision_id` (§16, §17 punto 11) | — (sin comando de negocio propio) | — | — | [#382](https://github.com/vvalotto/cognion/issues/382) |
| **US-6.1.2** | Docente crea una sesión en vivo desde el detalle de una Comisión | `CrearSesionEnVivo(comision_id, unidad_tematica?, tema?, cantidad_preguntas, tiempo_limite_por_pregunta_segundos)` → `SesionEnVivoCreada` | Docente | INV-AEV-01, INV-AEV-02 | [#383](https://github.com/vvalotto/cognion/issues/383) |
| **US-6.1.3** | Estudiante se une a la sesión (sala de espera o unión tardía ya `EnCurso`) | `UnirseASesionEnVivo(sesion_id, estudiante_id)` → `EstudianteUnido` | Estudiante | INV-AEV-06 (idempotente) | [#384](https://github.com/vvalotto/cognion/issues/384) |
| **US-6.1.4** | Docente inicia la sesión — se presenta el enunciado de la primera pregunta | `IniciarSesionEnVivo(sesion_id)` → `SesionEnVivoIniciada` | Docente | — | [#385](https://github.com/vvalotto/cognion/issues/385) |

**Orden de implementación:** US-6.1.1 primero (bloquea todo el resto). US-6.1.2 antes que
US-6.1.3/US-6.1.4 (no se puede unir ni iniciar una sesión que no existe).

Specs en `docs/specs/inc6/US-6.1.1.md` a `US-6.1.4.md`.

## Iteración 2 — RF-09, RF-10: dinámica en tiempo real, ranking, cálculo de puntaje

Backend únicamente — mismo criterio de diferir frontend que la Iteración 1 (el frontend del modo
en vivo todavía no tiene iteración asignada). Alcance: todo lo que sigue a `SesionEnVivoIniciada`
— mostrar opciones, responder con puntaje server-side, cerrar (respuesta correcta + histograma +
ranking), avanzar, finalizar, consultas de estado/ranking para reconexión, y la **verificación**
del RNF de rendimiento y de la sesión completa.

Decisiones de Víctor (2026-09-19, al especificar la iteración): read models como **tablas
propias** (modelo §15, no query sobre `events`); incluir la US de consultas/reconexión (`6.2.8`);
la medición del RNF va como **US de verificación propia** (`6.2.9`).

| US | Tipo | Comando/Evento | Actor | Invariantes | Issue |
|---|---|---|---|---|---|
| **US-6.2.1** *(técnica)* | Cálculo de puntaje server-side (fórmula del spike RF-10) + dificultad/importancia por `PreguntaConsultaPort` | — (servicio de dominio puro) | — | — | [#392](https://github.com/vvalotto/cognion/issues/392) |
| **US-6.2.2** | Docente muestra las opciones de la pregunta actual (arranca el temporizador) | `MostrarOpcionesDeLaPregunta(sesion_id)` → `OpcionesEnVivoMostradas` | Docente | INV-AEV-09 (parte) | [#393](https://github.com/vvalotto/cognion/issues/393) |
| **US-6.2.3** *(técnica)* | Read models `ranking_por_sesion` y `distribucion_por_pregunta` (tablas + migración, atómicos con el evento) | — | — | contrato de atomicidad evento + proyección | [#394](https://github.com/vvalotto/cognion/issues/394) |
| **US-6.2.4** | Estudiante responde una pregunta (un intento, tiempo medido por el servidor, feedback personal) | `ResponderPreguntaEnVivo(...)` → `RespuestaEnVivoRegistrada` | Estudiante | INV-AEV-07/08/09 | [#395](https://github.com/vvalotto/cognion/issues/395) |
| **US-6.2.5** | Docente cierra la pregunta: respuesta correcta + histograma + ranking (RNF ≤100 ms) | `CerrarPreguntaActual(sesion_id)` → `PreguntaEnVivoCerrada` | Docente | INV-AEV-09 (parte) | [#396](https://github.com/vvalotto/cognion/issues/396) |
| **US-6.2.6** | Docente avanza a la siguiente pregunta | `AvanzarSiguientePregunta(sesion_id)` → `SiguientePreguntaPresentada` | Docente | INV-AEV-03 | [#397](https://github.com/vvalotto/cognion/issues/397) |
| **US-6.2.7** | Docente finaliza la sesión: ranking final | `FinalizarSesionEnVivo(sesion_id)` → `SesionEnVivoFinalizada` | Docente | INV-AEV-03 | [#398](https://github.com/vvalotto/cognion/issues/398) |
| **US-6.2.8** | Consultar estado de la sesión, participantes y ranking (reconexión, ranking final del Estudiante) | queries — sin comando ni evento | Docente / Estudiante | — | [#399](https://github.com/vvalotto/cognion/issues/399) |
| **US-6.2.9** *(verificación)* | Sesión completa por la API real + medición del RNF (p95 ≤100 ms, 60 participantes) + revisión manual | — | Docente | — | [#400](https://github.com/vvalotto/cognion/issues/400) |

**Orden de implementación:** `6.2.1` y `6.2.3` primero (bases técnicas, independientes entre sí) →
`6.2.2` → `6.2.4` (necesita 1, 2 y 3) → `6.2.5` → `6.2.6` → `6.2.7` → `6.2.8` (necesita 3 y 7) →
`6.2.9` (cierra la iteración).

**Riesgos técnicos identificados al especificar** (resueltos como diseño en cada spec, no como
decisión abierta):
- `SQLAlchemyEventStore.append` hace `commit` sobre la sesión: la proyección se escribe **antes**
  del `append` y queda pendiente en la misma sesión, así el `commit` confirma ambas (`6.2.3`).
- 60 alumnos incrementando el mismo contador del histograma → `UPDATE` atómico en la base
  (`ON CONFLICT DO UPDATE SET cantidad = cantidad + 1`), nunca leer-modificar-escribir (`6.2.3`).
- `SesionesEnVivoController` ya tiene 3 use cases: separar por responsabilidad al acercarse al
  umbral de CBO (comandos / respuestas / consultas).
- El RNF se mide en una máquina local con conexiones simuladas: es una cota de referencia, no una
  garantía del despliegue final (`6.2.9`).

**Ítems abiertos que esta iteración deja para el frontend** (no bloquean el backend):
- Nombres de los estudiantes en la sala de espera y el ranking: hoy solo viajan `estudiante_id`.
  Resolver nombres requiere un puerto nuevo Actividad Evaluativa → Identidad.
- Confirmar con Víctor si `FinalizarSesionEnVivo` exige que sea la última pregunta o admite
  finalizar antes (`US-6.2.7`, decisión de spec: sin esa restricción, el modelo no la lista).

Specs en `docs/specs/inc6/US-6.2.1.md` a `US-6.2.9.md`.

**Hito del incremento:** el docente conduce una sesión en vivo completa en el aula, con
ranking actualizado en tiempo real dentro del umbral de ≤100ms server-side acordado en RNF.
