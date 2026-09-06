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
