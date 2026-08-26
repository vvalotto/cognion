# DesignReviewer — Iteración 1 del Incremento 3 "Actividad Evaluativa"

| Campo | Valor |
|---|---|
| Comando | `designreviewer src/ --config pyproject.toml` |
| Paths analizados | `src/` completo (163 archivos, todos los BC) |
| Fecha | 2026-08-26 |
| US cubiertas por esta iteración | `US-3.1.1`, `US-3.1.2`, `US-3.1.3` |
| Evidencia cruda | `quality/reports/designreviewer/inc3-iter1-designreviewer.json`, `.txt` |

---

## Resumen ejecutivo

```
163 archivos analizados · 14 analyzers · 1.26s
0 blocking issues (CRITICAL)
114 advertencias (WARNING)
0 informativos (INFO)
should_block: false
Esfuerzo estimado — bloqueantes: 0h · total del changeset: 98.7h
```

**Ningún hallazgo CRITICAL en todo `src/`.** `should_block: false` — DesignReviewer no bloquea
el cierre de esta iteración. Las 114 advertencias son deuda de diseño (métodos largos, Ley de
Demeter, listas de parámetros, etc.) repartida en los 4 BC, ninguna a nivel bloqueante.

| BC | Hallazgos (WARNING) |
|---|---|
| Banco de Preguntas | 59 |
| Identidad | 42 |
| **Actividad Evaluativa** | **11** |
| Shared | 2 |

Banco de Preguntas e Identidad son deuda **preexistente**, no introducida por esta iteración —
no se tocó código de esos BC en `US-3.1.1`/`3.1.2`/`3.1.3` salvo los adapters in-process ya
cubiertos en el pre-push gate de cada US (0 CRITICAL en cada uno, ver `quality/reports/inc3/`).

---

## Hallazgos en Actividad Evaluativa (11, todos WARNING)

| Analyzer | Archivo | Clase/Método | Valor/Umbral |
|---|---|---|---|
| LongMethodAnalyzer | `use_cases/iniciar_evaluacion.py` | `IniciarEvaluacionUseCase.execute` | 61/20 |
| LawOfDemeterAnalyzer | `use_cases/iniciar_evaluacion.py` | `execute` (`evento.ocurrido_en.isoformat`) | 2/1 |
| LongMethodAnalyzer | `use_cases/crear_actividad_periodo_abierto.py` | `CrearActividadPeriodoAbiertoUseCase.execute` | 57/20 |
| LawOfDemeterAnalyzer | `use_cases/crear_actividad_periodo_abierto.py` | `execute` (×3 — `fecha_apertura`/`fecha_cierre`/`ocurrido_en`.isoformat) | 2/1 |
| LongMethodAnalyzer | `entities/actividad_evaluativa_periodo_abierto.py` | `ActividadEvaluativaPeriodoAbierto.crear` | 26/20 |
| LongMethodAnalyzer | `frameworks/api/actividades_router.py` | endpoint `crear_actividad` | 29/20 |
| LongMethodAnalyzer | `frameworks/api/evaluaciones_router.py` | endpoint `iniciar_evaluacion` | 31/20 |
| LawOfDemeterAnalyzer | `frameworks/api/evaluaciones_router.py` | `iniciar_evaluacion` | 2/1 |
| LongMethodAnalyzer | `frameworks/event_store/sqlalchemy_event_store.py` | `SQLAlchemyEventStore` | 27/20 |

### Lectura

- **`LongMethodAnalyzer` en los dos Use Cases y en los dos routers**: ambos `execute()` (57 y
  61 líneas) concentran serialización de payload + orquestación de invariantes en un solo
  método — el mismo patrón en los dos Use Cases del BC (mismo criterio que `US-3.1.2`,
  aceptado en su momento). Los routers superan el umbral por el mapeo manual de excepciones de
  dominio a HTTP status (`try/except` con 2-3 ramas) más la construcción del `Response`
  Pydantic — patrón repetido también en `actividades_router.py` de `US-3.1.2`.
- **`LawOfDemeterAnalyzer`** (`evento.<campo>.isoformat()`, profundidad 2 sobre umbral 1): es
  la serialización del payload del event store — acceder al campo del evento y formatearlo es
  el patrón estándar de este BC (`ADR-002`), no una cadena de navegación real entre
  colaboradores; mismo falso positivo aceptado en `US-3.1.2`.
- **`SQLAlchemyEventStore`** (27/20 líneas): sin cambios en esta iteración — hallazgo
  preexistente de `US-3.1.1`.

**Ninguno de los 11 es CRITICAL ni requiere acción antes de cerrar la iteración** — coherente
con el criterio ya aplicado: DesignReviewer bloquea solo por CRITICAL (ver `CLAUDE.md` §Quality
gates), y esta corrida confirma `should_block: false`.

---

## Conclusión

DesignReviewer sobre `src/` completo: **0 CRITICAL**, 114 WARNING (deuda de diseño repartida,
mayormente preexistente en Banco de Preguntas/Identidad). No bloquea el UAT de la Iteración 1
del Incremento 3. Los 11 hallazgos propios de Actividad Evaluativa son advertencias esperables
(métodos de orquestación algo largos, serialización de eventos) — quedan como candidatos a
refactor si el BC crece, sin urgencia.
