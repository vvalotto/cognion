# Traceability Matrix — Cognion

> Estado documental: vigente
> Fuente de verdad para: trazabilidad RF → BC → Incremento → US-IEDD → estado, y escenarios de
> calidad (RNF) → BC/alcance → Incremento → estado
> Última actualización: 2026-08-26 — Cierre de la Iteración 0 (Modelado) del Incremento 3
> (`US-3.0.1` event storming + `US-3.0.2` wireframes/prototipo del flujo de período abierto,
> ambos aprobados por Víctor). RF-11, RF-11b, RF-12 y RF-13 pasan de Planificado a
> **Especificado** — el modelo de dominio y la UX ya están aprobados aunque las US-IEDD de
> feature de las Iteraciones 1 a 3 todavía no se escribieron. RNF-DISP-2 y RNF-CONF-1 (§4)
> pasan también a Especificado, con su mecanismo concreto ya definido en
> `docs/design/domain/BC-actividad-evaluativa-modelo.md`.
>
> 2026-08-23 — Cierre de `BL-003` (Incremento 2): backend y frontend de
> ambas iteraciones (Banco de Preguntas + Cuentas), `SP-ADJ-01` y el ajuste UX en vivo del
> 2026-08-23 completos, UAT formal aprobada (`quality/reports/uat/inc2/`, Iteración 1 e
> Iteración 2), ArchitectAnalyst leído (`should_block: false`). **RF-03, RF-04, RF-05, RF-06 y
> RF-19 pasan a "Validado"**, referenciando `.cm/baselines/BL-003-banco-preguntas-cuentas.md`.
> El merge `develop → main` y el tag `v0.4.0` quedan diferidos (mismo ítem abierto de
> infraestructura/Docker que `BL-001`/`BL-002`) — "Validado" certifica tests + UAT + baseline
> registrada, no requiere el deploy a `main` (ver estados normalizados en §2).
>
> 2026-08-19 — Iteración 2 del Incremento 2 (BC Identidad, gestión de
> cuentas por administrador y cambio de contraseña propio, `US-2.2.1` a `US-2.2.9`) modelada
> (wireframes) y especificada. RF-03 y RF-19 pasan de "Planificado" a "Especificado" — specs
> recién creadas, sin código todavía. El event storming ya estaba completo desde
> `BC-identidad-modelo.md` (§3, §9, §11); solo faltaba el wireframe
> (`docs/design/ux/wireframes-cuentas-administracion.md`), aprobado por Víctor en esta misma
> sesión.
>
> 2026-08-13 — `US-2.1.7` (Docente filtra el banco por materia, unidad,
> tema, dificultad e importancia, backend) cerrada. Es la única US-IEDD de backend de RF-06 —
> **RF-06 pasa a "Implementado (backend) — frontend Especificado"**, mismo criterio usado para
> RF-01/RF-02/RF-04/RF-05.
>
> 2026-08-12 — `US-2.1.6` (Docente elimina —baja lógica— una pregunta,
> backend) cerrada. Ninguno de los RF de `RF_v1.md` (RF-04 carga, RF-05 tipos+edición, RF-06
> metadatos+filtrado) menciona explícitamente la eliminación de preguntas — `US-2.1.6` no
> mueve ninguna fila de esta tabla, mismo criterio usado para `US-2.1.2` (US técnica sin RF
> propio). Queda documentada aquí por completitud del BC (INV-BP-04, baja lógica).
>
> 2026-08-12 — `US-2.1.5` (Docente edita una pregunta existente,
> backend) cerrada. Las tres US-IEDD de backend de RF-05 (`US-2.1.3`, `US-2.1.4`, `US-2.1.5`)
> están implementadas — **RF-05 pasa a "Implementado (backend) — frontend Especificado"**,
> mismo criterio usado para RF-01/RF-02/RF-04.
>
> 2026-08-08 — `US-2.1.4` (Docente carga una pregunta de
> Verdadero/Falso, backend) cerrada. Las tres US-IEDD de backend de RF-04 (`US-2.1.1`,
> `US-2.1.3`, `US-2.1.4`) están implementadas — **RF-04 pasa a "Implementado (backend) —
> frontend Especificado"**, mismo criterio usado para RF-01/RF-02 en BC Identidad. RF-05
> sigue "Especificado": su backend depende también de `US-2.1.5` (editar pregunta), todavía
> sin implementar.
>
> 2026-07-31 — Iteración 1 del Incremento 2 (BC Banco de Preguntas,
> `US-2.1.1` a `US-2.1.13`, backend y frontend) especificada y aprobada por Víctor. RF-04,
> RF-05 y RF-06 pasan de "Planificado" a "Especificado" — specs recién creadas, sin código
> todavía. `US-2.1.2` (refactor técnico de `Comisión.materia`, BC Identidad) no tiene RF propio
> — no mueve ninguna fila de esta tabla, igual que `US-1.1.0` en su momento.
>
> 2026-07-24 — Iteración 2 (frontend de Identidad, `US-1.1.6` a
> `US-1.1.9`) especificada y aprobada por Víctor. RF-01/RF-02 quedan "Implementado" — ese
> estado certifica el backend (código integrado en `develop`, ver §2), que ya está completo y
> probado. El frontend correspondiente todavía está en "Especificado" (specs recién creadas,
> sin código todavío) y se rastrea en la misma columna US-IEDD de cada fila. Ninguna de las
> dos filas puede pasar a "Validado" hasta que también el frontend esté implementado —
> criterio de cierre de baseline en `docs/plans/PLAN-CM.md` §7 (decisión 2026-07-24). `US-1.1.0`
> no tiene RF propio (ver nota en §3), por eso su implementación no mueve ninguna fila de esta
> tabla.
> Jerarquía de autoridad: `docs/plans/PLAN-CM.md` §6

---

## 1. Propósito

Esta matriz conecta cada Requerimiento Funcional (RF, ver `docs/rf/RF_v1.md`) con el
Bounded Context responsable, el Incremento de `docs/rf/PLAN_v1.md` donde se implementa, y la
US-IEDD que lo especifica.

También rastrea los escenarios de calidad de `docs/rf/RNF_v1.md` (§4) — un RF puede estar
"Validado" y aun así el escenario de calidad asociado (ej. rendimiento del ranking en vivo)
seguir "Planificado" hasta el incremento donde ese atributo se verifica bajo carga real. Sin
esta sección, un RNF podía quedar sin dueño explícito de incremento — el mismo problema que la
matriz ya resuelve para los RF.

## 2. Estados normalizados (obligatorios — ver `docs/plans/PLAN-CM.md` §6)

| Estado | Significado | Autoridad que lo certifica |
|---|---|---|
| **Planificado** | Existe intención en `PLAN_v1.md`, sin especificación formal | `docs/plans/` |
| **Especificado** | Tiene US-IEDD con precondición/postcondición/invariantes | `docs/specs/` |
| **Implementado** | Código integrado en `develop` | Tests unitarios pasando + revisión de código |
| **Validado** | Tests + UAT + baseline de cierre | `.cm/baselines/` |

No usar "definido" sin calificar a cuál de estos cuatro corresponde.

## 3. Matriz

| RF | BC | Incremento | US-IEDD | Estado |
|---|---|---|---|---|
| RF-01 | Identidad | 1 | US-1.1.1, US-1.1.2, US-1.1.3 (backend); US-1.1.6, US-1.1.8 (frontend) | Validado |
| RF-02 | Identidad | 1 | US-1.1.4, US-1.1.5 (backend); US-1.1.6, US-1.1.7 (frontend) | Validado |
| RF-03 | Identidad | 2 | US-2.2.1, US-2.2.2, US-2.2.3, US-2.2.4 (backend); US-2.2.6, US-2.2.7, US-2.2.9 (frontend) | Validado |
| RF-04 | Banco de preguntas | 2 | US-2.1.1, US-2.1.3, US-2.1.4 (backend); US-2.1.8, US-2.1.9, US-2.1.11 (frontend) | Validado |
| RF-05 | Banco de preguntas | 2 | US-2.1.3, US-2.1.4, US-2.1.5 (backend); US-2.1.11, US-2.1.12 (frontend) | Validado |
| RF-06 | Banco de preguntas | 2 | US-2.1.7 (backend); US-2.1.10 (frontend) | Validado |
| RF-07 | Banco de preguntas | 7 | — | Planificado |
| RF-08 | Actividad Evaluativa | 6 | — | Planificado |
| RF-09 | Actividad Evaluativa | 6 | — | Planificado |
| RF-10 | Actividad Evaluativa | 6 | — | Planificado |
| RF-11 | Actividad Evaluativa | 3 | US-3.0.1, US-3.0.2 (modelado) | Especificado |
| RF-11b | Actividad Evaluativa | 3 | US-3.0.1, US-3.0.2 (modelado) | Especificado |
| RF-12 | Actividad Evaluativa | 3 | US-3.0.1, US-3.0.2 (modelado) | Especificado |
| RF-13 | Actividad Evaluativa | 3 | US-3.0.1, US-3.0.2 (modelado) | Especificado |
| RF-14 | Notificaciones | 5 | — | Planificado |
| RF-15 | Analytics | 4 | — | Planificado |
| RF-16 | Analytics | 4 | — | Planificado |
| RF-17 | Analytics | 4 | — | Planificado |
| RF-18 | Analytics | 7 | — | Planificado |
| RF-19 | Identidad | 2 | US-2.2.1, US-2.2.5 (backend); US-2.2.8, US-2.2.9 (frontend) | Validado |

> RF-19 agregado 2026-07-17 (elicitación dedicada, ver `docs/rf/RF_v1.md` revisión 2026-07-17
> y `docs/design/domain/BC-identidad-modelo.md` §11) — agrupado con RF-03 en el Incremento 2.

> La columna US-IEDD se completa a medida que se elaboran las US candidatas de cada
> Incremento (`docs/plans/incN/incN-candidatas.md`) — ver `docs/plans/WORKFLOW-DESARROLLO.md` §3.

> `US-1.1.0` (alta de usuarios, comisión y asignación de docentes) no tiene RF propio — surgió
> como necesidad derivada del event storming (`BC-identidad-modelo.md` §6, §9) y es
> precondición técnica de RF-01/RF-02, por eso no aparece en la columna US-IEDD de ninguna
> fila. Detalle en `docs/plans/inc1/inc1-candidatas.md`. **Estado: Implementado** — mergeada a
> `develop` el 2026-07-21 (PR #11, `docs/reports/inc1/US-1.1.0-report.md`), 37/37 tests,
> quality gates APROBADO. Con la precondición resuelta, `US-1.1.1` (Docente genera invitación)
> queda desbloqueada como siguiente paso de la Iteración 1.

> `US-1.1.1` (Docente genera invitación) — implementada (`docs/plans/inc1/US-1.1.1-plan.md`),
> 53/53 tests, quality gates APROBADO.

> `US-1.1.2` (Estudiante se registra con invitación válida) — implementada en backend
> (`docs/plans/inc1/US-1.1.2-plan.md`), 77/77 tests, quality gates APROBADO. Frontend
> diferido a una US-IEDD separada (ver nota de alcance en el plan).

> `US-1.1.3` (Estudiante intenta registrarse con link vencido o inválido) — implementada en
> backend (`docs/plans/inc1/US-1.1.3-plan.md`), 85/85 tests (excluyendo el escenario de UI
> diferido), quality gates APROBADO. Refina `InvitacionNoValida` (guard genérico de
> `US-1.1.2`) en `InvitacionInvalida`, `InvitacionVencida`, `InvitacionYaUsada`. Frontend
> (`RegistroError.tsx`) diferido a la misma US-IEDD de frontend que ya difería
> `Registro.tsx`/`RegistroExito.tsx`. **RF-01 pasa a Implementado** — las tres US-IEDD que
> requería están cerradas en backend.

> `US-1.1.4` (Docente, administrador y estudiante se autentican y reciben un JWT con su rol)
> — implementada en backend (`docs/plans/inc1/US-1.1.4-plan.md`), 107/107 tests, quality
> gates APROBADO. Frontend diferido (mismo criterio que US-1.1.2/US-1.1.3).

> `US-1.1.5` (El sistema restringe el acceso según el rol del usuario autenticado) —
> implementada en backend (`docs/plans/inc1/US-1.1.5-plan.md`), 132/132 tests (suite
> completa del proyecto), quality gates APROBADO. `get_current_user`/`require_rol` aplicados
> a los endpoints de `US-1.1.0` (`administrador`) y `US-1.1.1` (`docente`); `/identidad/login`
> y `/identidad/registro` permanecen públicos. **RF-02 pasa a Implementado** — las dos US-IEDD
> que requería (`US-1.1.4`, `US-1.1.5`) están cerradas en backend. Con esto, la Iteración 1
> del Incremento 1 queda completa (todas las US de `docs/plans/inc1/inc1-candidatas.md`
> §Iteración 1 implementadas).

> **Iteración 2 — Frontend de Identidad** (`US-1.1.6` a `US-1.1.9`) especificada y aprobada
> por Víctor el 2026-07-24 (`docs/plans/inc1/inc1-candidatas.md` §Iteración 2, Issues #23–#26).
> Decisión de cierre de baseline: BL-002 no abre hasta que estas cuatro US también estén
> implementadas (`docs/plans/PLAN-CM.md` §7) — RF-01 y RF-02 permanecen "Implementado (backend)"
> hasta entonces, no pasan a "Validado". Fuera de alcance de esta iteración: UI de
> `CrearComision`/`AsignarDocenteAComision`, deferida sin fecha (el wireframe la deja
> explícitamente sin resolver).

> `US-1.1.6` (Infraestructura de frontend) — implementada
> (`docs/plans/inc1/US-1.1.6-plan.md`), 16/16 tests frontend, quality gates APROBADO
> (`quality/reports/inc1/US-1.1.6-quality.json`). Agrega Vitest + React Testing Library al
> proyecto (decisión tomada en Fase 0 — no existía estrategia de testing de frontend). Sin
> RF propio, igual que `US-1.1.0` — es precondición técnica de `US-1.1.7`/`US-1.1.8`/`US-1.1.9`,
> por eso no mueve ninguna fila de la matriz.

> `US-1.1.7` (Docente/Administrador/Estudiante inicia sesión desde la UI) — implementada
> (`docs/plans/inc1/US-1.1.7-plan.md`), 21/21 tests frontend (suite completa), quality gates
> APROBADO (`quality/reports/inc1/US-1.1.7-quality.json`). `Login.tsx` consume
> `POST /identidad/login` (`US-1.1.4`), guarda la sesión y redirige por rol; `LoginError.tsx`
> es un componente inline (mismo `/login`, no ruta separada) con el mensaje genérico que no
> distingue email inexistente de contraseña incorrecta. **RF-02 pasa a Implementado** (backend
> + frontend) — las dos US-IEDD de frontend que requería (`US-1.1.6`, `US-1.1.7`) están
> cerradas. RF-01 sigue "Implementado (backend) — frontend Especificado" hasta que se
> implemente `US-1.1.8`. BL-002 sigue sin abrir — falta también `US-1.1.9`
> (`docs/plans/PLAN-CM.md` §7). Próxima: `US-1.1.8` (registro con invitación).

> `US-1.1.8` (Estudiante se registra desde la UI con un link de invitación) — implementada
> (`docs/plans/inc1/US-1.1.8-plan.md`), 30/30 tests frontend (suite completa) + 71/71
> unitarios y 38/38 integración de backend, quality gates APROBADO
> (`quality/reports/inc1/US-1.1.8-quality.json`). `Registro.tsx` consume
> `POST /identidad/registro` (`US-1.1.2`/`US-1.1.3`); `RegistroError.tsx`/`RegistroExito.tsx`
> son pantallas completas (no inline, a diferencia de `LoginError.tsx`), coherente con el
> wireframe (§2.4/§2.5). Ampliación de backend acordada con Víctor durante la Fase 2 (fuera
> del alcance original "sin cambios de backend" de la spec, documentada como adenda en
> `docs/specs/inc1/US-1.1.8.md`): `RegistroResponse.materia`, para poder mostrar el nombre de
> la comisión en la pantalla de éxito — el wireframe lo requiere y antes solo se exponía
> `comision_id` (UUID). **RF-01 pasa a Implementado** (backend + frontend) — las dos US-IEDD
> de frontend que requería (`US-1.1.6`, `US-1.1.8`) están cerradas. BL-002 sigue sin abrir —
> falta `US-1.1.9` (`docs/plans/PLAN-CM.md` §7). Próxima: `US-1.1.9` (alta de Docente desde la
> UI, Administrador).
>
> **2026-07-29 — `US-1.1.9` (Administrador da de alta un Docente desde la UI) cerrada**
> (`docs/reports/inc1/US-1.1.9-report.md`, 42/42 tests frontend, quality gates APROBADO). Sin
> RF propio, igual que `US-1.1.0` (precondición operativa — sin esta pantalla, Víctor no puede
> dar de alta un Docente desde la aplicación). Gap detectado en Fase 2: el `.feature` asumía
> ruta protegida por rol, pero `router.tsx`/`AppLayout.tsx` (`US-1.1.6`) no tenían guard
> client-side — se agregó `RequireRole` (componente reutilizable), fuera del alcance original
> de la spec, documentado como adenda en `docs/specs/inc1/US-1.1.9.md`. **Cierra la
> Iteración 2 (Frontend de Identidad) — última US-IEDD pendiente. Se abre BL-002**
> (`docs/plans/PLAN-CM.md` §7).
>
> **2026-07-29 — BL-002 cerrada, RF-01 y RF-02 pasan a Validado.** UAT del Incremento 1
> aprobado sin hallazgos 🔴 Bloqueantes sin resolver — Capa 1 (132 tests backend + 46
> frontend) y Capa 2 (`smoke.sh` + UAT manual en navegador real) según
> `quality/reports/uat/inc1/design.md` y `evidencia.md`. Los dos hallazgos del UAT manual
> (CORS sin configurar, estilo no institucional) se resolvieron dentro de `US-1.1.9` antes
> de cerrar la baseline. Evidencia completa: `.cm/baselines/BL-002-bc-identidad.md`. Merge
> `develop → main` y tag `v0.3.0` diferidos — pendiente de la decisión de infraestructura
> (mismo ítem abierto que `BL-001`).

## 4. Escenarios de calidad (RNF)

IDs propios (`RNF-<atributo>-N`) porque `docs/rf/RNF_v1.md` no numera los escenarios de forma
única entre atributos. Mismos cuatro estados de la sección 2 — para un escenario de calidad,
"Validado" exige evidencia específica del atributo (medición de performance, UAT bajo carga,
revisión de API, etc.), no solo tests unitarios.

**Regla:** todo escenario debe vincularse a un ADR — ver `docs/plans/PLAN-CM.md`. La única
excepción válida es que el escenario dependa de una decisión puramente de **comportamiento de
dominio** (se vincula al RF, no a un ADR inventado) o de un **ítem abierto** sin decisión
tomada todavía (se marca "Sin ADR — pendiente", nunca se deja vacío sin explicación).

| RNF | Atributo | ADR | RNF_v1.md § | BC / Alcance | Incremento | Estado | Verificación esperada |
|---|---|---|---|---|---|---|---|
| RNF-REND-1 | Rendimiento | ADR-005 | Rendimiento, Escenario 1 | Actividad Evaluativa | 6 | Planificado | Medición server-side ≤100ms con hasta 60 clientes conectados |
| RNF-DISP-1 | Disponibilidad | ADR-010 | Disponibilidad, Escenario 1 | Actividad Evaluativa / Infraestructura | 0 (healthcheck) → 6 (cancelación a los 5 min) | Planificado | Healthcheck expuesto (Inc 0) + comportamiento de cancelación verificado en UAT de Inc 6 |
| RNF-DISP-2 | Disponibilidad | N/A — decisión de dominio (RF-11b), no arquitectónica | Disponibilidad, Escenario 2 | Actividad Evaluativa | 3 | Especificado | RF-11b (modificación de cierre en caliente) cubre el escenario — mecanismo concreto en `BC-actividad-evaluativa-modelo.md` INV-AE-04 |
| RNF-CONF-1 | Confiabilidad | ADR-009, ADR-004 | Confiabilidad | Actividad Evaluativa | 3 | Especificado | Test de reconexión sin pérdida de respuestas confirmadas — mecanismo concreto en `BC-actividad-evaluativa-modelo.md` INV-AE-09 (persistencia atómica) y wireframe `#est-rendir` |
| RNF-SEG-1 | Seguridad | ADR-007 | Seguridad | Identidad (transversal a todos los BC) | 1 | Implementado | Revisión de API — RBAC + JWT validado en cada endpoint. Mecanismo concreto (roles derivados de `perfil`, JWT sin refresh/blacklist) definido en `docs/design/domain/BC-identidad-modelo.md` (US-1.0.1, aprobado 2026-07-17). `get_current_user`/`require_rol` (`US-1.1.5`) aplicados a los endpoints de `US-1.1.0`/`US-1.1.1`; revisión formal de API queda para el cierre de Incremento |
| RNF-USA-1 | Usabilidad | ADR-011 | Usabilidad, Escenario 1 | Frontend (transversal) | Todos los incrementos con frontend | Planificado — gate cumplido para Incremento 1 | Gate UX de cada incremento — verificación de prototipo aprobado. Incremento 1: `docs/design/ux/wireframes-identidad.md` + prototipo aprobados (US-1.0.2, 2026-07-18). Estado global se mantiene "Planificado" hasta que cada incremento con frontend repita el gate |
| RNF-USA-2 | Usabilidad | ADR-011 | Usabilidad, Escenario 2 | Frontend / Actividad Evaluativa en vivo | 6 | Planificado — ⚠️ ítem abierto, criterio a definir en diseño UX antes del Incremento 6 (ver `CLAUDE.md`) | Validación humana en dispositivo real (proyección en aula) |
| RNF-MANT-1 | Mantenibilidad | ADR-001 | Mantenibilidad | Banco de preguntas | 2 | Planificado — ⚠️ depende del modelo polimórfico de tipos de pregunta, a resolver en la Iteración 0 — Modelado | Spike de incorporación de un tipo nuevo en ≤ 1 jornada |
| RNF-OBS-1 | Observabilidad | ADR-002, ADR-010 | Observabilidad | Actividad Evaluativa | 3 | Planificado | Reconstrucción de una actividad evaluativa desde el event store, verificada en UAT |
| RNF-ADM-1 | Administrabilidad | ADR-008 | Administrabilidad, Escenario 1 | Infraestructura | 0 | Implementado | Pipeline de GitHub Actions ya integrado en `develop` (CI/CD + Docker) |
| RNF-ADM-2 | Administrabilidad | Sin ADR — pendiente, no hay decisión de infraestructura de producción todavía | Administrabilidad, Escenario 2 | Infraestructura | Sin asignar | Planificado — ⚠️ ítem abierto, depende de la decisión de infraestructura de producción (ver `CLAUDE.md`) | Backup mensual verificado una vez resuelta la infraestructura definitiva |

> Los escenarios marcados con ⚠️ dependen de un ítem abierto listado en `CLAUDE.md` — no
> deberían pasar de "Planificado" hasta que ese ítem se resuelva. Cuando esa decisión de
> infraestructura se tome, RNF-ADM-2 debe ganar su propio ADR antes de avanzar de estado.
