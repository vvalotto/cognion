# Incremento 6 — Sesión en Vivo — US candidatas

> Estado documental: **Iteración 0 — Modelado en curso.** Spike del algoritmo de puntaje
> (RF-10) resuelto con Víctor 2026-09-17 (detalle más abajo). Event storming y wireframes
> todavía no arrancados. Milestone
> [`Incremento 6 — Sesión en Vivo`](https://github.com/vvalotto/cognion/milestone/8) (abierto,
> vacío).
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

Sin especificar todavía — depende del cierre de la Iteración 0.

## Iteración 2 — RF-09, RF-10: dinámica en tiempo real, ranking, cálculo de puntaje

Sin especificar todavía — depende del cierre de la Iteración 0 y de la Iteración 1
(infraestructura WebSockets).

**Hito del incremento:** el docente conduce una sesión en vivo completa en el aula, con
ranking actualizado en tiempo real dentro del umbral de ≤100ms server-side acordado en RNF.
