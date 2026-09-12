# BC Analytics — Modelo de Dominio (Event Storming ligero)

> Estado documental: **borrador — pendiente de aprobación explícita de Víctor en el comentario
> de cierre del Issue [#227](https://github.com/vvalotto/cognion/issues/227) (US-4.0.1,
> Iteración 0, Incremento 4).**
> Alcance de este modelo: RF-15 (vista de desempeño individual del estudiante, acotada a
> evaluaciones de período abierto — sin sesiones en vivo, que no existen todavía, Incremento
> 6), RF-16 (seguimiento por alumno) y RF-17 (seguimiento por curso y tema). RF-18 (KPIs
> históricos) queda fuera — Incremento 7.
>
> Fuente: `docs/rf/RF_v1.md` (RF-15, RF-16, RF-17), `docs/rf/ARQ_v1.md` (Analytics = Supporting
> Subdomain, Read Models sin persistencia de escritura propia), `ADR-002` (Event Sourcing +
> CQRS, ya implementado en BC Actividad Evaluativa),
> `docs/design/domain/BC-actividad-evaluativa-modelo.md` §6 ("Frontera con Analytics" — el
> event store queda preparado desde el inicio para este consumo), `docs/design/domain/
> BC-banco-preguntas-modelo.md` (`unidad_tematica`/`tema` de `PreguntaPlantilla`),
> `docs/design/domain/BC-identidad-modelo.md` (`Comisión`, `Estudiante.comision_id`).
> Modelado en conversación con Víctor, 2026-09-04.
> Diagrama de event storming (flujo de consulta: actor → query → puerto → fuente de datos, en
> Mermaid): `BC-analytics-modelo-event-storming.html`.
> Diagrama complementario (puertos de consulta, sus métodos y DTOs, en Mermaid):
> `BC-analytics-modelo-diagramas.html`.
>
> **Ampliación 2026-09-12 — pendiente de aprobación** (`US-ADJ-33`, Incremento 5-ADJ,
> `docs/plans/inc5-adj/inc5-adj-candidatas.md`): se agrega el §8 con las 4 queries de RF-20 a
> RF-23 (agregadas a `RF_v1.md` el 2026-09-09, sin incremento asignado hasta ahora). No
> reemplaza nada de lo ya aprobado en `US-4.0.1` — solo agrega.

---

## 1. Actores

| Actor | Rol en el BC |
|---|---|
| Estudiante | Consulta su propio desempeño: por evaluación individual (RF-15) y acumulado en toda la materia |
| Docente | Consulta el desempeño de un estudiante elegido (RF-16, misma forma que el estudiante ve el suyo) y el desempeño agregado de una comisión o de toda la materia por tema (RF-17) |

Sin actor Sistema — a diferencia de Actividad Evaluativa, no hay disparadores automáticos ni
Policy: todo el BC reacciona a queries síncronas de un usuario autenticado.

---

## 2. Concepto central — BC puramente de lectura, sin aggregate propio

Primer BC del sistema sin aggregate, sin comando y sin evento de dominio propio (`ARQ_v1.md` —
Analytics, Supporting Subdomain). No hay invariante que proteger ni estado que mutar: todo el
dato ya existe, escrito por BC Actividad Evaluativa (event store, `ADR-002`) y BC Banco de
Preguntas/Identidad (metadatos). El trabajo de este BC es exclusivamente **componer y agregar
lectura de otros BCs, vía puertos** (`CLAUDE.md` — nunca imports directos entre BCs).

**Decisión de mecanismo (confirmada con Víctor):** **query directa** sobre las fuentes
existentes, sin read model materializado ni tabla propia — mismo criterio ya aplicado en
`evaluaciones_activas_por_actividad` (`US-3.2.4`), y más apropiado acá todavía: Analytics no
tiene ningún evento propio que sincronizar, así que materializar implicaría inventar un
mecanismo de recomputación sin ningún trigger de dominio que lo dispare. Válido a la escala del
proyecto (30-60 alumnos por comisión); revisar si el volumen cambia.

**Patrón CQRS — puertos angostos, uno por fuente y por necesidad, sin puerto único
"AnalyticsQueryPort".** Mismo criterio que ya evitó el CRÍTICO de CBO repetido en
`US-2.1.2`/`US-2.1.5`/`US-2.1.6`/`US-2.1.7` y que separó `EvaluacionActivaQueryPort` de
`ActividadQueryPort` de `EvaluacionEstudianteQueryPort` dentro del propio BC Actividad
Evaluativa: cada puerto expone exactamente lo que un Use Case necesita, no una superficie
genérica. Facilita agregar más resultados analíticos más adelante (RF-18, Incremento 7) sumando
puertos/Use Case nuevos en vez de ensanchar los existentes.

---

## 3. Fuentes de datos consumidas (vía puertos, sin imports directos)

| Fuente | BC dueño | Qué expone |
|---|---|---|
| Tabla `events` (streams `Evaluacion` y `ActividadEvaluativaPeriodoAbierto`) | Actividad Evaluativa | `Respuesta` vigente por `pregunta_id` (`es_correcta`, `confirmada_en`), `estudiante_id`, `actividad_id` → `materia_id`, `estado`/`finalizada_en` de cada `Evaluacion` |
| `PreguntaPlantilla.unidad_tematica` / `.tema` | Banco de Preguntas | Metadato de clasificación por `pregunta_id`, ya expuesto vía `MetadatosPregunta` (`US-ADJ-17`) |
| `Comisión` (roster) | Identidad | Qué `estudiante_id` pertenecen a qué `comision_id`, y qué comisiones tiene una `materia_id` |

---

## 4. Queries → resultados (sin comando ni evento de dominio)

| Query | Actor | RF | Resultado |
|---|---|---|---|
| `ObtenerDesempenoPorEvaluacion(estudiante_id, materia_id?)` | Estudiante (su propio `estudiante_id`) o Docente (`estudiante_id` elegido) | RF-15, RF-16 | Una fila por `Evaluacion` finalizada del estudiante (filtrada por materia si se indica): `evaluacion_id`, `actividad_id`, `materia_id`, `finalizada_en`, `cantidad_correctas`, `cantidad_incorrectas` |
| `ObtenerDesempenoAcumuladoPorMateria(estudiante_id, materia_id)` | Estudiante o Docente | RF-15, RF-16 | Suma de correctas/incorrectas de todas las `Evaluacion` finalizadas del estudiante en esa materia — agregación sobre el mismo dato de la query anterior, sin fuente adicional |
| `ObtenerTasaErrorPorTema(materia_id, comision_id?)` | Docente | RF-17 | Una fila por `(unidad_tematica, tema)` de la materia: `cantidad_respuestas`, `cantidad_incorrectas`, `tasa_error` — agregado sobre todas las comisiones de la materia si `comision_id` se omite, o acotado al roster de una comisión puntual si se indica |

**Nota de alcance RF-15:** el RF menciona también sesiones en vivo ("para sesiones en vivo, ve
su puntaje y posición en el ranking") — ese tipo de sesión no existe todavía (Incremento 6). Las
tres queries de arriba cubren exclusivamente evaluaciones de período abierto.

---

## 5. Puertos nuevos a definir

### `EvaluacionDesempenoConsultaPort` → BC Actividad Evaluativa

Implementado por un adapter in-process propio en `src/analytics/frameworks/adapters/`, que
consulta directamente la tabla `events` (misma tabla física, mismo proceso — no importa código
Python de `src/actividad_evaluativa/`, mismo patrón que los adapters in-process ya usados para
`MateriaPort`/`MateriaConsultaPort`).

| Método | Devuelve |
|---|---|
| `listar_evaluaciones_finalizadas(estudiante_id, materia_id: UUID \| None)` | Una fila por `Evaluacion` finalizada del estudiante — `evaluacion_id`, `actividad_id`, `materia_id`, `finalizada_en`, `cantidad_correctas`, `cantidad_incorrectas` |
| `listar_respuestas_vigentes_de_materia(materia_id, estudiante_ids: list[UUID] \| None)` | Una fila por `Respuesta` vigente (`pregunta_id`, `estudiante_id`, `es_correcta`) de toda `Evaluacion` finalizada de la materia, filtrado a `estudiante_ids` si se indica (roster de una comisión) — insumo de `ObtenerTasaErrorPorTema` |

### `PreguntaMetadatoConsultaPort` → BC Banco de Preguntas

Copia propia de Analytics (mismo criterio que `MateriaPort` de Identidad vs.
`MateriaConsultaPort` de Actividad Evaluativa — cada BC consumidor define su propio contrato,
no importa el de otro BC).

| Método | Devuelve |
|---|---|
| `obtener_metadatos(pregunta_ids: list[UUID])` | `dict[UUID, MetadatoPreguntaResumen]` — `unidad_tematica`/`tema` por `pregunta_id`, para el `join` en memoria con `listar_respuestas_vigentes_de_materia` |

### `ComisionConsultaPort` → BC Identidad

**Puerto nuevo, sin equivalente hoy** — examinado `src/identidad/entities/ports/`: ni
`ComisionRepositoryPort` ni `UsuarioRepositoryPort` exponen "estudiantes de una comisión" ni
"comisiones de una materia" (ambos son puertos internos de Identidad, con solo
`obtener_por_id`). Requiere una query nueva del lado de Identidad — se implementa en `US-4.0.1`
o la primera US de Iteración 2 que lo necesite (RF-17), no bloquea la aprobación del modelo.

| Método | Devuelve |
|---|---|
| `listar_comisiones_por_materia(materia_id)` | `list[ComisionResumen]` (`id`, identificador visible — horario u otro campo de `Comisión`) |
| `listar_estudiantes(comision_id)` | `list[UUID]` — roster de `estudiante_id` de esa comisión |

---

## 6. Hot spots — resueltos con Víctor (2026-09-04)

1. **Mecanismo de proyección:** query directa, no materializada (§2).
2. **Alcance de "por curso" en RF-17:** ambos niveles — por materia completa (todas las
   comisiones) y por comisión puntual, vía el parámetro opcional `comision_id` en
   `ObtenerTasaErrorPorTema` (§4).
3. **RF-15/RF-16 — vista por sesión vs. acumulada:** el estudiante (y el docente, mirando a un
   estudiante) necesita ambas — por evaluación individual y acumulada en toda la materia. Se
   resuelve con dos queries (§4): `ObtenerDesempenoPorEvaluacion` da el detalle fila por fila,
   `ObtenerDesempenoAcumuladoPorMateria` agrega sobre el mismo dato — no hace falta una fuente
   adicional para el acumulado.
4. **Puertos de consulta a Identidad:** no existe nada reusable — `ComisionConsultaPort` es
   puerto nuevo (§5), con la implementación de sus métodos en Identidad diferida a la spec de
   la US que primero lo necesite (RF-17).

**Pendiente de definir en la spec de implementación (no bloquea la aprobación del modelo):**
- Forma exacta de `ComisionResumen` (qué campo de `Comisión` la identifica de forma legible
  para el docente en la UI — a resolver junto con `US-4.0.2`, wireframes).
- Si `ObtenerTasaErrorPorTema` pagina o no — a esta escala (una materia, un puñado de
  unidades/temas) probablemente no lo necesite, a confirmar cuando haya datos reales de
  volumen.

---

## 7. Próximo paso

Modelo completo, sin hot spots abiertos (§6) — pasa a aprobación explícita de Víctor en el
comentario de cierre del Issue #227 (DoD tipo `Modelado`, `WORKFLOW-DESARROLLO.md` §2). Una vez
aprobado, es el input de los wireframes de US-4.0.2 (Issue #228) y de las specs US-IEDD de las
Iteraciones 1 y 2 (`docs/plans/inc4/inc4-candidatas.md`).

---

## 8. Ampliación — RF-20 a RF-23 (Incremento 5-ADJ, `US-ADJ-33`)

> Origen: `RF-20` a `RF-23` (`RF_v1.md`, agregados 2026-09-09 durante la prueba manual E2E de
> estabilización), sin incremento asignado hasta que se agrupan en
> `docs/plans/inc5-adj/inc5-adj-candidatas.md`. Mismo criterio del BC ya vigente (§2): sin
> aggregate, sin comando, sin evento propio — solo compone lectura de otros BCs vía puertos.
> Todos los actores son Docente (a diferencia de RF-15/16, acá no hay vista propia del
> Estudiante).

### 8.1 Hallazgo de deriva documental — `ActividadEvaluativaPeriodoAbierto` (no bloquea este modelo)

Al diseñar RF-20 se detectó que `src/actividad_evaluativa/entities/actividad_evaluativa_periodo_abierto.py`
ya tiene cuatro atributos que `docs/design/domain/BC-actividad-evaluativa-modelo.md` (§5, la
tabla del aggregate) no documenta: `titulo` (`US-ADJ-10`), `comisiones_ids` (restricción de
visibilidad por comisión, agregada en la prueba de estabilización del portal Docente, PR #299,
sin US-IEDD formal — hallazgo de UAT resuelto directo en `src/`, `frontend/`-only según el
criterio de la época pero terminó tocando el aggregate) y `unidad_tematica`/`tema` (restricción
del set aleatorio, mismo PR). Este modelo de Analytics **ya diseña contra el código real**
(`comisiones_ids` es imprescindible para RF-20, ver §8.3) — la actualización formal de
`BC-actividad-evaluativa-modelo.md` §5 queda anotada para la Iteración 5 (revisión documental
transversal) de este mismo incremento, no se corrige acá para no mezclar el modelo de un BC
ajeno dentro de este documento.

### 8.2 Fuentes de datos nuevas / puertos ampliados

| Fuente | BC dueño | Qué expone (nuevo) |
|---|---|---|
| `ActividadEvaluativaPeriodoAbierto.comisiones_ids`/`fecha_apertura`/`fecha_cierre`/`cerrada_manualmente` | Actividad Evaluativa | Qué actividades de una materia están **abiertas ahora** y visibles para una comisión puntual (RF-20) |
| Tabla `events`, stream `Evaluacion` — estado sin exigir `Finalizada` | Actividad Evaluativa | Estado (`en_curso`/`suspendida`/`finalizada`) de cada `Evaluacion` de una actividad puntual, no solo las finalizadas (RF-23) — a diferencia de `listar_evaluaciones_finalizadas` (§5), que ignora todo lo que no llegó a `Finalizada` |
| `PreguntaPlantilla.enunciado` | Banco de Preguntas | Texto de la pregunta, para el ranking (RF-22) — `MetadatoPreguntaResumen` (§5) hoy solo trae `unidad_tematica`/`tema` |

**Ampliación de `EvaluacionDesempenoConsultaPort`** (mismo puerto de §5, crece con la
Iteración 4 igual que ya creció entre `US-4.1.1` y `US-4.2.4` — no se crea un puerto nuevo por
cada RF):

| Método nuevo | Devuelve |
|---|---|
| `listar_actividades_abiertas(materia_id, comision_id)` | `list[UUID]` de `actividad_id` con `fecha_apertura ≤ ahora ≤ fecha_cierre`, `cerrada_manualmente = false`, y visibles a `comision_id` (`comisiones_ids` vacío = todas, o `comision_id ∈ comisiones_ids`) — insumo de "actividades pendientes" (RF-20) |
| `listar_estados_de_actividad(actividad_id, estudiante_ids)` | `dict[UUID, EstadoEvaluacion]` — estado de la `Evaluacion` de cada estudiante para esa actividad puntual (`en_curso`, `suspendida` o `finalizada`); un `estudiante_id` ausente del dict nunca inició — "sin iniciar" (RF-23) |

**Ampliación de `MetadatoPreguntaResumen`/`PreguntaMetadatoConsultaPort`** (§5): agrega el
campo `enunciado: str` al DTO existente — mismo método `obtener_metadatos`, sin nuevo método,
ya que es la misma consulta por lote a `PreguntaPlantilla` ampliando qué campos trae.

**Sin cambios** en `ComisionConsultaPort` (§5) — `listar_comisiones_por_materia` y
`listar_estudiantes` ya alcanzan para las 4 queries nuevas.

### 8.3 Queries → resultados (nuevas)

| Query | RF | Resultado |
|---|---|---|
| `ObtenerDesempenoPorComision(comision_id)` | RF-20 | Una fila por estudiante de la comisión: `estudiante_id`, `nombre`, `porcentaje_aciertos_acumulado: float \| None` (`None` = "Sin datos", nunca `0%`, si no tiene ninguna `Evaluacion` finalizada — agrega igual que `ObtenerDesempenoAcumuladoPorMateria`, §4, para cada estudiante del roster), `actividades_pendientes: int` (actividades de `listar_actividades_abiertas(materia_id, comision_id)` sin `Evaluacion` `Finalizada` de ese estudiante — no distingue sin-iniciar de en-curso/suspendida, ese detalle es RF-23) |
| `ObtenerRevisionDeEvaluacion(evaluacion_id, docente_id)` | RF-20 (drill-down) | Reusa la revisión completa ya existente de Actividad Evaluativa (`GET /evaluaciones/{id}/revision`, `US-3.2.3`) — **requiere ampliar su guard de rol** (hoy solo el propio Estudiante dueño puede pedirla) para admitir Docente, validando que la `Evaluacion` pertenezca a una comisión de una materia que ese Docente dicta (mismo patrón de `require_docente_o_administrador` ya usado en `US-ADJ-23`, pero acá es "Docente de la materia", no "cualquier Docente") |
| `ObtenerEvolucionTemporalEstudiante(estudiante_id, materia_id)` | RF-21 (individual) | Una fila por `Evaluacion` finalizada del estudiante en la materia, ordenada por `finalizada_en` — mismo dato que `ObtenerDesempenoPorEvaluacion` (§4), solo reordenado como serie temporal; sin fuente adicional |
| `ObtenerEvolucionTemporalComision(comision_id, materia_id)` | RF-21 (comisión) | Una fila por `actividad_id` con al menos una `Evaluacion` finalizada de algún estudiante del roster: `porcentaje_aciertos_promedio` (promedio simple entre los estudiantes que finalizaron esa actividad — quien no la rindió no entra al promedio de ese punto, no cuenta como 0%), ordenada por `min(finalizada_en)` del grupo como proxy de orden cronológico de la actividad (evita depender de `fecha_apertura`, que `EvaluacionDesempenoResumen` no trae hoy) |
| `ObtenerRankingPreguntasFalladas(materia_id, comision_id?)` | RF-22 | Una fila por `pregunta_id` que apareció en al menos una `Respuesta` vigente de la materia (`listar_respuestas_vigentes_de_materia`, §5, acotado a `estudiante_ids` del roster si se indica `comision_id`): `enunciado`, `unidad_tematica`, `tema`, `cantidad_presentaciones`, `cantidad_fallos`, `tasa_error` — mismo criterio de "solo lo efectivamente presentado" que evita denominador cero |
| `ObtenerCompletitudPorActividad(actividad_id)` | RF-23 | Una fila por estudiante del roster de la(s) comisión(es) a la(s) que la actividad está restringida, o de **todas** las comisiones de la materia si `comisiones_ids` está vacío (unidas en una sola tabla, sin selección previa del Docente): `estudiante_id`, `nombre`, `estado` ∈ {`sin_iniciar`, `en_curso`, `suspendida`, `finalizada`} — de `listar_estados_de_actividad` (§8.2), completando con `sin_iniciar` los estudiantes ausentes del dict |

### 8.4 Hot spots — resueltos con Víctor (2026-09-12)

1. **¿"Actividades pendientes" (RF-20) distingue sin-iniciar de en-curso/suspendida?**
   Resuelto — no, es un conteo simple ("no finalizada todavía"); el detalle por estado es
   exactamente RF-23, sin duplicar esa granularidad en RF-20.
2. **¿Cómo se ordena el eje X de la evolución por comisión (RF-21) sin un campo de fecha de la
   actividad en el DTO existente?** Resuelto — se usa `min(finalizada_en)` del grupo de
   evaluaciones de esa actividad como proxy de orden cronológico, evitando ampliar
   `EvaluacionDesempenoResumen` con un dato (`fecha_apertura` de la actividad) que ningún otro
   consumidor de ese DTO necesita hoy.
3. **¿Quién puede pedir la revisión completa de una evaluación de un estudiante (RF-20
   drill-down)?** Resuelto — se amplía el guard de `GET /evaluaciones/{id}/revision` (hoy
   exclusivo del propio Estudiante) para admitir también al Docente de la materia de esa
   actividad, no a cualquier Docente del sistema.
4. **¿`ObtenerCompletitudPorActividad` sobre una actividad sin restricción de comisión
   (`comisiones_ids` vacío) — contra qué roster se arma la tabla?** Resuelto con Víctor
   (2026-09-12) — el roster de **todas las comisiones de la materia**, unidas en una sola
   tabla (vía `listar_comisiones_por_materia` + `listar_estudiantes` por cada una,
   `ComisionConsultaPort` §5). Distinto del patrón de `ObtenerTasaErrorPorTema` (RF-17, `comision_id`
   opcional): acá no hace falta que el Docente elija nada — si la actividad está restringida,
   se usa esa(s) comisión(es); si no, se usa la materia entera, sin paso intermedio de
   selección.

### 8.5 Próximo paso

Ampliación del modelo completa — pasa a aprobación explícita de Víctor en el comentario de
cierre del Issue [#319](https://github.com/vvalotto/cognion/issues/319) (`US-ADJ-33`, DoD tipo
`Modelado`, `WORKFLOW-DESARROLLO.md` §2). Habilita `US-ADJ-34` (wireframes) y la Iteración 4 de
`docs/plans/inc5-adj/inc5-adj-candidatas.md`.
