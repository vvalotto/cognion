# BL-008 — Estabilización de Portales (datos reales)

| Campo | Valor |
|-------|-------|
| Tipo | Incremento técnico (no planificado en `PLAN_v1.md` — insertado fuera de la secuencia, sin numeración `N-ADJ` porque no abrió su propio Milestone de GitHub) |
| Fecha apertura | 2026-09-08 |
| Fecha cierre | 2026-09-10 |
| Git tag inicial | `v0.6.1` (`BL-007`) |
| Git tag cierre | `v0.6.2` (PATCH — mismo criterio de versionado que `BL-005`/`BL-007`) |
| Estado | ✅ Completado — mergeado a `main` |
| DoD | Los tres portales (Administrador, Docente, Estudiante) recorridos de punta a punta desde un login real, con datos reales de la materia "Ingeniería de Software" (71 preguntas, 17 estudiantes), sin hallazgos 🔴 Bloqueantes sin resolver. |

---

## Descripción

Prueba manual E2E de estabilización posterior al cierre de `BL-007` (decisión explícita de
Víctor, sin US-IEDD ni spec formal): recorrer cada portal desde un login real con una base
limpia, narrando cada paso, para revisar y estabilizar aspectos que ninguna de las rondas de
UAT formales anteriores había cubierto. Registrada en tres bitácoras narradas por Víctor y
escritas por la sesión de Claude Code —
[`tests/uat/datos-reales/bitacora-administrador.md`](../../tests/uat/datos-reales/bitacora-administrador.md),
`bitacora-docente.md`, `bitacora-estudiante.md` — **no versionadas** (el directorio
`tests/uat/datos-reales/` queda fuera de git: contiene datos reales de estudiantes y material
docente en `.docx`). Regla operativa de la sesión: no correr `pytest` mientras duraba la
prueba (trunca la base de datos local compartida) — verificación con `curl`/`psql` directo en
cada paso.

Tres PRs, uno por portal, todos mergeados a `develop` con pre-push gate (`DesignReviewer`) en
0 CRITICAL:

- **PR [#298](https://github.com/vvalotto/cognion/pull/298)** — portal Administrador (bitácora
  Pasos 1 a 9). Hallazgo más serio de toda la prueba: `PATCH` de edición de cuenta devolvía
  `200` con el dato "correcto" pero `SQLAlchemyUsuarioRepository.actualizar()` nunca escribía
  `nombre`/`email` al modelo ORM — placebo total, invisible sin volver a consultar la base
  (Paso 5). Mismo bug class detectado en `MateriaRepositoryPort` (Paso 6). Estandarización de
  CRUD completa para Materias/Comisiones/Cuentas: editar, ver, eliminar con baja lógica
  condicionada a datos asociados, y reactivar (Pasos 8-9) — dos puertos cruzados nuevos
  (`ComisionConsultaPort` Banco→Identidad, `EvaluacionConsultaPort` Identidad→Actividad
  Evaluativa, ambos in-process). Además: `/` sin sesión ahora redirige a `/login` (Paso 1),
  `POST /materias` acepta rol `administrador` además de `docente` (Paso 3), `RequireRole` gana
  soporte de array de roles.
- **PR [#299](https://github.com/vvalotto/cognion/pull/299)** — portal Docente (bitácora Pasos
  1 a 12). Carga masiva de las 71 preguntas reales de Ingeniería de Software vía script
  (`cargar_preguntas.py`). Hallazgo de producto: una Actividad Evaluativa no estaba restringida
  a una Comisión ni a una unidad temática/tema concretos — resuelto con filtros nuevos en el
  formulario de alta y su validación correspondiente (Pasos 3, 5, 10, 10b). Listados de
  Actividades/Materias/Comisiones pasados a tabla con columnas de métricas (cantidad de
  comisiones/estudiantes/actividades). Formularios de alta/edición con estilo más elegante y
  tinte suave en los campos (Pasos 11-12).
- **PR [#300](https://github.com/vvalotto/cognion/pull/300)** — portal Estudiante (bitácora
  Pasos 1 a 5). Carga de los 17 estudiantes reales vía script (`cargar_estudiantes.py`).
  Decisión de producto significativa (Paso 3): el Estudiante puede ver si acertó o no cada
  respuesta y reintentarla mientras la evaluación siga en curso (antes: sin feedback ni
  reintento) — `IntentosAgotados` (422) nuevo, contador de intentos por pregunta. Decisión de
  producto (Paso 4): "Finalizar evaluación" pasa a ser una acción independiente de responder la
  última pregunta — el Estudiante decide cuándo cerrar, ya no se dispara automáticamente. Paso
  5, fuera de implementación: elicitación de `RF-20` a `RF-23` (informes de Analytics para el
  Docente — desempeño por comisión, evolución temporal, ranking de preguntas falladas,
  completitud por actividad), agregados a `docs/rf/RF_v1.md` y a la matriz de trazabilidad como
  Planificado, sin incremento asignado todavía (decisión explícita: no se prioriza en esta
  baseline).

Ningún hallazgo de esta prueba requirió una invariante de dominio nueva — los cambios de
entidad (`Usuario`, `Materia`, `Comision`, `Evaluacion`) fueron mutaciones y validaciones
simples sobre el patrón ya existente. Sin Issues de GitHub ni specs — track informal en su
totalidad, consistente con la clasificación de hallazgos de frontend/backend ya usada en UAT
anteriores.

---

## Inventario de Configuration Items

| CI | Artefacto | Tipo | Descripción |
|----|-----------|------|-------------|
| CI-D38 | `tests/uat/datos-reales/bitacora-{administrador,docente,estudiante}.md` (no versionados) | Documento | Bitácoras narradas de la prueba manual E2E, evidencia de UAT de esta baseline |
| CI-D39 | `docs/rf/RF_v1.md` (RF-20 a RF-23), `docs/traceability/matrix.md` (filas nuevas, Planificado) | Documento | Nuevos RF de Analytics para el Docente, elicitados durante la prueba |
| CI-C17 | `src/identidad/{entities,use_cases,interface_adapters,frameworks}/**` (Usuario/Materia/Comision: editar, eliminar, activar; `ComisionConsultaPort`) | Código de backend | Estandarización de CRUD Identidad + puerto cruzado hacia Banco de Preguntas |
| CI-C18 | `src/banco_preguntas/**` (Materia editar/eliminar/activar, restricción de Actividad por unidad temática/tema) | Código de backend | Estandarización de CRUD Banco de Preguntas |
| CI-C19 | `src/actividad_evaluativa/**` (`EvaluacionConsultaPort`, restricción por Comisión, `IntentosAgotados`, finalizar independiente) | Código de backend | Puerto cruzado hacia Identidad + reintento de respuestas + finalización independiente |
| CI-F12 | `frontend/src/pages/{identidad,cuentas,banco-preguntas,actividad-evaluativa}/**` | Código de frontend | Tablas con métricas, formularios elegantes, reactivar entidades, reintento en `RendirEvaluacion.tsx` |
| CI-T09 | `quality/reports/designreviewer/BL-008-designreviewer.txt`, `quality/reports/architectanalyst/BL-008-arquitectura.json` | Herramienta | Salidas de cierre de baseline |

---

## Métricas al cerrar

**Backend:**
- `pytest tests/`: 910 passed
- `ruff check src/`: 0 violaciones (All checks passed!)
- `mypy src/`: 0 errores (227 archivos)
- `pylint src/`: 9.57/10 (`BL-005`: 9.59/10 — leve baja, sin CRITICAL nuevo, `duplicate-code`
  entre `analytics/frameworks/api/schemas` y `use_cases/obtener_desempeno_estudiante`)
- Cobertura (`pytest --cov=src --cov-report=json`): 94.42% (2860/3029 statements)

**Frontend:**
- `vitest run`: 379/379 tests, 64 archivos
- Cobertura (`vitest run --coverage --no-file-parallelism`): 90.9% statements / **80.36%
  branches** (por encima del umbral global del 80%) / 86.21% functions / 93.58% lines
- `oxlint`: 0 errores, 6 warnings preexistentes (`only-export-components`, `no-unsafe-optional-chaining`)
- `tsc -b --noEmit`: 0 errores

**Diseño:**
- `designreviewer src/ --config pyproject.toml`: 0 CRITICAL, **161 advertencias** (`BL-007`:
  132 — suba de 29, esperable por el volumen de código agregado en 3 PRs de estandarización;
  sin cluster nuevo relevante, mismos analyzers ya vistos: `LongMethodAnalyzer`,
  `LawOfDemeterAnalyzer`), 130.5h de deuda técnica estimada (0h bloqueante)
- `architectanalyst src/ --sprint-id BL-008 --config pyproject.toml`: 6 críticos (mismo "Zone
  of Pain" aceptado desde `US-ADJ-13`/`19` — `identidad`, `settings`, `shared`,
  `banco_preguntas`, `actividad_evaluativa`, `analytics`, sin módulo nuevo desde `BL-006`), 9
  warnings, 147 infos, `should_block: false`

**UAT:** prueba manual E2E completa de los tres portales con datos reales (bitácoras arriba),
sin hallazgos 🔴 Bloqueantes sin resolver al cierre — todos los hallazgos de las tres bitácoras
fueron corregidos en el momento, dentro de los PR #298/#299/#300. Sin Capa 2 HTTP/WS separada
(la prueba en sí, contra el backend real vía navegador y `curl`, cumple ese rol). Sin RF/RNF
que pasen de Implementado a Validado — todos los cambios son refinamientos de UI/UX y
correcciones de bugs sobre RF ya `Validado` (`RF-01`, `RF-02`, `RF-03`) o backlog nuevo sin
implementar (`RF-20` a `23`, quedan en Planificado).

---

## Decisiones técnicas relevantes

| Decisión | Contexto |
|----------|----------|
| Baseline propia (`BL-008`) sin Milestone de GitHub ni numeración `N-ADJ` | La prueba no tenía US-IEDD ni Issues desde el inicio (decisión de Víctor al abrirla); se decide al cerrarla, igual que se había dejado pendiente en `BL-007`, que sí ameritaba consolidar en una baseline técnica — mismo criterio de trazabilidad de `BL-005`, pero sin aparato de Milestone porque no hubo Issues que cerrar. |
| `tests/uat/datos-reales/` queda fuera de git permanentemente | Contiene `.docx` con contenido de examen real y datos de 17 estudiantes reales — no es evidencia que deba vivir versionada en el repositorio, a diferencia de `quality/reports/uat/incN/` de las UAT formales. |
| RF-20 a RF-23 quedan sin incremento asignado | Decisión explícita de Víctor al cerrar esta baseline: no priorizar todavía — se retoma en una sesión de planificación futura (Incremento 5 de `PLAN_v1.md` o un nuevo `-ADJ`). |
| Reintento de respuestas y finalización independiente (Estudiante) sin nueva US-IEDD | Cambios de comportamiento visibles para el usuario final, pero sin invariante de dominio nueva (`FinalizarEvaluacionUseCase`/`RegistrarRespuestaUseCase` ya soportaban ambos casos desde `US-3.2.1`/`3.2.4`) — track informal, mismo criterio de clasificación de hallazgos de UAT ya usado en `BL-004`/`BL-006`. |

---

## Retrospectiva

### ¿Qué funcionó?

- Verificar cada cambio de backend con `curl` + `psql`/`SELECT` directo, nunca confiando en un
  `200` de la UI, fue lo que permitió detectar el hallazgo más serio de la prueba (Paso 5 del
  portal Administrador: `actualizar()` no escribía nada al ORM pese a responder `200`) —
  invisible a cualquier prueba que solo mirara el código de respuesta HTTP.
- Cargar datos reales (71 preguntas de un `.docx` docente, 17 estudiantes reales) en vez de
  fixtures mínimos volvió a exponer problemas de volumen/usabilidad que ninguna ronda de UAT
  con datos sintéticos había mostrado — mismo patrón ya documentado para el Banco de Preguntas
  en el Incremento 2.
- Clasificar cada hallazgo como frontend-puro vs. que toca `src/` *antes* de codear (regla ya
  establecida desde Identidad) se mantuvo consistente en las tres bitácoras, sin necesidad de
  pivotar de track a mitad de un fix.

### ¿Qué fue más difícil de lo esperado?

- El bug de `actualizar()` sin escritura real llevó a repetir el mismo patrón dos veces
  (`UsuarioRepository` en el Paso 5, `MateriaRepositoryPort` en el Paso 6, que directamente no
  tenía el método) — sugiere que ningún puerto de repositorio tiene todavía una prueba que
  verifique la escritura real contra la base más allá del valor de retorno del método.
- La estandarización de CRUD (Paso 8) resultó bastante más grande de lo previsto al iniciar la
  prueba — terminó cruzando los cuatro BCs (dos puertos in-process nuevos) para poder mostrar
  "¿tiene datos asociados?" antes de decidir baja física vs. lógica.

### ¿Qué ajustar en el próximo incremento?

- Agregar al menos un test de integración por `Repository.actualizar()` que lea de vuelta la
  fila tras escribir, no solo que el método no lance excepción — hubiera detectado el hallazgo
  del Paso 5 sin depender de una prueba manual.
- Retomar la decisión de a qué incremento asignar `RF-20` a `RF-23` antes de que se acumulen
  más RF "Planificado sin incremento" — a la fecha de este cierre son los primeros con ese
  estado.
- El backlog de `DesignReviewer` sigue creciendo sin un incremento dedicado a bajarlo (161 en
  esta baseline, 118 en `BL-005`) — evaluar si amerita una iteración de ajuste propia antes de
  que un archivo puntual empiece a concentrar issues nuevos.

---

*Creado: 2026-09-10*
