# HITO-5 — Unidad temática y Tema se cargan como texto libre en vez de lista seleccionable

> Estado documental: evidencia
> Registra un hallazgo de aprendizaje del ensayo IEDD en Cognion.
> No reemplaza a las fuentes vigentes (ADRs, arquitectura, specs).

| Campo | Valor |
|-------|-------|
| **Documento** | HITO-5 — hallazgo de UX en UAT de cierre de la Iteración 1, Incremento 2 |
| **Fecha** | 2026-08-17 |
| **Incremento / contexto** | Incremento 2 (Banco de Preguntas), UAT manual en navegador real de cierre de la Iteración 1 — mismo UAT donde se registró `HITO-4` |
| **Relacionado** | `HITO-4`, `docs/design/ux/wireframes-banco-preguntas.md` §2.5/§2.6, `US-2.1.11`, `docs/specs/ajustes/US-ADJ-01.md` |

---

## Contexto

Continuando el UAT manual sobre las pantallas de carga de preguntas (`NuevaPreguntaOpcionMultiple.tsx`,
`NuevaPreguntaVerdaderoFalso.tsx`), Víctor señaló que "Unidad temática" y "Tema" deberían
aparecer como listas para seleccionar, no como campos de texto libre — riesgo de typos que
fragmenten el filtrado del banco (`US-2.1.7`/`US-2.1.10`: dos preguntas con "Unidad 2" y
"Unidad  2" no se agrupan al filtrar).

---

## Hallazgo / Análisis

El wireframe aprobado (`wireframes-banco-preguntas.md` §2.5) ya especificaba esto para Unidad
temática: *"unidad temática (select), tema (texto libre)"* — el código real
(`NuevaPreguntaOpcionMultiple.tsx:157-166`, mismo patrón en `NuevaPreguntaVerdaderoFalso.tsx`
y `EditarPregunta.tsx`) la implementó como `Input` de texto libre, no como `select`.

A diferencia de `HITO-4` (divergencia de estilo, no documentada como decisión), esta sí fue
una **decisión consciente y documentada** — `CLAUDE.md`, nota de cierre de `US-2.1.11`:
*"unidad temática como texto libre — sin catálogo ni endpoint de origen, mismo criterio que
US-2.1.8"*. La razón es real: no existe ningún endpoint que exponga un catálogo de unidades
temáticas por materia, así que en Fase 2 de `/implement-us` se decidió recortar el alcance en
vez de agregar un endpoint nuevo fuera de lo que pedía la US.

Lo que el UAT reveló es que esa decisión, tomada mirando solo la Unidad temática, dejó un gap
de usabilidad que el wireframe no preveía del todo: sin selección de una lista, cargar varias
preguntas de la misma unidad/tema depende de que el Docente escriba el texto de forma
idéntica cada vez. Víctor pidió extender el mismo criterio a Tema también (el wireframe lo
preveía como texto libre incluso en el diseño original).

**Decisión de Víctor (confirmada):** no se necesita un catálogo nuevo en el backend. La lista
se arma en el cliente, derivada de los valores de `unidad_tematica`/`tema` ya presentes en las
preguntas del banco actual (mismos datos que ya trae `GET /bancos/{id}/preguntas` — sin
endpoint nuevo). Como el banco puede estar vacío o el Docente puede necesitar un valor nuevo,
el control debe seguir permitiendo escribir un valor no listado (combobox, no un `<select>`
cerrado).

---

## Aprendizaje(s)

- **L-5.1:** Un recorte de alcance documentado y justificado en el momento (sin catálogo,
  sin endpoint) puede seguir generando fricción real de uso que el criterio de aceptación
  original no anticipaba — la nota en `CLAUDE.md` explicaba el *porqué* de la decisión, pero
  no alcanzaba para prever el impacto de usabilidad hasta que un humano cargó varias preguntas
  seguidas en el UAT.
- **L-5.2:** Cuando dos campos comparten el mismo problema (unidad temática y tema, ambos
  "libres" por falta de catálogo), la solución de menor costo no siempre es agregar backend —
  derivar las opciones del lado del cliente a partir de datos que ya se están trayendo
  (`GET /bancos/{id}/preguntas`) resuelve el caso de uso principal (evitar fragmentación por
  typos) sin ampliar el contrato de la API ni requerir una US-IEDD de backend.

---

## Resumen de Aprendizajes

| ID | Aprendizaje | Impacto |
|----|-------------|---------|
| L-5.1 | Un recorte de alcance justificado en el momento puede seguir dejando fricción de uso real, solo visible en UAT | Proceso |
| L-5.2 | Preferir derivar opciones del lado del cliente sobre datos ya disponibles antes de escalar a un endpoint de catálogo nuevo | Arquitectura / Workflow |

---

*Creado: 2026-08-17*
