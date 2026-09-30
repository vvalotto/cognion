# BL-010 — Incremento 5-ADJ: Identidad Autoservicio y Analytics del Docente

| Campo | Valor |
|-------|-------|
| Tipo | Incremento (fuera de secuencia, `PLAN_v1.md` no lo numera — mismo criterio que `BL-005`/`BL-007`) |
| Fecha apertura | 2026-09-10 |
| Fecha cierre | 2026-09-17 |
| Git tag inicial | `v0.7.0` (`BL-009`) |
| Git tag cierre | `v0.7.1` (PATCH — incremento fuera de la secuencia de `PLAN_v1.md`, mismo criterio de versionado que `BL-005` → `v0.5.1` y `BL-007` → `v0.6.1`) |
| Estado | ✅ Completado — mergeado a `main` |
| DoD | Backlog de Identidad relevado por Víctor (`hallazgos-cognion.md`, 2026-09-12) resuelto de punta a punta: contraseña visible/oculta, política segura (12+ caracteres, mezcla de tipos), descubribilidad de "Cambiar contraseña", recuperación de contraseña por autoservicio (RF-24) y autoregistro con selección de perfil (RF-25). `RF-20` a `RF-23` (Analytics para el Docente: por comisión, evolución temporal, ranking de preguntas falladas, completitud por actividad) implementados backend + frontend. Documentación reconciliada con el código real (`RF_v1.md`, ADRs, modelos de dominio, wireframes, matriz de trazabilidad). |

---

## Descripción

Incremento insertado fuera de la secuencia numérica 0-7 de `PLAN_v1.md` (mismo criterio que
Incremento 3-ADJ/4-ADJ: no se renumeran los Incrementos 6-7 ya mapeados a RF), abierto
inmediatamente después de `BL-009`. Agrupa dos frentes independientes que compartían el mismo
motivo de secuenciación — backlog sin asignar antes de abrir el Incremento 6 (Sesión en Vivo):

1. **`RF-20` a `RF-23`** (Analytics) — elicitados 2026-09-09 durante la prueba manual E2E de
   estabilización posterior a `BL-007` (desempeño por comisión, evolución temporal, ranking de
   preguntas falladas, completitud por actividad).
2. **Identidad Autoservicio** — hallazgos relevados por Víctor en revisión manual
   (`hallazgos-cognion.md`, 2026-09-12): mostrar/ocultar contraseña, política de contraseña
   segura, descubribilidad de "Cambiar contraseña", recuperación de contraseña (RF nuevo,
   `RF-24`) y autoregistro de Docente/Estudiante con selección de perfil (RF nuevo, `RF-25`,
   convive con el registro por invitación existente).

Cinco iteraciones, backend y frontend juntos en cada una (Iteraciones 1 a 4), sin diferir
frontend — mismo criterio que Banco de Preguntas/Cuentas/Portal de Entrada.

- **Iteración 0 — Modelado** (`US-ADJ-32`, `US-ADJ-33`, `US-ADJ-34`), aprobadas por Víctor:
  ampliación de `BC-identidad-modelo.md` §13 (`TokenRecuperacionPassword`, comandos
  `AutoregistrarDocente`/`AutoregistrarEstudiante`, `INV-ID-11` ampliada — PR #322); ampliación
  de `BC-analytics-modelo.md` §8 (4 queries nuevas para `RF-20` a `23`, sin puertos nuevos — PR
  #324/#325); wireframes/prototipo (11 pantallas de `identidad-autoservicio.html` + 4 pantallas
  de `analytics-portal-desempeno.html` ampliado — PR #327).
- **Iteración 1 — Contraseña segura y accesible** (`US-ADJ-35` a `37`), PR #333/#335/#337: sin
  RF propio, ajuste sobre `RF-02`/`RF-19` ya Validados. `PasswordInput.tsx` compartido con
  toggle mostrar/ocultar; `INV-ID-11` ampliada a 12 caracteres + mezcla de tipos (cierra un gap
  real — `CrearUsuario`/`RegistrarEstudiante` no llamaban la validación de dominio);
  `UserMenu.tsx` como único punto de entrada por clic a "Cambiar contraseña"/"Cerrar sesión".
- **Iteración 2 — Recuperación de contraseña** (`RF-24`, `US-ADJ-38` a `40`), PR
  #343/#344/#345: endpoints públicos solicitar/confirmar (token 1 hora, `SmtpCanalEnvio` de
  Notificaciones — primera vez que Identidad depende de un puerto de Notificaciones, `ADR-006`),
  pantallas "Olvidé mi contraseña"/"Definir nueva contraseña". Fix aparte: FK de
  `TokenRecuperacionPassword` bloqueaba `EliminarCuenta` de un usuario con tokens emitidos
  (PR #346).
- **Iteración 3 — Autoregistro con selección de perfil** (`RF-25`, `US-ADJ-41` a `43`), PR
  #351/#352/#353: endpoints públicos por perfil (Docente activo de inmediato sin aprobación;
  Estudiante con `comision_id` obligatorio), pantalla de selección de perfil → formulario
  dinámico.
- **Iteración 4 — Analytics** (`RF-20` a `23`, `US-ADJ-44` a `51`): backend (PR #364) amplía
  `EvaluacionDesempenoConsultaPort` sin puertos nuevos, reutilizando
  `ObtenerDesempenoEstudianteUseCase` de `US-4.1.2` para el drill-down de `RF-20`. Frontend, PR
  #366 (`US-ADJ-48`, Desempeño por comisión con dos niveles de drill-down), #367 (`US-ADJ-49`,
  Evolución temporal — gráfico SVG a mano, sin entrada en `AppNav.tsx`), #368 (`US-ADJ-50`,
  Ranking de preguntas falladas), #369 (`US-ADJ-51`, Completitud por actividad). Decisión
  operativa de Víctor desde esta iteración: la verificación manual en navegador real deja de
  repetirse US por US — un solo pase al cierre completo de la iteración.
- **Iteración 5 — Revisión documental de cierre** (`US-ADJ-52`, sin código de producción), PR
  #373: numeración definitiva de `RF-24`/`RF-25` en `RF_v1.md`; matriz de trazabilidad (`RF-20`
  a `RF-25` a "Implementado"); nota en `ADR-012` (recuperación de contraseña ≠ recuperación de
  invitación) y `ADR-020` nuevo (autoregistro como tercera vía de alta de cuenta);
  `BC-actividad-evaluativa-modelo.md` §5 actualizado con `titulo`/`comisiones_ids`/
  `unidad_tematica`/`tema`; wireframes reconciliados con el código real.

**Hallazgos de la UAT de cierre de Iteración 4, corregidos en PR #370 (mergeado 2026-09-16)**
antes de esta baseline: alta/edición/baja de Materia pasa a ser exclusiva del Administrador
(RBAC confuso — antes también el Docente); los 4 informes de Analytics se unifican bajo un
único ítem de menú "Reportes" en `AppNav.tsx`, con landing (`Analytics.tsx`, `/analytics`);
paginación de 20 ítems en ranking/tema/comisión/detalle-por-evaluación. Un hallazgo posterior
de esta misma UAT —`HomeDocente.tsx` seguía con cards directas a "Desempeño por
alumno"/"por tema" sin pasar por "Reportes"— corregido aparte en PR #374 (2026-09-16). PR #375
(2026-09-16, sin US propia) agregó los diagramas de BC Notificaciones faltantes y corrigió
estados desactualizados en `docs/design/` detectados durante la revisión de `US-ADJ-52`.

---

## Inventario de Configuration Items

| CI | Artefacto | Tipo | Descripción |
|----|-----------|------|-------------|
| CI-D46 | `docs/design/ux/wireframes-identidad-autoservicio.md` + `prototipos/identidad-autoservicio.html` | Documento | UX de las 11 pantallas de autoservicio (`US-ADJ-34`) |
| CI-D47 | `docs/design/ux/wireframes-analytics.md` + `prototipos/analytics-portal-desempeno.html` (ampliado) | Documento | UX de las 4 pantallas nuevas de Analytics (`US-ADJ-34`) |
| CI-D48 | `docs/specs/ajustes/US-ADJ-35.md` a `US-ADJ-51.md` | Documento | Specs US-IEDD de las Iteraciones 1 a 4 |
| CI-D49 | `docs/reports/inc5-adj/US-ADJ-35-report.md` a `US-ADJ-51-report.md` | Documento | Reportes de cierre de `/implement-us` por US |
| CI-D50 | `docs/adr/ADR-020-autoregistro-docente-estudiante.md` | Documento | ADR nuevo — autoregistro como tercera vía de alta de cuenta (`US-ADJ-52`) |
| CI-D51 | `docs/adr/ADR-012-*.md` (nota de alcance agregada) | Documento | Aclaración: recuperación de contraseña ≠ recuperación de invitación (`US-ADJ-52`) |
| CI-D52 | `docs/rf/RF_v1.md` (revisión 2026-09-16) | Documento | Numeración definitiva de `RF-24`/`RF-25` |
| CI-D53 | `docs/traceability/matrix.md` | Documento | `RF-20` a `RF-25`: Planificado/Sin asignar → Implementado → Validado (esta baseline) |
| CI-C23 | `src/identidad/entities/{usuario,token_recuperacion_password}.py`, `use_cases/{solicitar_recuperacion_password,confirmar_recuperacion_password,autoregistrar_docente,autoregistrar_estudiante}.py` | Código de backend | `TokenRecuperacionPassword` (aggregate nuevo), `INV-ID-11` ampliada, comandos de recuperación y autoregistro |
| CI-C24 | `src/identidad/interface_adapters/` (`AutoregistroController`, endpoints públicos de recuperación) | Código de backend | Endpoints públicos nuevos: `POST /identidad/recuperar-password/{solicitar,confirmar}`, `POST /identidad/autoregistro/{docente,estudiante}` + 2 endpoints públicos acotados de Materia/Comisión para el selector |
| CI-C25 | `src/notificaciones/` (`CanalRecuperacionPort`/`CanalRecuperacionPortInProcess`) | Código de backend | Primera dependencia de Identidad hacia un puerto de Notificaciones (`ADR-006`) |
| CI-C26 | `src/analytics/entities/ports/evaluacion_desempeno_consulta_port.py` (ampliado), `use_cases/{obtener_desempeno_por_comision,obtener_evolucion_temporal_*,obtener_ranking_preguntas_falladas,obtener_completitud_por_actividad}.py` | Código de backend | 4 Use Case nuevos de `RF-20` a `23`, `AnalyticsCompletitudController` nuevo (separación por CBO) |
| CI-F16 | `frontend/src/components/ui/PasswordInput.tsx`, `components/UserMenu.tsx` | Código de frontend | Componentes compartidos nuevos (Iteración 1) |
| CI-F17 | `frontend/src/pages/identidad/{RecuperarPassword*,Autoregistro*}.tsx` | Código de frontend | 9 pantallas nuevas de autoservicio (Iteraciones 2 y 3) |
| CI-F18 | `frontend/src/pages/analytics/{DesempenoPorComision,EvolucionTemporal,RankingPreguntasFalladas,CompletitudActividad,Analytics}.tsx` | Código de frontend | 4 informes nuevos + landing "Reportes" (Iteración 4 + fix PR #370) |
| CI-T12 | `quality/reports/designreviewer/BL-010-designreviewer.json`, `quality/reports/architectanalyst/BL-010-arquitectura.json` | Herramienta | Salidas de cierre de esta baseline |

---

## Métricas al cerrar

**Backend:**
- `pytest tests/ --cov=src --cov-report=json`: 1197 passed (unit + integration + BDD)
- `ruff check src/`: 0 violaciones (All checks passed!)
- `mypy src/`: 0 errores (258 archivos)
- `pylint src/`: 9.57/10 (`BL-009`: 9.54/10 — leve suba, sin CRITICAL nuevo, mismo
  `duplicate-code` preexistente entre `analytics/frameworks/api/schemas` y
  `use_cases/obtener_desempeno_estudiante`)
- Cobertura: 95.49% (3471/3635 statements)

**Frontend:**
- `npx vitest run --coverage`: 497/497 passed (83 archivos de test)
- `npx oxlint`: 0 errores (6 advertencias preexistentes, sin relación con esta baseline)
- `npx tsc -b`: 0 errores
- Cobertura: 91.72% statements / 81.75% branches / 87.65% functions / 94.56% lines — por
  encima del umbral de 80% del proyecto en las 4 métricas

**Diseño:**
- `designreviewer src/ --config pyproject.toml`: 0 CRITICAL, 215 advertencias sobre 258
  archivos (`BL-009`: 176 sobre 238 — suba esperable, 3 BC nuevos de código desde entonces
  además de Analytics/Identidad ampliados, sin cluster relevante nuevo)
- `architectanalyst src/ --sprint-id BL-010`: 7 CRITICAL (`DistanceAnalyzer`, "Zone of Pain"),
  uno por cada paquete raíz de BC — sube de 6 (`BL-006`) a 7 por `notificaciones` como séptimo
  módulo del patrón. Mismo falso positivo aceptado permanentemente desde `US-ADJ-13`/`19`
  (`CLAUDE.md` §Quality gates): bug de `DependencyGraphBuilder` que deja `Ca=Ce=0` para todo el
  proyecto — `should_block: false`, sin acción.

**Sin migraciones de esquema fuera de** `token_recuperacion_password` (tabla nueva,
`US-ADJ-38`) — sin backfill, tabla vacía al momento de la migración.

---

## UAT de cierre

Sin UAT formal consolidada de baseline (Capa 1/Capa 2 + `design.md`/`evidencia.md` en
`quality/reports/uat/inc5-adj/`) — cada iteración con código de producción (1 a 4) ya corrió su
propia verificación, documentada progresivamente en `CLAUDE.md` a medida que cerraba: 986→1116→
1148→1169→1196/1196 tests backend en verde sin regresiones a lo largo de las iteraciones, más
un pase de navegador real al cierre de la Iteración 4 (decisión operativa de Víctor
2026-09-14: dejar de repetir la verificación manual US por US) sin hallazgos 🔴 Bloqueantes,
con dos hallazgos 🟡 corregidos antes de esta baseline (PR #370, #374). Iteración 5 es
documentación pura, sin superficie que testear. Mismo criterio que `BL-005` (Incremento 3-ADJ,
"sin UAT — deuda de tooling, nada visible para un usuario final"), pero aquí por el motivo
inverso: cada pieza de producto ya tuvo su propio pase de UAT antes de llegar a esta baseline,
en vez de no requerirlo por no ser observable.

Confirmación explícita de Víctor sobre el DoD completo del incremento: Issue
[#372](https://github.com/vvalotto/cognion/issues/372), comentario de cierre 2026-09-16.

---

## Actualización de la matriz de trazabilidad

`RF-20` a `RF-25` pasan de **Implementado** a **Validado**, referenciando esta baseline
(`BL-010`) como evidencia — `docs/traceability/matrix.md` actualizado en el mismo commit que
este archivo.

---

## Retrospectiva

**Qué funcionó:**
- Backend y frontend juntos en cada iteración (sin diferir a una iteración final como en
  Actividad Evaluativa) mantuvo cada RF verificable de punta a punta apenas cerraba su
  iteración, sin acumular una Iteración 4/5 gigante de solo-frontend.
- Reutilización agresiva de infraestructura existente: `EvaluacionDesempenoConsultaPort`
  (Analytics) y `PasswordInput.tsx`/`Usuario.validar_password_nueva` (Identidad) absorbieron
  toda la funcionalidad nueva de sus iteraciones sin un solo puerto nuevo entre BCs más allá de
  `CanalRecuperacionPort` (Identidad → Notificaciones, primera vez).
- Decisión operativa de aflojar la verificación manual a un solo pase por iteración (en vez de
  US por US) desde la Iteración 4 redujo fricción sin perder cobertura — los 2 hallazgos que
  sí aparecieron (PR #370) fueron de integración entre pantallas, exactamente el tipo de
  problema que un pase consolidado detecta mejor que uno aislado por US.
- La Iteración 5 (documental, sin código) como cierre explícito evitó que la reconciliación de
  ADRs/modelos/wireframes con el código real quedara como deuda silenciosa — mismo patrón que
  ya había fallado antes (`HITO-9`) cuando nadie recorría el "camino real".

**Qué ajustar:**
- El "Zone of Pain" de `ArchitectAnalyst" sigue subiendo un crítico por cada BC nuevo (6→7 con
  `notificaciones`); sigue sin haber una vía corta para verificarlo distinto a releer la nota
  de `US-ADJ-19` cada vez — vale la pena, si el bug upstream
  ([`software_limpio#77`](https://github.com/vvalotto/software_limpio/issues/77)) no se corrige
  antes del Incremento 6, dejar un chequeo de una línea en el checklist de cierre de baseline
  que apunte directo a esa nota en vez de re-derivar la explicación.
- Sin UAT formal consolidada de baseline es una excepción justificada acá (cada pieza ya
  verificada), pero el criterio de cuándo alcanza con eso y cuándo hace falta una UAT
  consolidada nueva no está escrito en ningún lado — quedó como juicio de la sesión. Si se
  repite el patrón en el Incremento 6, documentarlo como regla explícita en
  `PROCEDIMIENTO-UAT.md`.

---

## Próximo paso

Retomar Incremento 6 (Sesión en Vivo, `PLAN_v1.md`) — Iteración 0 incluye el spike del
algoritmo de puntaje en vivo (RF-10, ítem abierto pendiente en `CLAUDE.md`).
