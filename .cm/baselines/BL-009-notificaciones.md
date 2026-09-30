# BL-009 — Incremento 5: Notificaciones (RF-14)

| Campo | Valor |
|-------|-------|
| Tipo | Incremento (`PLAN_v1.md`) |
| Fecha apertura | 2026-09-10 |
| Fecha cierre | 2026-09-10 |
| Git tag inicial | `v0.6.2` (`BL-008`) |
| Git tag cierre | `v0.7.0` (MINOR — Incremento de `PLAN_v1.md`, mismo criterio de versionado que `BL-006`) |
| Estado | ✅ Completado — mergeado a `main` |
| DoD | El ciclo de la actividad de período abierto queda completo con la comunicación automática al estudiante: apertura y cierre manual disparan un email real, sin bloquear la operación de dominio ante fallo de envío. |

---

## Descripción

Primer BC puramente event-driven del sistema (`BC-notificaciones-modelo.md` §2): sin
aggregate propio ni comando disparado por un actor humano, reacciona a eventos ya existentes
de Actividad Evaluativa (`ActividadEvaluativaCreada`/`ActividadEvaluativaCerrada`) y produce
un efecto de borde (enviar un email). Incremento corto y deliberadamente aislado (`PLAN_v1.md`):
valida la integración directa Actividad Evaluativa → Notificaciones documentada en `ADR-006`
con el menor acoplamiento posible. Una sola iteración (`inc5-candidatas.md` no planifica una
Iteración 2) — `US-5.1.3` cierra completa la iteración y el incremento entero.

- **US-5.0.1** (Modelado) — Issue [#304](https://github.com/vvalotto/cognion/issues/304):
  contrato de eventos consumidos, forma de la `Notificacion`, puerto de integración directa
  (`ADR-006`), mecanismo de envío para el entorno actual (SMTP de prueba local).
- **US-5.1.1** (Infraestructura), PR [#311](https://github.com/vvalotto/cognion/pull/311):
  `CanalEnvioPort`/`SmtpCanalEnvio`, `ComisionConsultaPort` propio de Notificaciones (con
  `email`), `NotificacionPort` declarado sin cablear.
- **US-5.1.2** (Notificación de apertura), PR
  [#313](https://github.com/vvalotto/cognion/pull/313): `CrearActividadPeriodoAbiertoUseCase`
  dispara `notificar_apertura(...)`, `NotificarAperturaUseCase` nuevo.
- **US-5.1.3** (Notificación de cierre manual), PR
  [#314](https://github.com/vvalotto/cognion/pull/314): `CerrarActividadUseCase` dispara
  `notificar_cierre(...)`, `NotificarCierreUseCase` nuevo, `NotificacionPort.notificar_cierre`
  extendido con `materia_nombre`. El vencimiento natural del período (verificado por
  `VerificarVencimientosUseCase`, `US-3.2.4`) sigue sin disparar ningún email — decisión de
  producto confirmada en la Iteración 0.

UAT de cierre (`quality/reports/uat/inc5/design.md`/`evidencia.md`): Capa 1 (757/757
unit+integration, 212/212 BDD) y Capa 2 (`smoke.sh` extendido con verificación del contenido
real de los emails de apertura y cierre, sin pasos HTTP nuevos — reutiliza el flujo ya
existente de crear y cerrar una actividad) en verde. Sin recorrido de navegador — RF-14 no
tiene pantalla propia; verificación manual = revisión directa del contenido de los emails
capturados por el fake SMTP extendido para persistirlos (antes los descartaba).

---

## Inventario de Configuration Items

| CI | Artefacto | Tipo | Descripción |
|----|-----------|------|-------------|
| CI-D40 | `docs/design/domain/BC-notificaciones-modelo.md` | Documento | Modelo de dominio del BC (`US-5.0.1`) |
| CI-D41 | `docs/specs/inc5/US-5.1.1.md` a `US-5.1.3.md` | Documento | Specs US-IEDD de la Iteración 1 |
| CI-D42 | `quality/reports/uat/inc5/design.md`/`evidencia.md` | Documento | UAT de cierre del incremento |
| CI-C20 | `src/notificaciones/{entities,use_cases,frameworks}/**` | Código de backend | BC nuevo completo: puertos, `NotificarAperturaUseCase`, `NotificarCierreUseCase`, `SmtpCanalEnvio`, `ComisionConsultaPortInProcess` |
| CI-C21 | `src/actividad_evaluativa/entities/ports/notificacion_port.py`, `frameworks/adapters/notificacion_port_in_process.py`, `use_cases/{crear_actividad_periodo_abierto,cerrar_actividad}.py` | Código de backend | Puerto de disparo y su cableado en los dos Use Case que lo invocan |
| CI-C22 | `src/identidad/**` (`ComisionQueryPort.listar_estudiantes_con_email`) | Código de backend | Método nuevo requerido por `ComisionConsultaPort` de Notificaciones |
| CI-T10 | `.claude/skills/run-cognion/fake_smtp.py`, `smoke.sh` | Herramienta | Fake SMTP extendido para persistir contenido real de los mensajes; dos verificaciones nuevas de Capa 2 |
| CI-T11 | `quality/reports/designreviewer/BL-009-designreviewer.txt`, `quality/reports/architectanalyst/BL-009-arquitectura.json` | Herramienta | Salidas de cierre de baseline |

---

## Métricas al cerrar

**Backend:**
- `pytest tests/ --cov=src --cov-report=json`: 969 passed (unit + integration + BDD)
- `ruff check src/`: 0 violaciones (All checks passed!)
- `mypy src/`: 0 errores (238 archivos)
- `pylint src/`: 9.54/10 (`BL-008`: 9.57/10 — leve baja, sin CRITICAL nuevo, mismo
  `duplicate-code` preexistente entre `analytics/frameworks/api/schemas` y
  `use_cases/obtener_desempeno_estudiante`)
- Cobertura: 94.82% (2968/3130 statements)

**Sin frontend** — RF-14 no tiene pantalla propia, sin gate UX que verificar (`docs/specs/inc5/US-5.1.1.md` a `US-5.1.3.md`, "Fuente de verdad UX: No aplica").

**Diseño:**
- `designreviewer src/ --config pyproject.toml`: 0 CRITICAL, 176 advertencias (`BL-008`: 161
  — suba esperable por el BC nuevo, sin cluster relevante nuevo: `LongMethodAnalyzer`,
  `LawOfDemeterAnalyzer`, mismos analyzers ya vistos), 147.0h de deuda técnica estimada (0h
  bloqueante)
- `architectanalyst src/ --sprint-id BL-009 --config pyproject.toml`: 7 críticos (mismo "Zone
  of Pain" aceptado desde `US-ADJ-13`/`19` — `identidad`, `settings`, `shared`,
  `banco_preguntas`, `actividad_evaluativa`, `analytics`, **`notificaciones` nuevo** como
  séptimo módulo del mismo patrón), 10 warnings, 155 infos, `should_block: false`

**UAT:** aprobada sin hallazgos (`quality/reports/uat/inc5/evidencia.md`) — Capa 1 + Capa 2 en
verde, contenido real de los emails de apertura y cierre revisado. RF-14 pasa de
"Especificado" a "Validado" en `docs/traceability/matrix.md`.

---

## Decisiones técnicas relevantes

| Decisión | Contexto |
|----------|----------|
| `NotificacionPort` extendido con `materia_nombre` en ambos métodos (`notificar_apertura` en `US-5.1.2`, `notificar_cierre` en `US-5.1.3`) | Notificaciones no tiene su propio `MateriaConsultaPort` — quien invoca (ya con ese puerto inyectado) lo resuelve y lo pasa directo, evitando ensanchar los puertos de Notificaciones. |
| Fake SMTP de `smoke.sh` extendido para persistir mensajes, en vez de instalar Mailhog | Decisión de Víctor 2026-09-10: el resultado que importa verificar (asunto/cuerpo/destinatario reales) es el mismo con un log de texto; Mailhog no agrega cobertura para este alcance puntual, solo cambia la experiencia de revisión. |
| Cuenta SMTP real de producción queda como ítem abierto (`CLAUDE.md`) | Evaluadas 3 variantes (cuenta institucional única, "From" delegado del Docente con riesgo de spoofing, cuenta real por Materia) — la de cuenta por Materia es la preferida pero implica un salto de alcance del diseño actual (una sola cuenta SMTP global). Se resuelve junto con la decisión mayor de infraestructura de producción, todavía pendiente institucionalmente. |
| Sin Iteración 2 del Incremento 5 | `inc5-candidatas.md` lo especifica desde el diseño: incremento corto y deliberadamente aislado, `US-5.1.3` cierra la única iteración planificada. |

---

## Retrospectiva

### ¿Qué funcionó?

- Reutilizar exactamente el mismo esqueleto de `NotificarAperturaUseCase` para
  `NotificarCierreUseCase` (`US-5.1.3`) redujo la implementación a copiar y simplificar, sin
  diseñar de nuevo el manejo de fallos "nunca lanza" ni la resolución de roster.
- El diseño de integración directa BC→BC (`ADR-006`, sin cola de eventos) resultó
  suficientemente simple de verificar en Capa 2: los pasos HTTP que ya existían por otras US
  (crear y cerrar una actividad) alcanzaron para ejercitar el flujo completo de
  Notificaciones sin agregar ningún endpoint ni paso nuevo al smoke test.
- Evaluar las variantes de cuenta SMTP real con Víctor antes de escribir código evitó
  construir algo (credenciales por Materia) contra un entorno de producción que todavía no
  existe.

### ¿Qué fue más difícil de lo esperado?

- El `fake_smtp.py` original descartaba cada mensaje sin persistirlo — nadie lo había
  necesitado hasta esta UAT de cierre, porque los tests de integración/BDD ya usaban su
  propio stub con buffer. Extenderlo para la UAT reveló que el criterio de aceptación
  original ("que no rompa con 500") nunca verificó contenido real end-to-end contra el
  backend completo corriendo.

### ¿Qué ajustar en el próximo incremento?

- La decisión de la cuenta SMTP real de producción sigue abierta — no bloquea nada mientras
  el proyecto corra con datos de prueba, pero conviene resolverla junto con la decisión mayor
  de infraestructura antes de que haya usuarios reales.
- El backlog de `DesignReviewer` sigue subiendo sin una iteración dedicada a bajarlo (176 en
  esta baseline, 161 en `BL-008`) — mismo ítem ya señalado en la retrospectiva de `BL-008`,
  todavía sin resolver.

---

*Creado: 2026-09-10*
