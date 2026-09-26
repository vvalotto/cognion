# US-ADJ-57: Cada Docente ve y opera solo sobre las materias de sus Comisiones

**Estado**: `Especificada`
**Iteracion / Sprint**: sin asignar — se implementa **después** del cierre de `BL-011` (decisión de Víctor, 2026-09-25)
**Tipo**: `feat` backend + frontend (autorización)
**Agregado principal afectado**: ninguno nuevo (la asignación Docente ↔ Comisión ya existe en Identidad, `comision_docentes`)
**Bounded Context**: transversal — Banco de Preguntas, Identidad, Actividad Evaluativa, Analytics
**Origen**: validación manual de `US-6.3.10` (2026-09-25): logueado como `valid-docente`, Víctor ve en Banco de
Preguntas la materia "Ingeniería de Software", que no tiene asignada.

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **ver y operar solo sobre las materias de las Comisiones que tengo asignadas**,
para **no ver ni modificar el trabajo ni los datos de estudiantes de otros Docentes**.

---

## Contexto del dominio

### Problema

El sistema nació con **un único Docente** (`CLAUDE.md`, "Docente único"): ningún endpoint filtra por la asignación
Docente ↔ Comisión. Desde el autoregistro de Docentes (`RF-25`, Incremento 5-ADJ) puede haber varios, y hoy
cualquier Docente:

- ve todas las materias activas (`GET /materias`, `ListarMateriasUseCase`) y, con ellas, carga, edita y elimina
  preguntas de bancos ajenos;
- ve las Comisiones de cualquier materia, sus estudiantes y genera invitaciones;
- crea y conduce actividades de período abierto y sesiones en vivo en Comisiones ajenas (ítem abierto "sin
  ownership de sesión" del Incremento 6);
- consulta los reportes de Analytics de cualquier materia, con datos de estudiantes de otro Docente.

### Regla (decisión de Víctor, opción a)

**Un Docente ve y opera solo sobre las materias en las que está asignado a al menos una Comisión, y dentro de ellas
solo sobre sus Comisiones.** El **Administrador** sigue viendo y gestionando todo (sin cambios). El **Estudiante** no
cambia (ya está acotado a su propia Comisión).

| Recurso | Docente asignado | Docente no asignado |
|---|---|---|
| Materia en listados (`GET /materias` y selectores) | aparece | no aparece |
| Banco de la materia: ver, cargar, editar, eliminar preguntas | permitido | `403` |
| Comisiones de la materia, detalle, estudiantes, invitaciones | solo **sus** Comisiones | `403` |
| Actividades de período abierto: listar, crear, detalle, modificar, cerrar | permitido en su materia; restricción a Comisiones ajenas `403` | `403` |
| Sesiones en vivo: crear, listar, conducir | solo en **sus** Comisiones | `403` |
| Reportes de Analytics (RF-16, RF-17, RF-20 a RF-23) | solo de su materia y **sus** Comisiones | `403` |

**Materia sin Comisiones o con Comisiones sin Docente asignado:** solo la ve el Administrador (la da de alta y
asigna Docentes, `PR #370`).

### Modelo involucrado (propuesta, se confirma en la Fase 2)

| Elemento | Responsabilidad |
|---|---|
| Identidad | Fuente de verdad de la asignación: consulta "¿el Docente X está asignado a la Comisión Y?" y "materias / Comisiones del Docente X" |
| Puertos por BC (`ADR-006`, in-process) | Cada BC amplía **su** `ComisionConsultaPort` hacia Identidad (ya existen en Banco de Preguntas, Actividad Evaluativa y Analytics) con la consulta de asignación — sin imports directos entre BCs |
| Autorización | En los use cases o en el borde HTTP de cada BC, según el patrón que se elija en la Fase 2; **un solo criterio para todos los BCs** |
| Frontend | Los listados muestran solo lo permitido (sale solo del backend); un `403` inesperado muestra el mensaje de acceso denegado existente |

---

## Especificacion del comportamiento

### Precondicion

- `BL-011` cerrada (Incremento 6).

### Postcondicion

- La regla de la tabla se cumple en los 4 BCs, verificada por tests de integración con **dos Docentes** asignados a
  Comisiones de materias distintas.
- El Administrador no pierde ninguna capacidad.
- Los circuitos E2E del modo en vivo (`US-6.3.10`) siguen en verde.

### Alcance y partición

Toca muchos endpoints: en la Fase 2 se decide si se implementa como **una US por BC** (recomendado: Identidad +
Banco de Preguntas, Actividad Evaluativa, Analytics), compartiendo la regla y los tests con dos Docentes.

---

## Criterios de aceptacion

```gherkin
Feature: Cada Docente opera solo sobre sus materias (US-ADJ-57)

  Background:
    Given el Docente A asignado a una Comisión de "Ingeniería de Software"
    And el Docente B asignado a una Comisión de "Gestión de Proyectos"

  Scenario: Solo ve sus materias
    When el Docente A abre el listado de materias
    Then ve "Ingeniería de Software" y no ve "Gestión de Proyectos"

  Scenario: No puede tocar un banco ajeno
    When el Docente A intenta cargar o editar una pregunta del banco de "Gestión de Proyectos"
    Then recibe 403 y el banco no cambia

  Scenario: Solo ve sus Comisiones
    Given el Docente A también ve una segunda Comisión de "Ingeniería de Software" a la que no está asignado
    When abre las Comisiones de la materia
    Then solo ve la suya

  Scenario: No puede crear una sesión en vivo en una Comisión ajena
    When el Docente A intenta crear una sesión en vivo en la Comisión del Docente B
    Then recibe 403

  Scenario: No ve reportes de otra materia
    When el Docente A pide un reporte de Analytics de "Gestión de Proyectos"
    Then recibe 403

  Scenario: El Administrador ve todo
    When el Administrador abre el listado de materias y de Comisiones
    Then ve ambas materias y todas sus Comisiones

  Scenario: Materia recién creada sin Docente
    Given una materia sin Comisiones con Docente asignado
    When cualquier Docente abre el listado de materias
    Then no aparece
```

---

## Impacto arquitectonico

- [x] Sí — consulta de asignación en Identidad y ampliación de los `ComisionConsultaPort` de Banco de Preguntas,
  Actividad Evaluativa y Analytics. Sin tablas ni eventos nuevos. Riesgo conocido: **CBO** en controllers y use
  cases al sumar dependencias (patrón ya visto en los Incrementos 2 y 6) — diseñar la separación desde la Fase 2.

---

## Decisiones abiertas (para la Fase 2, con Víctor)

1. `403` o `404` para recursos ajenos (`404` no revela que existen). Esta spec propone **`403`**, consistente con el resto del sistema.
2. Actividades de período abierto **sin** restricción de Comisión (aplican a toda la materia): ¿las ve y las modifica
   cualquier Docente asignado a alguna Comisión de la materia? Esta spec propone **sí**.
3. Datos ya existentes creados por un Docente en materias que no tiene asignadas (por ejemplo, en la prueba de
   estabilización): ¿se migran o se dejan? No se borra nada.

---

## Fuente de verdad UX

- No hay pantallas nuevas: los listados existentes muestran menos elementos. Sin gate UX, salvo que la Fase 2
  detecte un estado vacío nuevo ("Todavía no tenés materias asignadas").

---

## Referencias

- `CLAUDE.md` ("Docente único"; ítem abierto "sin ownership de sesión", Incremento 6)
- `RF-25` (autoregistro de Docente), `PR #370` (alta de Materia exclusiva del Administrador)
- Puertos existentes: `ComisionConsultaPort` en `banco_preguntas`, `actividad_evaluativa`, `analytics`
- Origen: validación manual de `US-6.3.10`
