# US-6.3.10: Verificación del modo en vivo en navegador real (proyección + celulares)

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-6.3`
**Tipo**: `verificación` (UAT — sin código de producción)
**Agregado principal afectado**: — (recorre el modo en vivo de punta a punta, backend + frontend)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **conducir una sesión en vivo real con la pantalla de proyección y varios celulares**,
para **confiar en usarla en el aula frente a mis alumnos**.

---

## Contexto del dominio

### Problema

Cierra la Iteración 3 y el **hito del Incremento 6**: "el docente conduce una sesión en vivo completa en el aula".
`US-6.2.9` lo verificó por API y WebSocket; falta verlo **en navegador real**, donde viven los defectos que Vitest con
`WebSocket` falso no ve (precedentes: CORS y cascada CSS en `US-1.1.9`; el `AbortController` y `StrictMode` de
`US-ADJ-20`; `localhost` vs. IP de la red). Por el gate de diseño de `CLAUDE.md`, la **legibilidad en proyección y el uso
con el pulgar** se validan **en el dispositivo real**, no solo en un navegador de escritorio.

Sigue el criterio de Víctor (Incremento 4): **una sola pasada al cierre de la iteración**, no US por US.

### Qué se verifica

| Eje | Cómo | Criterio |
|---|---|---|
| **Sesión completa** | Un Docente (proyección a 1920×1080) y ≥ 3 Estudiantes (pestañas emuladas de móvil 375×812) recorren ≥ 3 preguntas: mostrar → responder → cerrar → histograma → ranking → avanzar → finalizar | Cada paso funciona; cada pantalla pasa sola a la siguiente; el podio final coincide con los puntajes |
| **V/F y 3 opciones** | Sesión con preguntas de esos tipos (hay en el banco real de Gestión de Proyectos) | Se ven y responden bien |
| **Legibilidad en proyección (§1.1)** | Medición en el navegador de tamaños y contraste de las pantallas `stage-*` | Pregunta ≥ 40 px; temporizador y opciones ≥ 26 px; eyebrow ≥ 18-20 px; contraste ≥ 7:1; sin scroll |
| **Reconexión** | Cortar la red de un Estudiante con la pregunta abierta y de la proyección del Docente en el histograma; restablecer | Recuperan etapa, tiempo restante y avance; la participación no se pierde; el indicador "Reconectando…" aparece y desaparece |
| **Recarga (F5)** | En cada etapa del Docente y del Estudiante | Vuelve a la misma etapa con los datos correctos |
| **Un solo intento / respuesta tardía** | Doble toque; toque con el tiempo vencido | Un solo envío; mensaje claro de tiempo agotado |
| **`StrictMode` en `npm run dev`** | Recorrer el flujo en modo desarrollo | El canal no se abre/cierra en bucle ni pierde mensajes (lección `US-ADJ-20`) |
| **Dispositivo real** | ≥ 1 **celular real** en la misma red (frontend con `--host`, backend accesible por IP) y la proyección en un monitor/proyector | Objetivos táctiles ≥ 44 px, colores distinguibles a distancia, texto legible |
| **Rendimiento percibido** | Con los celulares reales | El ranking aparece < 1 s desde el cierre (RNF Rendimiento) |
| **Regresión** | Suite completa + `oxlint` + `tsc -b` | Sin regresiones sobre el resto del sistema |

### Alcance (honestidad del método)

- Entorno propio (máquina de desarrollo). **El checkpoint de staging** (Fly.io, WSS real detrás de un proxy,
  `PROCEDIMIENTO-UAT.md` §4) **sigue pendiente** y no lo reemplaza esta US.
- La cantidad de dispositivos reales limita la carga: el RNF de 60 concurrentes ya se midió en `US-6.2.9` con
  conexiones simuladas; acá se verifica la **experiencia**, no la carga.

---

## Especificacion del comportamiento

### Precondicion

- `US-6.3.0` a `US-6.3.9` cerradas.

### Postcondicion

- Existen: guion de la revisión manual, diseño y evidencia de la UAT (`quality/reports/uat/inc6/design-iteracion3.md`,
  `evidencia-iteracion3.md`) y la plantilla de hallazgos.
- **Víctor valida en persona** (proyección + celular real). Cualquier 🔴 Bloqueante frena el cierre de la iteración;
  los 🟡/🟢 se registran (severidades en `docs/plans/PROCEDIMIENTO-UAT.md` §8).
- Con la validación, RF-08/09/10 quedan listos para **Validado** en el cierre de baseline `BL-011`
  (`docs/traceability/matrix.md` **no** se toca antes).

### Regla de clasificación de hallazgos (`CLAUDE.md`)

Hallazgo que **solo toca `frontend/`** → track informal. Si al resolverlo la primera acción es abrir `src/` → track
formal (US-IEDD + spec + `/implement-us`).

---

## Criterios de aceptacion

```gherkin
Feature: Verificación del modo en vivo en navegador real (US-6.3.10)

  Scenario: Sesión completa con proyección y celulares
    Given un Docente con la proyección y tres Estudiantes conectados
    When se recorren tres preguntas completas y se finaliza
    Then cada paso funciona, cada pantalla avanza sola y el podio coincide con los puntajes

  Scenario: Legibilidad de la proyección
    Given las pantallas de proyección abiertas a 1920x1080
    When se miden los tamaños de fuente y el contraste
    Then cumplen los criterios de legibilidad del wireframe

  Scenario: Reconexión de un celular
    Given un Estudiante con la pregunta abierta y la red cortada
    When se restablece la red
    Then recupera la pregunta, el tiempo restante y su avance

  Scenario: Recarga en cualquier etapa
    Given cada etapa de la proyección y del celular
    When se recarga la pantalla
    Then vuelve a la misma etapa con los datos correctos

  Scenario: Modo desarrollo sin bucles
    Given el frontend en npm run dev
    When se recorre el flujo
    Then el canal no se abre y cierra en bucle

  Scenario: Celular real
    Given un celular real en la misma red y la proyección en un monitor
    When Víctor conduce una sesión
    Then valida que se lee y se toca bien

  Scenario: Aprobación
    Given la evidencia y los hallazgos de la UAT
    When Víctor los revisa
    Then confirma en el Issue #421 que no hay hallazgos bloqueantes
```

---

## Impacto arquitectonico

- [ ] No — verificación. Si aparece un defecto de `src/`, se abre una `US-ADJ` por el track formal.

**Capa(s) afectadas:** ninguna (sin código de producción).

---

## Fuente de verdad UX

- `docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` (incluida la sección de ampliaciones de `US-6.3.0`) y su prototipo, contra los cuales se compara lo implementado.

---

## Artefactos a crear

| Artefacto | Contenido |
|---|---|
| `tests/uat/inc6/guion_manual_iteracion3.md` | Guion paso a paso (URLs, cuentas, qué mirar en cada pantalla, cómo cortar la red) |
| `tests/uat/inc6/sembrar_sesion_en_vivo.sh` (o `.py`) | Siembra Docente, Comisión, Estudiantes y un banco con preguntas de opción múltiple, V/F y 3 opciones |
| `quality/reports/uat/inc6/design-iteracion3.md`, `evidencia-iteracion3.md`, `hallazgos-revision-manual-iteracion3.md` | Diseño, evidencia y hallazgos |

---

## Referencias

- Procedimiento: `docs/plans/PROCEDIMIENTO-UAT.md` (§3 capas, §4 staging, §8 severidades)
- Precedentes: `US-6.2.9`, `quality/reports/uat/inc6/`, UAT de las iteraciones con frontend de los Incrementos 2 y 4
- Lecciones: `US-1.1.9` (CORS/CSS), `US-ADJ-20` (`StrictMode`)
- Depende de: `US-6.3.0` a `US-6.3.9`
- Cierra: Iteración 3 del Incremento 6

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
