# US-ADJ-02: Unidad temática y Tema como lista seleccionable derivada del banco actual

**Estado**: `Especificada`
**Iteracion / Sprint**: `SP-ADJ` (sin incremento asignado todavía — ver `HITO-5`)
**Tipo**: `refactor frontend`
**Agregado principal afectado**: — (sin cambios de dominio ni de contrato de API, solo del control de entrada en el cliente)
**Bounded Context**: Banco de Preguntas (frontend)

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **elegir la Unidad temática y el Tema de una lista de valores ya usados en el banco de
esa materia, en vez de escribirlos siempre a mano**
para **evitar que un typo (p. ej. "Unidad 2" vs "Unidad  2") fragmente el filtrado del banco
(`US-2.1.7`/`US-2.1.10`) y agrupe mal preguntas que deberían quedar juntas**.

---

## Contexto del dominio

### Problema

Detectado en el UAT manual de cierre de la Iteración 1 (`HITO-5`,
`quality/reports/uat/inc2/evidencia.md`): `NuevaPreguntaOpcionMultiple.tsx`,
`NuevaPreguntaVerdaderoFalso.tsx` y `EditarPregunta.tsx` cargan Unidad temática y Tema como
`Input` de texto libre. El wireframe aprobado (`wireframes-banco-preguntas.md` §2.5) ya
especificaba Unidad temática como `select`; se implementó como texto libre por una decisión
documentada en `CLAUDE.md` (cierre de `US-2.1.11`): no existe catálogo ni endpoint de origen
para esos valores.

Esa decisión sigue siendo válida — no se agrega un catálogo nuevo en el backend. Lo que
cambia es el origen de las opciones: se derivan del banco actual, no de un catálogo.

### Modelo involucrado

Sin cambios de dominio, de Aggregate ni de contrato de API — `unidad_tematica` y `tema` siguen
siendo `str` libres en el backend (`CargarPreguntaOpcionMultiple`/`VerdaderoFalso`,
`EditarPregunta`). El cambio es exclusivamente de UI: el campo de texto se comporta como
combobox (lista + posibilidad de escribir un valor nuevo), con las opciones derivadas
client-side de `GET /bancos/{id}/preguntas` (ya se consume en `Banco.tsx` y puede reusarse o
volver a pedirse desde las pantallas de carga/edición).

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Componente nuevo | `Combobox` (o extensión de `Input` con `datalist`) | Campo de texto que sugiere valores ya usados en el banco, pero acepta un valor nuevo |
| Fuente de datos | `GET /bancos/{id}/preguntas` (ya existe, `US-2.1.7`) | Se listan los `unidad_tematica`/`tema` únicos de las preguntas del banco actual |

---

## Especificacion del comportamiento

### Precondicion

- `US-2.1.11` (carga) y `US-2.1.12` (edición) implementadas y mergeadas.
- El banco de la materia puede estar vacío — el control debe funcionar igual (sin opciones
  sugeridas, el Docente escribe el primer valor libremente).

### Postcondicion

- Al abrir el formulario de carga o edición de una pregunta, los campos "Unidad temática" y
  "Tema" muestran como sugerencias los valores ya usados en el banco de esa materia (sin
  duplicados).
- El Docente puede seleccionar una sugerencia o escribir un valor nuevo — no es un `<select>`
  cerrado, es un combobox.
- El envío del formulario sigue mandando `unidad_tematica`/`tema` como `str` libre — sin
  cambios en `banco-preguntas-api.ts` ni en los endpoints del backend.
- Si el banco está vacío, el campo se comporta como texto libre simple (sin sugerencias),
  sin bloquear la carga de la primera pregunta.

### Invariantes

| ID | Invariante |
|----|------------|
| — | Sin invariantes de dominio nuevas — `unidad_tematica`/`tema` siguen sin restricción de formato más allá de la ya existente (`min_length=1, max_length=200`, `schemas.py`). |

---

## Criterios de aceptacion

```gherkin
Feature: Unidad temática y Tema como combobox derivado del banco (US-ADJ-02)

  Scenario: Sugerencias derivadas del banco con preguntas existentes
    Given un banco con preguntas que usan "Unidad 2" y "DDD" como unidad/tema
    When un Docente abre el formulario de carga de una pregunta nueva en esa materia
    Then el campo "Unidad temática" sugiere "Unidad 2" entre sus opciones
    And el campo "Tema" sugiere "DDD" entre sus opciones

  Scenario: Banco vacío
    Given un banco recién creado, sin preguntas
    When un Docente abre el formulario de carga de la primera pregunta
    Then los campos "Unidad temática" y "Tema" no tienen sugerencias
    And el Docente puede escribir un valor nuevo libremente y guardar la pregunta

  Scenario: Escribir un valor no sugerido
    Given un Docente en el formulario de carga con sugerencias disponibles
    When escribe una unidad temática que no está en la lista de sugerencias
    Then el sistema acepta el valor y lo guarda igual (no es un select cerrado)
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — sin cambios de capas de dominio ni de contratos de API; reusa
  `GET /bancos/{id}/preguntas` ya existente. Es una decisión de UI, ya tomada por Víctor
  (derivar del banco actual, no agregar un catálogo — ver `HITO-5`).

**Capa(s) afectadas:**
- [x] Frontend — `NuevaPreguntaOpcionMultiple.tsx`, `NuevaPreguntaVerdaderoFalso.tsx`,
  `EditarPregunta.tsx`, posible componente nuevo de combobox en `components/ui/`
- [ ] Backend — sin cambios

---

## Fuente de verdad UX

`docs/design/ux/wireframes-banco-preguntas.md` §2.5/§2.6 (unidad temática ya era `select` en
el diseño original). El comportamiento de combobox derivado del banco es una decisión de
Víctor posterior al prototipo estático (que hardcodea opciones fijas) — no requiere volver a
pasar por el gate de prototipo/wireframe porque no cambia la disposición visual, solo el
origen de los datos de un campo ya existente.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/pages/NuevaPreguntaOpcionMultiple.tsx` | Unidad temática y Tema como combobox con sugerencias del banco |
| `frontend/src/pages/NuevaPreguntaVerdaderoFalso.tsx` | Ídem |
| `frontend/src/pages/EditarPregunta.tsx` | Ídem |
| `frontend/src/components/ui/combobox.tsx` (o `datalist` simple) | Componente/patrón nuevo, reusado en las 3 pantallas |

---

## Referencias

- Relacionada con: `US-2.1.7` (`GET /bancos/{id}/preguntas`, fuente de las sugerencias),
  `US-2.1.11`/`US-2.1.12` (pantallas que esta US ajusta), `HITO-5` (hallazgo que origina esta
  US), `US-ADJ-01` (ajuste visual de las mismas pantallas — coordinar implementación conjunta
  si se hacen en el mismo ciclo, para no tocar los mismos archivos dos veces)
- Candidatas: sin incremento asignado — se decide después de completar el UAT de cierre de la
  Iteración 1 (`quality/reports/uat/inc2/evidencia.md`)

---

*Basado en el template de `docs/specs/inc2/US-2.1.13.md` — adaptado a capas
`entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`). US de ajuste (`SP-ADJ`,
`docs/plans/PLAN-CM.md` §12) — sin Issue de GitHub ni branch hasta que se decida el
incremento de implementación.*
