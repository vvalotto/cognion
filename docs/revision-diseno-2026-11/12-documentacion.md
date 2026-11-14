# 12 · Documentación

> Pregunta: ¿la documentación es confiable y se puede sostener?

## Qué se miró

- `README.md`, `CLAUDE.md`, `CHANGELOG.md`.
- `docs/inventario/`, `docs/architecture/` (índice y vista 70), `docs/traceability/matrix.md`.
- Tamaño de cada carpeta de `docs/`.

Se leyeron completos solo los documentos citados. De las vistas de arquitectura se leyó una; el resto se evaluó por su índice.

## Fortalezas

- **Las vistas de arquitectura dicen lo que no saben.** 13 de las 18 vistas de `docs/architecture/` tienen una sección "Sin verificar" y otra "Cómo verificar esta vista contra el código". Es la mejor práctica documental del proyecto.
- **Jerarquía de autoridad explícita.** Ante un conflicto, se sabe qué documento manda: código y tests, baselines, ADR, matriz, `CLAUDE.md`, `README.md`.
- **ADR con notas de vigencia.** Las decisiones superadas se marcan en lugar de borrarse.
- **Docstrings completos** en el código, con referencias a invariantes y decisiones.

## Hallazgos

### DC-01 · El `README.md` describe un proyecto que todavía no empezó

- **Vara:** Conformidad · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:** el [`README.md`](../../README.md) tiene 30 líneas y dice:
  - "🟡 En desarrollo — etapa de definición de requerimientos y arquitectura".
  - "Stack a definir".
  - "`docs/architecture/` — Decisiones de arquitectura (ADR)" (los ADR están en `docs/adr/`).
- **Por qué importa:** es la puerta de entrada del repositorio y de la versión `1.0.0` publicada. Está último en la jerarquía de autoridad, pero es lo primero que se lee.
- **Recomendación:** reescribirlo: qué es, estado (`1.0.0`), stack, cómo instalar (enlace a `docs/INSTALACION.md`) y dónde está la arquitectura.

### DC-02 · `CLAUDE.md` afirma cosas que el código desmiente

- **Vara:** Conformidad · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:**
  - Línea 104: "`main` ← baselines — deploy automático al mergear". No hay despliegue automático.
  - Línea 157: el gate de `main` es "build Docker + deploy + healthcheck". El CD construye y publica.
  - Línea 45: "Python 3.11". Corre en 3.12 ([CA-02](02-conformidad-arquitectonica.md#ca-02--la-versión-de-python-validada-no-es-la-que-corre)).
  - Línea 96: "Incremento (PLAN_v1.md, 0–6)". El proyecto va por el 10.1.
  - "Solo por puertos definidos en `entities/ports/`" como regla entre contextos, cuando la regla verificada es otra ([AC-01](03-acoplamiento-entre-contextos.md#ac-01--ningún-contexto-publica-una-interfaz-el-consumidor-se-acopla-a-sus-internos)).
  - La sección de ítems abiertos mezcla decisiones pendientes con una ya resuelta y tachada.
- **Por qué importa:** este archivo es el contexto que el asistente lee al empezar cada sesión. Una afirmación falsa ahí se convierte en una suposición de trabajo. El mismo archivo dice, en otra sección, que el despliegue no es automático: se contradice.
- **Recomendación:** separar en dos archivos. Uno estable con reglas y arquitectura, y otro con el estado, que se reescribe en cada cierre. Sacar la historia a `docs/historial/`.

### DC-03 · El mapa documental no acompañó a la documentación

- **Vara:** Conformidad · **Severidad:** Baja · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:** `DOCUMENTATION-MAP.md` se actualizó por última vez el 2026-08-31 y `FUENTES-DE-VERDAD-DOCUMENTAL.md` el 2026-09-07. `docs/architecture/` se escribió en noviembre y el mapa la nombra una sola vez, de pasada; su lectura recomendada sigue enviando a `ARQ_v1.md`.
- **Por qué importa:** `CLAUDE.md` remite a este mapa como autoridad por tema. Un índice atrasado es peor que no tener índice, porque se confía en él.
- **Recomendación:** actualizarlo ahora y agregarlo a la lista de verificación de cierre de baseline. Este informe también debería figurar ahí.

### DC-04 · La misma historia se cuenta en cuatro lugares

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** M
- **Evidencia:**
  - `CHANGELOG.md`: 1.361 líneas.
  - `docs/historial/ESTADO-HISTORICO.md`: 1.310 líneas.
  - `.cm/baselines/`: un documento por baseline.
  - `docs/traceability/matrix.md`: su encabezado acumula una entrada "Anterior —" por cada cierre; hay que pasar más de veinte líneas de historia para llegar a la matriz.
- **Por qué importa:** cuatro relatos del mismo hecho son cuatro lugares donde puede quedar una versión distinta, y cada cierre de baseline obliga a tocarlos todos.
- **Recomendación:** una sola fuente para la historia (las baselines). El `CHANGELOG.md` queda para el usuario que instala; la matriz muestra solo el estado actual, con un enlace a la última baseline.

### DC-05 · Los nombres de carpeta ya no dicen lo que contienen

- **Vara:** Decisión · **Severidad:** Baja · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:** `docs/rf/` contiene requerimientos funcionales, no funcionales, arquitectura y plan. `docs/requirements/` contiene solo la visión. `docs/plans/` mezcla procedimientos vigentes (`WORKFLOW-DESARROLLO.md`, `PLAN-CM.md`) con 340 planes de historias.
- **Por qué importa:** encontrar el procedimiento de desarrollo exige saber de antemano que está en la carpeta de planes.
- **Recomendación:** mover los procedimientos a `docs/proceso/` y unificar `rf/` y `requirements/` en `docs/definicion/`. Hacerlo junto con DC-03.

### DC-06 · El código cita documentos que no están en el repositorio

- **Vara:** Conformidad · **Severidad:** Baja · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:** dos docstrings de `src/` citan `feedback_cbo_pre_push_no_fase7`, que es un archivo de la memoria local del asistente, fuera del repositorio. Los docstrings citan además historias (`US-6.2.4`) y secciones de documentos de modelo (`§14`, `§16`).
- **Por qué importa:** la referencia a la memoria local no la puede resolver nadie más. Las referencias a historias envejecen bien como trazabilidad, pero convierten al docstring en un relato de cuándo se escribió algo, en lugar de qué hace.
- **Recomendación:** quitar las dos referencias a la memoria local. En código nuevo, citar invariantes y ADR (que son estables) y dejar la historia para el mensaje del commit.

## Juicio

La documentación de arquitectura reciente es muy buena y marca el estándar: se contrasta con el código y declara lo que no verificó. El problema está en los documentos de entrada (`README.md`, `CLAUDE.md`, el mapa), que son los más leídos y los menos cuidados, y en que hay más documentación de la que una persona puede mantener cierta. Reducir cuánta documentación viva hay es más efectivo que auditarla más seguido.
