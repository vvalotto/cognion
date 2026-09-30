# US-6.3.8: Estudiante ve las sesiones disponibles, se une y espera en la sala

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-6.3`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (consume `ListarSesionesEnVivo` y `UnirseASesionEnVivo`)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Estudiante**,
quiero **ver si hay una sesión en vivo de mi Comisión, unirme y esperar a que empiece**,
para **entrar a la dinámica desde mi celular sin que nadie me pase un enlace**.

---

## Contexto del dominio

### Problema

Cubre `§3.1 #est-sesiones` y `§3.2 #est-sala-espera`. Esta US crea el **contenedor**
`SesionEnVivoEstudiante` (ruta `/mis-sesiones-en-vivo/:sesionId`) con su máquina de etapas y las dos primeras;
`US-6.3.9` agrega la pregunta, el resultado y el final **sobre el mismo contenedor**.

### Sesiones disponibles (§3.1, confirmado con Víctor)

- **No hay pantalla ni ítem de menú aparte:** las sesiones aparecen **en la pantalla donde el Estudiante ya ve las
  actividades de período abierto de su materia** (`MisActividades.tsx`, `/mis-actividades/materias/:materiaId/actividades`),
  junto a esas actividades, distinguidas por su propio `Badge` de estado.
- Datos: `listarSesionesEnVivo` (`US-6.3.2`, la Comisión sale del backend), filtradas por la `materiaId` de la pantalla.
- **Tarjetas:** Materia, cantidad de preguntas, `Badge` (`En espera` / `En curso`).
- **Se refresca sola:** al montar y cada **10 s** mientras la pantalla está visible (`setInterval` dentro de un
  `useEffect` con cleanup). Sin WebSocket aquí: el canal necesita un `sesion_id` y todavía no se conoce.
- Sin sesiones: estado vacío ("Por ahora no hay sesiones en vivo"). Las `Finalizada` no se listan.
- Tap en una tarjeta → `unirseASesion` → navega a `/mis-sesiones-en-vivo/:sesionId`. **`En espera`** y **`En curso`**
  usan el mismo comando (unión tardía, hot spot 2 confirmado); el contenedor decide la etapa según el estado.
  `422 SesionYaFinalizada` → mensaje y refresca la lista. `404` → mensaje y refresca.

### `#est-sala-espera` (§3.2)

- **"¡Te uniste!"** (feedback de `EstudianteUnido`), **cantidad de participantes** (mismo dato que ve el Docente, en vivo con
  `participantes_actualizados`) y el mensaje de mirar la proyección.
- **Transición automática** al recibir el primer `pregunta_presentada` — **sin botón** (el prototipo usa un botón
  deshabilitado como placeholder de esa espera). En esta US esa transición lleva a una etapa provisional; la real llega con `US-6.3.9`.
- Idempotencia: recargar la pantalla vuelve a llamar a `unirseASesion` (reunión idempotente del servidor, INV-AEV-06) y
  luego a `GET estado`; **no se guarda en el cliente que "ya se unió"**.

### Etapas del contenedor (al montar y en cada `onReconectado`, con `GET estado`)

| Estado del servidor | Etapa |
|---|---|
| `EnEspera` | `#est-sala-espera` |
| `EnCurso` | etapas de pregunta (**`US-6.3.9`**) |
| `Finalizada` | resultado final (**`US-6.3.9`**) |

---

## Especificacion del comportamiento

### Precondicion

- `US-6.3.2`, `US-6.3.4` cerradas; `US-6.3.0` (H8, indicador de conexión).

### Postcondicion

- El Estudiante descubre su sesión, se une y ve la sala; pasa solo a la pregunta cuando el Docente inicia.

---

## Criterios de aceptacion

```gherkin
Feature: Estudiante ve sesiones, se une y espera (US-6.3.8)

  Scenario: Las sesiones aparecen junto a las actividades de la materia
    Given una sesión EnEspera de la Comisión del Estudiante
    When el Estudiante abre las actividades de su materia
    Then ve la tarjeta de la sesión con su Badge "En espera"

  Scenario: Solo sesiones de su materia
    Given una sesión de otra materia de la misma Comisión
    When el Estudiante abre las actividades de su materia
    Then no aparece

  Scenario: Sin sesiones
    Given ninguna sesión activa
    When el Estudiante abre la pantalla
    Then ve el estado vacío

  Scenario: El listado se refresca solo
    Given la pantalla abierta sin sesiones
    When el Docente crea una sesión
    Then aparece en menos de 10 segundos sin recargar

  Scenario: Unirse a una sesión en espera
    Given la tarjeta de una sesión EnEspera
    When el Estudiante la toca
    Then se une y ve "¡Te uniste!" con la cantidad de participantes

  Scenario: Unión tardía a una sesión en curso
    Given una sesión EnCurso
    When el Estudiante la toca
    Then se une y entra a la etapa de la pregunta actual

  Scenario: El conteo de la sala es en vivo
    Given el Estudiante en la sala de espera
    When otro Estudiante se une
    Then el conteo aumenta sin recargar

  Scenario: Pasa solo a la pregunta cuando el Docente inicia
    Given el Estudiante en la sala de espera
    When llega pregunta_presentada
    Then sale de la sala sin tocar nada

  Scenario: Sesión ya finalizada
    Given una tarjeta que quedó vieja y la sesión ya finalizó
    When el Estudiante la toca
    Then ve el mensaje y la lista se refresca

  Scenario: Recargar la sala
    Given el Estudiante en la sala de espera
    When recarga la pantalla
    Then vuelve a la sala sin perder su participación
```

---

## Impacto arquitectonico

- [ ] No.

**Capa(s) afectadas:** [x] Frontend (sin cambios de `src/`).

**Calidad (frontend):** `oxlint`, `tsc -b`, cobertura ≥ 80%; `vi.useFakeTimers()` para el refresco de 10 s; cleanup del intervalo verificado (lección `US-ADJ-20`).

---

## Fuente de verdad UX

- `docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` §3.1 (`#est-sesiones`), §3.2 (`#est-sala-espera`).
- Prototipo: `#est-sesiones`, `#est-sala-espera`.
- Pantalla existente: `frontend/src/pages/actividad-evaluativa/MisActividades.tsx` y `wireframes-actividad-evaluativa.md` §3.
- **`US-6.3.0`** H8 (indicador de conexión).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/pages/actividad-evaluativa/MisActividades.tsx` (+ test) | Bloque de sesiones en vivo con refresco |
| `frontend/src/pages/actividad-evaluativa/SesionEnVivoEstudiante.tsx` (+ test) | Contenedor y máquina de etapas (nuevo) |
| `frontend/src/pages/actividad-evaluativa/estudiante/SalaEsperaEstudiante.tsx` (+ test) | Etapa (nueva) |
| `frontend/src/router.tsx` | Reemplaza el placeholder de `/mis-sesiones-en-vivo/:sesionId` |

---

## Referencias

- Wireframes: `wireframes-actividad-evaluativa-en-vivo.md` §3.1, §3.2
- Backend: `US-6.1.3` (unirse), `US-6.3.2` (listar), `US-6.2.8` (estado)
- Depende de: `US-6.3.2`, `US-6.3.4`, `US-6.3.0`
- Consumida por: `US-6.3.9`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
