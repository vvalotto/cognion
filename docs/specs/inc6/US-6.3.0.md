# US-6.3.0: Ampliación de wireframes y prototipo del modo en vivo

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-6.3`
**Tipo**: `UX` (gate de diseño — sin código de producción)
**Agregado principal afectado**: — (artefactos de diseño)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Docente (dueño de producto)**,
quiero **aprobar las pantallas y estados que los wireframes de la Iteración 0 no cubrían**,
para **que ninguna línea de frontend del modo en vivo se escriba sobre un diseño que no aprobé**.

---

## Contexto del dominio

### Problema

`docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` fue aprobado el 2026-09-17 (12 pantallas). Al
especificar el frontend contra el backend real (`US-6.1.x`, `US-6.2.x`) aparecieron **huecos**: casos que el
backend admite y las pantallas aprobadas no resuelven. Por el gate de diseño de `CLAUDE.md` ("ninguna línea
de `frontend/` sin artefacto aprobado") esos huecos se cierran **antes** de `US-6.3.5` a `US-6.3.9`, no se
resuelven a ojo al codear (anti-patrón "spec-validatoria" que ya costó una US revertida en AtaraxiaDive).

### Huecos a resolver (propuesta de partida — Víctor decide)

| # | Hueco | Por qué es un hueco | Propuesta de partida |
|---|---|---|---|
| H1 | **Preguntas Verdadero/Falso** | El prototipo solo dibuja 4 opciones. El banco real tiene V/F (`tipo = verdadero_falso`, `opciones = null`, respuesta `{valor: bool}`); en `preguntas_gestion.json` son 5 de 36 | 2 tarjetas/cajas grandes "Verdadero" y "Falso", con los colores `b` (azul) y `c` (amarillo) — **no** rojo/verde, para no sugerir cuál es la correcta |
| H2 | **Preguntas con 3 opciones** | El backend exige ≥ 2 opciones y **no fija un máximo**; el banco real tiene 10 de 36 con 3 | N opciones (2 a 4) toman los colores `a`, `b`, `c`, `d` en orden; con 3, la tercera ocupa el ancho completo de la grilla. Más de 4: los colores se repiten cíclicamente (caso no presente en los datos reales, se documenta) |
| H3 | **Pantalla del Estudiante entre "pregunta presentada" y "opciones mostradas"** | §3.3 arranca con las opciones ya visibles; `§3.1` menciona "una pantalla de espera si está entre preguntas" sin dibujarla | `#est-espera-opciones`: "Pregunta N de total" + enunciado + "Esperá a que el Docente muestre las opciones" |
| H4 | **Estudiante que no respondió y la pregunta se cerró** | Sin `#est-esperando` (eliminada en la 4ª ronda) no hay pantalla para quien dejó pasar la pregunta | `#est-sin-respuesta`: "Se cerró la pregunta — no respondiste (+0)" con el acumulado propio, hasta la siguiente pregunta o el final |
| H5 | **Tiempo agotado al tocar** | §3.3 menciona el 422 `TiempoAgotado` sin pantalla | Mismo `#est-sin-respuesta`, con el mensaje "Se acabó el tiempo antes de tu respuesta" |
| H6 | **Recuperar una sesión ya creada (Docente)** | La sesión solo se llega a ver justo después de crearla; si el Docente cierra la pestaña o se cae el navegador no hay forma de volver | En el detalle de la Comisión (`ComisionDetalleDocente`), bloque "Sesiones en vivo activas" con "Continuar" (a la sala si `EnEspera`, a la proyección si `EnCurso`) |
| H7 | **Salida de la pantalla terminal** | §2.7 dice "sin acción, pantalla terminal": el Docente queda sin forma de salir de la proyección | Enlace discreto "Volver a la Comisión" (fuera del foco visual, no forma parte de lo que ve el aula) |
| H8 | **Estado de conexión** | Ninguna pantalla dice qué ve el usuario si se cae el WebSocket | Indicador discreto "Reconectando…" (Docente y Estudiante) que desaparece al recuperar; nunca bloquea ni oculta la pantalla |
| H9 | **Sin participantes / menos de 3** | §2.6/§2.7 asumen un Top 3 completo | Se muestran tantos puestos como participantes haya; con 0: "Nadie participó" |

Las decisiones **ya tomadas con Víctor** (2026-09-21, al especificar la iteración) no se reabren:
- El **ranking muestra Top 3 en todas las pantallas** (proyección y resultado final); el Estudiante ve además su posición exacta.
- Los **nombres** de los Estudiantes los agrega el backend (`US-6.3.1`).

---

## Especificacion del comportamiento

### Postcondicion

- `wireframes-actividad-evaluativa-en-vivo.md` gana la sección **§6 "Ampliaciones de la Iteración 3"** con una
  subsección por hueco (H1 a H9): actor, elementos, transiciones y estados de error.
- `prototipos/actividad-evaluativa-en-vivo.html` incorpora las pantallas nuevas navegables
  (`#est-espera-opciones`, `#est-sin-respuesta`, variante V/F y de 3 opciones de `#est-pregunta` y
  `#stage-pregunta-opciones`, bloque de sesiones activas en el detalle de Comisión) sin alterar las 12
  aprobadas.
- Víctor **aprueba explícitamente** en el comentario de cierre del Issue #422, incluida la validación de
  legibilidad **en el dispositivo real** (celular y proyector) que exige el gate para este escenario.

### Restricciones

- No se modifican las decisiones de las seis rondas de la Iteración 0.
- Los criterios de legibilidad de §1.1 aplican a toda pantalla `stage-*` nueva o variante.

---

## Criterios de aceptacion

```gherkin
Feature: Ampliación de wireframes del modo en vivo (US-6.3.0)

  Scenario: Cada hueco tiene su resolución documentada
    Given los huecos H1 a H9 de esta spec
    When se revisa la sección "Ampliaciones de la Iteración 3" del documento de wireframes
    Then cada hueco tiene actor, elementos, transiciones y estados de error

  Scenario: El prototipo cubre las pantallas nuevas
    Given el prototipo HTML actualizado
    When se navega por las pantallas nuevas
    Then se ven V/F, 3 opciones, espera de opciones, sin respuesta y sesiones activas

  Scenario: Las pantallas aprobadas no cambian
    Given las 12 pantallas aprobadas el 2026-09-17
    When se compara el prototipo actualizado
    Then ninguna cambió salvo lo agregado por esta US

  Scenario: Aprobación en el dispositivo real
    Given el prototipo actualizado abierto en un celular y en un proyector
    When Víctor lo revisa
    Then aprueba explícitamente en el Issue #422
```

---

## Impacto arquitectonico

- [ ] No — solo artefactos de diseño.

**Capa(s) afectadas:** ninguna (sin `src/` ni `frontend/`).

---

## Fuente de verdad UX

Esta US **produce** la fuente de verdad ampliada. Punto de partida:
`docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` (§1 a §5) y
`docs/design/ux/prototipos/actividad-evaluativa-en-vivo.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` | §6 "Ampliaciones de la Iteración 3" (H1 a H9) |
| `docs/design/ux/prototipos/actividad-evaluativa-en-vivo.html` | Pantallas y variantes nuevas |

---

## Referencias

- Wireframes vigentes: `docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md`
- Gate de diseño: `CLAUDE.md` §"Gate de diseño UX"
- Bloquea a: `US-6.3.5` a `US-6.3.9`
- Candidatas: `docs/plans/inc6/inc6-candidatas.md` §Iteración 3

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
