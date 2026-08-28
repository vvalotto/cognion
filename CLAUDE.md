# CLAUDE.md — Cognion

> Estado operativo actual del proyecto. Resume y enlaza evidencia — no duplica los documentos fuente.
> Actualizar al cierre de cada Incremento (SP-ADJ incluido).
> Jerarquía: Código y tests > Baselines > ADRs > Matriz de trazabilidad > **este archivo** > README.md
> Mapa documental y autoridad por tema, completo: `docs/inventario/DOCUMENTATION-MAP.md`.

---

## Contexto del proyecto

Plataforma web de evaluación universitaria con cuestionarios gamificados. Docente único (Víctor Valotto), materias de Ingeniería de Software y Gestión de Proyectos en FIUNER, 30–60 alumnos por comisión. Equipo de desarrollo: unipersonal.

Documentos de definición (no se modifican retroactivamente):
- `docs/rf/RF_v1.md` — 18 requerimientos funcionales
- `docs/rf/RNF_v1.md` — atributos de calidad y escenarios
- `docs/rf/ARQ_v1.md` — arquitectura de referencia, stack decidido, ADRs 001–006
- `docs/rf/PLAN_v1.md` — plan de implementación (7 incrementos, walking skeleton primero)

---

## Estado actual

**Fase:** BL-002 (Incremento 1 — BC Identidad) cerrada el 2026-07-29 en desarrollo local
(`.cm/baselines/BL-002-bc-identidad.md`). Merge `develop → main` y tag `v0.3.0` ejecutados el
2026-08-24 junto con el cierre de `BL-003` (ver más abajo) — tag retroactivo sobre el commit
real de cierre, `75e0de9`. BC Identidad completo: RF-01 (registro por
invitación) y RF-02 (autenticación y RBAC por rol) implementados de punta a punta, backend
(Iteración 1: `US-1.1.0` a `US-1.1.5`) y frontend (Iteración 2: `US-1.1.6` a `US-1.1.9`)
integrados juntos, cumpliendo el criterio de cierre de baseline de `docs/plans/PLAN-CM.md` §7
(decisión 2026-07-24 — la Baseline no cierra backend-only). Decisiones previas al incremento:
invitación con expiración de 7 días, rechazo sin recuperación automática (`ADR-012`); JWT de
60 minutos sin refresh ni blacklist (`ADR-013`); hashing bcrypt (`ADR-014`).
**US-1.1.9 (Administrador da de alta un Docente desde la UI) cerrada 2026-07-29**, PR #35
mergeado a `develop`, `docs/reports/inc1/US-1.1.9-report.md`: pantallas `AltaDocente.tsx`/
`AltaDocenteExito.tsx` + guard de ruta `RequireRole` (ampliación de scope detectada en Fase 2:
el `.feature` asumía ruta protegida, pero no había guard client-side desde `US-1.1.6`).
**UAT manual de Víctor en navegador real** detectó y corrigió dos gaps preexistentes desde
`US-1.1.6`/`1.1.7`, invisibles a Vitest: falta de `CORSMiddleware` en el backend (bloqueaba
cualquier llamada real del frontend) y un bug de cascada CSS (regla heredada sin `@layer`
pisando las utilities de Tailwind) + paleta/tipografía no institucionales — corregidos dentro
de `US-1.1.9` a pedido de Víctor. 46/46 tests frontend, quality gates APROBADO
(`quality/reports/inc1/US-1.1.9-quality.json`). Esta US cierra la Iteración 2 y el Incremento 1.
**Quality gates de cierre ejecutados:** DesignReviewer del último PR — 0 CRITICAL, 27
advertencias; ArchitectAnalyst (`quality/reports/architectanalyst/BL-002-arquitectura.json`) —
3 críticos "Zone of Pain" a nivel de paquete raíz (`identidad`, `settings`, `shared`), leídos y
aceptados, `should_block: false` (nunca bloquea, solo informa tendencias — ver retrospectiva
de `BL-002` para el detalle y el ajuste propuesto para el próximo incremento).
Incremento 2 — Banco de Preguntas en curso (`docs/plans/inc2/inc2-candidatas.md`).
Iteración 0 — Modelado cerrada 2026-07-31 (US-2.0.1 event storming, Issue #38; US-2.0.2
wireframes, Issue #39). **US-2.1.1 (Docente da de alta una Materia; banco vacío en el mismo
flujo) cerrada 2026-07-31**, PR #56 mergeado a `develop`,
`docs/reports/inc2/US-2.1.1-report.md`. **US-2.1.2 (Comisión referencia Materia por puerto,
refactor técnico de BC Identidad) cerrada 2026-08-05**, PR #62 mergeado a `develop` (merge
`8294a82`), Issue #43 cerrado, `docs/reports/inc2/US-2.1.2-report.md`: `Comisión.materia_id`
resuelto contra `MateriaPort` sin imports directos entre BCs, migración con backfill
verificada por round-trip real. El pre-push gate (`DesignReviewer`, `CBOAnalyzer`) detectó un
CRITICAL (CBO=11/10 en `RegistrarEstudianteUseCase` al inyectar `MateriaPort`) recién en la
fase de PR — no cubierto por los Quality Gates de Fase 7, que miden pylint/CC/MI/coverage pero
no acoplamiento; se corrigió moviendo la resolución del nombre de materia a
`RegistroController` (detalle de presentación, no de la regla de negocio de registro). 158/158
tests, DesignReviewer 0 CRITICAL tras el fix. **US-2.1.3 (Docente carga una pregunta de
opción múltiple en un banco) cerrada 2026-08-06**, PR #65 mergeado a `develop` (merge
`80aca29`), Issue #44 cerrado, `docs/reports/inc2/US-2.1.3-report.md`: aggregate
`PreguntaPlantillaOpcionMultiple` autovalidante (INV-BP-02 exactamente una opción correcta,
INV-BP-03 mínimo 2 opciones), `CargarPreguntaOpcionMultipleUseCase`, endpoint
`POST /preguntas/opcion-multiple` (rol `docente`). Primer tipo de pregunta implementado —
establece el patrón que sigue `US-2.1.4` sin generalizar entre tipos. 180/180 tests, quality
gates APROBADO (pylint 9.37/10, CC máx 6, MI mín 56.4, coverage 99%), pre-push gate 0
CRITICAL.
**US-2.1.4 (Docente carga una pregunta de Verdadero/Falso en un banco) cerrada 2026-08-08**,
PR #68 mergeado a `develop` (merge `40849c4`), Issue #45 cerrado,
`docs/reports/inc2/US-2.1.4-report.md`: segundo aggregate de pregunta,
`PreguntaPlantillaVerdaderoFalso` (sin invariantes adicionales sobre `respuesta_correcta`),
`CargarPreguntaVerdaderoFalsoUseCase`, endpoint `POST /preguntas/verdadero-falso` (rol
`docente`), migración `respuesta_correcta` nullable en `pregunta_plantilla`. Repitió el patrón
de `US-2.1.3` sin generalizar entre tipos de pregunta, según lo previsto. 194/194 tests, quality
gates APROBADO (pylint 9.27/10, CC máx 6, MI mín 51.47, coverage 99%).
**US-2.1.5 (Docente edita una pregunta existente) cerrada 2026-08-12**, PR #71 mergeado a
`develop` (merge `39e2a12`), Issue #46 cerrado, `docs/reports/inc2/US-2.1.5-report.md`: método
`editar(...)` en `PreguntaPlantillaOpcionMultiple`/`PreguntaPlantillaVerdaderoFalso`
(reaplica INV-BP-02/03, tipo no editable), `EditarPreguntaUseCase`, endpoint
`PUT /preguntas/{pregunta_id}` (rol `docente`). Mismo patrón de CRITICAL de CBO que
`US-2.1.2` (`CBO=11/10` en `PreguntasController` al inyectar el tercer use case), corregido
tipando el evento de retorno como `object` en el controller. 219/219 tests, quality gates
APROBADO (pylint 9.27/10, CC máx 8, MI mín 49.62, coverage 99%).
**US-2.1.6 (Docente elimina —baja lógica— una pregunta) cerrada 2026-08-12**, PR #73 mergeado a
`develop` (merge `bb5c317`), Issue #47 cerrado, `docs/reports/inc2/US-2.1.6-report.md`: método
`eliminar()` en `PreguntaPlantillaOpcionMultiple`/`PreguntaPlantillaVerdaderoFalso` (INV-BP-04,
baja lógica), `EliminarPreguntaUseCase`, endpoint `DELETE /preguntas/{pregunta_id}` (rol
`docente`). Tercera vez que el pre-push gate detecta CRITICAL de CBO en `PreguntasController`
(mismo patrón que `US-2.1.2`/`US-2.1.5`) — esta vez se corrigió extendiendo el criterio de
tipar el evento como `object` también a los dos endpoints de carga (`US-2.1.3`/`US-2.1.4`),
no solo a los nuevos. CBO baja de 11/10 a 10/10. Ninguno de los RF de `RF_v1.md` cubre
explícitamente la eliminación de preguntas — no mueve ninguna fila de la matriz de
trazabilidad, mismo criterio que `US-2.1.2`. 237/237 tests, quality gates APROBADO (pylint
9.18/10, CC máx 8, MI mín 49.62, coverage 99%).
**US-2.1.7 (Docente filtra el banco por materia, unidad, tema, dificultad e importancia)
cerrada 2026-08-13**, PR #76 mergeado a `develop` (merge `c26ce32`), Issue #48 cerrado,
`docs/reports/inc2/US-2.1.7-report.md`: método `filtrar()` agregado a `PreguntaRepositoryPort`
(solo preguntas `activa = true`, filtros opcionales combinables AND), `FiltrarBancoUseCase`,
endpoint `GET /bancos/{banco_id}/preguntas` (rol `docente`). Controller nuevo y separado
(`BancosController`) en vez de sumar un 5° use case a `PreguntasController` — ese ya estaba en
el umbral duro de CBO (10/10) tras `US-2.1.6`; detectarlo en Fase 2 evitó repetir el patrón de
CRITICAL de `US-2.1.2`/`US-2.1.5`/`US-2.1.6`. 258/258 tests, quality gates APROBADO (pylint
9.28/10, CC máx 2, MI mín 41.66, coverage 99%). Cierra completa la Iteración 1 backend
(`US-2.1.1` a `US-2.1.7`).
**US-2.1.8 (Infraestructura de frontend del Banco de Preguntas) cerrada 2026-08-14**, PR #78
mergeado a `develop` (merge `071a394`), Issue #49 cerrado,
`docs/reports/inc2/US-2.1.8-report.md`: cliente API tipado (`banco-preguntas-api.ts`, reutiliza
`apiFetch`/JWT/401/403 de `US-1.1.6`, mapea snake_case↔camelCase), 7 rutas nuevas en
`router.tsx` protegidas con `RequireRole rol="docente"` (`US-1.1.9`), placeholder temporal
hasta que `US-2.1.9` a `US-2.1.13` las reemplacen. **Gap detectado en Fase 2 (planificación,
antes de escribir código):** el backend no expone `GET /materias` (listado) — solo
`POST /materias` (`US-2.1.1`); la spec de `US-2.1.9` asumía que ya existía. Decisión de
Víctor: excluir `listarMaterias` del alcance de esta US. 65/65 tests frontend, quality gates
APROBADO (oxlint 0 errores, `tsc --noEmit` 0 errores, coverage 100% en `banco-preguntas-api.ts`).
**US-2.1.9 (Docente ve el listado de materias y da de alta una nueva) cerrada 2026-08-14**,
PR #80 mergeado a `develop` (merge `98deff7`), Issue #50 cerrado,
`docs/reports/inc2/US-2.1.9-report.md`: resuelve el gap de `US-2.1.8` — `GET /materias`
(nuevo), `ListarMateriasUseCase` (reutiliza `PreguntaRepositoryPort.filtrar()` para el conteo
de preguntas activas por materia, sin ensanchar ese puerto), métodos nuevos
`MateriaRepositoryPort.listar()` y `BancoRepositoryPort.obtener_por_materia_id()`. Frontend:
`listarMaterias()`, pantallas `Materias.tsx`/`NuevaMateria.tsx`, reemplazando los placeholders
de `US-2.1.8`. 225/225 tests backend, 73/73 frontend, quality gates APROBADO (pylint 9.96/10,
CC máx 3, MI mín 55.56, coverage 100% backend / 100%-93.33% en las pantallas nuevas). Smoke
test manual en navegador real confirmado (login docente, alta de materia, listado).
**US-2.1.10 (Docente ve y filtra el banco de preguntas de una materia) cerrada 2026-08-16**,
PR #82 mergeado a `develop` (merge `641be0d`), `docs/reports/inc2/US-2.1.10-report.md`:
frontend puro, sin cambios de backend — consume `GET /bancos/{id}/preguntas` (`US-2.1.7`) y
`GET /materias` (`US-2.1.9`) para resolver `materiaId → nombre/bancoId` sin agregar un
endpoint dedicado. Pantalla `Banco.tsx` (tabla + filtros de unidad/tema/dificultad/
importancia) reemplaza el placeholder de `US-2.1.8` en `/materias/:materiaId/banco`; acciones
"Editar"/"+ Nueva pregunta" apuntan a rutas placeholder pendientes de `US-2.1.11`–`US-2.1.13`,
"Eliminar" deshabilitado (sin ruta de confirmación todavía). 80/80 tests frontend, quality
gates APROBADO (oxlint 0 errores, `tsc --noEmit` 0 errores, coverage 95.55%/89.28%/89.47% en
`Banco.tsx`).
**US-2.1.11 (Docente carga una pregunta eligiendo su tipo) cerrada 2026-08-16**, PR #84
mergeado a `develop` (merge `45c6b25`), Issue #52 cerrado,
`docs/reports/inc2/US-2.1.11-report.md`: frontend puro, sin cambios de backend — consume
`POST /preguntas/opcion-multiple`/`POST /preguntas/verdadero-falso` (`US-2.1.3`/`US-2.1.4`) y
`GET /materias` (`US-2.1.9`) para resolver `materiaId → bancoId`. 3 pantallas nuevas
(`NuevaPreguntaTipo.tsx`, `NuevaPreguntaOpcionMultiple.tsx`, `NuevaPreguntaVerdaderoFalso.tsx`)
reemplazan los 3 placeholders de "+ Nueva pregunta" en `router.tsx`; validación de cliente
(INV-BP-02/03) antes de enviar; unidad temática como texto libre — sin catálogo ni endpoint de
origen, mismo criterio que `US-2.1.8`. 89/89 tests frontend, quality gates APROBADO (oxlint 0
errores, `tsc --noEmit` 0 errores, coverage 100%/83.33%/90.47% en las 3 pantallas nuevas).
**US-2.1.12 (Docente edita una pregunta existente) cerrada 2026-08-17**, PR #86 mergeado a
`develop`, Issue #53 cerrado: pantalla `EditarPregunta.tsx` prellenada según el tipo concreto
de la pregunta, reutiliza `PUT /preguntas/{id}` (`US-2.1.5`) y `filtrarBanco()` (`US-2.1.7`)
sin backend nuevo; reemplaza el placeholder de "Editar" en `Banco.tsx`. 97/97 tests frontend,
quality gates APROBADO (oxlint 0 errores, `tsc --noEmit` 0 errores, coverage 90.52% en
`EditarPregunta.tsx`).
**US-2.1.13 (Docente elimina —baja lógica— una pregunta desde la UI) cerrada 2026-08-17**, PR
#87 mergeado a `develop`, Issue #54 cerrado: pantalla `EliminarPregunta.tsx` con confirmación
explícita ("no afecta sesiones pasadas"), reutiliza `DELETE /preguntas/{id}` (`US-2.1.6`);
habilita el botón "Eliminar" deshabilitado desde `US-2.1.10`. 103/103 tests frontend. Cierra
completa la Iteración 1 del Incremento 2, backend y frontend juntos.

**UAT de cierre de la Iteración 1 ejecutada 2026-08-17/18** (`quality/reports/uat/inc2/`):
Capa 1 (270 pytest + 103 Vitest) y Capa 2 (`smoke.sh` extendido con el flujo de Banco de
Preguntas) en verde; recorrido en navegador real primero por la sesión, luego por Víctor en
persona con el banco de la materia "Ingeniería de Software" cargado con contenido real (70
preguntas de un `.docx` docente + 1 previa, 71 en total) para ejercitar volumen realista, no
solo fixtures mínimos. La UAT dejó tres no conformidades registradas (`evidencia.md`), todas
🟡 Observación, ninguna 🔴 Bloqueante, especificadas como US de ajuste (`SP-ADJ`,
`docs/specs/ajustes/`) sin Issue de GitHub ni incremento asignado todavía:
- **US-ADJ-01** (`HITO-4`): las pantallas de Banco de Preguntas no reproducen el lenguaje
  visual del prototipo aprobado (cards, tags de color, breadcrumb) — deuda de calidad, no
  implementada.
- **US-ADJ-02** (`HITO-5`): Unidad temática/Tema como combobox derivado del banco actual en
  vez de texto libre — **implementada y mergeada 2026-08-18**, PR #88 a `develop` (merge
  `cfa65d8`): `<datalist>` nativo en carga, edición y filtros (`Banco.tsx`), reusa
  `GET /bancos/{id}/preguntas` sin endpoint nuevo. 106/106 tests frontend.
- **US-ADJ-03** (`HITO-6`): el banco sin paginación no aguanta volumen real (71 preguntas en
  una sola tabla) — especificada, no implementada. Decisiones ya tomadas: página de 20,
  paginación en backend, `fecha_creacion` nueva (backfill con timestamp único de migración),
  reset a página 1 al cambiar filtros, UI de números de página + Anterior/Siguiente. Requiere
  actualizar `wireframes-banco-preguntas.md` (gate UX) antes de tocar `frontend/`.

**Decisión de secuencia:** `US-ADJ-01`/`US-ADJ-03` no se implementan en paralelo a la
Iteración 2 — se agrupan en una única iteración de ajuste conjunta después de cerrar la
Iteración 2 completa (backend + frontend) y su propia UAT, mismo criterio de "no fragmentar en
mini-ajustes" ya aplicado en Identidad.

Incremento 2 — Iteración 2 (RF-03, RF-19: gestión de cuentas por administrador y cambio de
contraseña propio) en curso, backend casi completo (`docs/plans/inc2/inc2-candidatas.md`
§Iteración 2). Wireframes/prototipo de `docs/design/ux/wireframes-cuentas-administracion.md`
aprobados por Víctor 2026-08-19 — cubren el gap que `wireframes-identidad.md` §4 dejaba fuera
de alcance; no hizo falta una nueva US de Modelado de dominio (el event storming de
`BC-identidad-modelo.md` §3/§9/§11 ya alcanzaba).
**US-2.2.1 (Bloqueo automático de cuenta por 3 intentos fallidos consecutivos de login)
cerrada 2026-08-19**, PR #92 + PR #93 (fix de rutas `context.md`/`plan.md`) mergeados a
`develop`, Issue #91 cerrado, `docs/reports/inc2/US-2.2.1-report.md`: `Usuario` gana
`bloqueada`/`intentos_fallidos_login`/`intentos_fallidos_password`, evento `CuentaBloqueada`,
`UsuarioRepositoryPort.actualizar()` nuevo (distinto de `guardar()`, lo reutilizan
`US-2.2.4`/`US-2.2.5`). 281/281 tests, quality gates APROBADO.
**US-2.2.2 (Administrador ve el listado de cuentas, filtra por rol/estado/búsqueda) cerrada
2026-08-19**, PR #95 mergeado a `develop`, Issue #94 cerrado,
`docs/reports/inc2/US-2.2.2-report.md`: mismo patrón de CRITICAL de CBO que
`US-2.1.2`/`US-2.1.5`/`US-2.1.6`/`US-2.1.7` (esta vez sobre `UsuarioRepositoryPort` al
diseño original) — resuelto separando la consulta en `CuentaQueryPort`/
`SQLAlchemyCuentaQueryRepository` propios (command/query), no forzando el método en el
repositorio existente. `CuentasController` nuevo, separado de `UsuariosController`. Tests
pasando (ver reporte), quality gates APROBADO.
**US-2.2.3 (Administrador ve el detalle de una cuenta) cerrada 2026-08-19**, PR #97 mergeado a
`develop`, Issue #96 cerrado, `docs/reports/inc2/US-2.2.3-report.md`: `Usuario.creado_en`
agregado (gap de spec detectado y resuelto con Víctor en la sesión, no excluido de alcance),
`ObtenerCuentaUseCase` reutiliza `obtener_por_id()` existente — el pre-push gate no repitió el
CRITICAL de CBO de `US-2.2.2` por diseñar la separación command/query desde el inicio.
305/305 tests, quality gates APROBADO.
**US-2.2.4 (Administrador resetea la contraseña de una cuenta, desbloqueo incluido) cerrada
2026-08-20**, PR #98 mergeado a `develop`, Issue #99 cerrado,
`docs/reports/inc2/US-2.2.4-report.md`: `Usuario.validar_password_nueva()` (INV-ID-11, primera
vez que se enforza del lado del dominio, reutilizable por `US-2.2.5`) y
`usuario.resetear_password()` (mutación de estado pura) separados para que la entidad no
dependa del hasher; `ResetearPasswordUseCase` es el tercer método inyectado en
`CuentasController` sin llegar a CRITICAL de CBO. 329/329 tests, quality gates APROBADO.

**US-2.2.5 (Usuario autenticado cambia su propia contraseña) cerrada 2026-08-20**, PR #106
mergeado a `develop`, Issue #100 cerrado: reutiliza `Usuario.validar_password_nueva()` de
`US-2.2.4` y el contador propio `intentos_fallidos_password` de `US-2.2.1`. Cierra completo
el backend de la Iteración 2.
**US-2.2.6 (Administrador ve y filtra el listado de cuentas — UI) cerrada 2026-08-20**, PR
#107 mergeado a `develop`, Issue #101 cerrado: consume `GET /usuarios?filtros` (`US-2.2.2`).
**US-2.2.7 (Administrador ve el detalle de una cuenta y resetea/desbloquea — UI) cerrada
2026-08-20**, PR #108 mergeado a `develop`, Issue #102 cerrado: consume `GET /usuarios/{id}`
(`US-2.2.3`) y `POST /usuarios/{id}/resetear-password` (`US-2.2.4`).

**US-2.2.8 (Cualquier usuario autenticado cambia su propia contraseña — UI) cerrada
2026-08-20**, branch `feature/US-2.2.8-cambiar-password-ui`, Issue #103: consume `PUT
/usuarios/me/password` (`US-2.2.5`), pantalla accesible a los tres roles, sin `RequireRole`.
**Gap detectado en Fase 2** (antes de escribir código): la spec asumía que el backend exponía
`intentos_fallidos_password` en el error — no era así (`detail` string genérico). Decisión de
Víctor: extender el backend (`Usuario.intentos_restantes_cambio_password()`,
`PasswordActualIncorrecta.intentos_restantes`, `perfil_router.py`), manteniendo los status
codes 401/403 ya testeados por `US-2.2.5` — el `detail` pasa de string a objeto estructurado.
**Ajuste detectado en Fase 3** (al correr la suite de `US-2.2.5` antes de dar por cerrado el
plan): el plan original proponía 403 para el 3er fallo consecutivo, pero
`test_us_2_2_5_steps.py` ya afirmaba 401 en ese caso — corregido antes de tocar tests
existentes. Segundo hallazgo de diseño: el interceptor global de 401 de `api-client.ts`
(limpia sesión, navega a `/login`) rompía el criterio "no requiere volver a iniciar sesión" —
resuelto con una opción `handleUnauthorized: false` en `apiFetch`, sin cambiar ningún caller
existente. 357/357 tests backend, 145/145 tests frontend, quality gates APROBADO
(`quality/reports/inc2/US-2.2.8-quality.json`), pre-push gate (DesignReviewer) 0 CRITICAL.

**US-2.2.9 (Login refleja el estado de cuenta bloqueada — UI) cerrada 2026-08-21**, branch
`feature/US-2.2.9-login-cuenta-bloqueada`, Issue #104: frontend puro, sin cambios de backend —
`POST /identidad/login` ya distinguía 403 (`CuentaBloqueadaError`) de 401
(`CredencialesInvalidas`) desde `US-2.2.1`. **Gap detectado en Fase 2**: la spec asumía
`frontend/src/lib/auth-api.ts`, que no existe — `Login.tsx` llama `apiFetch` directamente, sin
capa intermedia. Decisión: distinguir el caso por `ApiError.status === 403` en `Login.tsx`, sin
crear el archivo ni tocar `src/`. `LoginCuentaBloqueadaError.tsx` (alerta destructiva,
`wireframes-cuentas-administracion.md` §2.8) + formulario completo deshabilitado (`fieldset`)
cuando la cuenta está bloqueada. 148/148 tests frontend, quality gates APROBADO
(`quality/reports/inc2/US-2.2.9-quality.json`). **Cierra completa la Iteración 2 del
Incremento 2, backend y frontend juntos.**

**UAT de cierre de la Iteración 2 ejecutada 2026-08-21** (`quality/reports/uat/inc2/`,
`design-iter2.md`/`evidencia-iter2.md`): Capa 1 (357 pytest + 148 Vitest) en verde sin
regresiones; Capa 2 (`smoke.sh` extendido con el flujo completo de bloqueo automático →
detección por Administrador → reseteo → desbloqueo, `US-2.2.1` a `US-2.2.5`) todos los pasos
en verde; recorrido en navegador real (Chrome vía claude-in-chrome, sesión de Claude Code —
confirmación humana de Víctor pendiente si la quiere agregar) sin hallazgos 🔴 Bloqueantes:
login con 3 intentos fallidos muestra la alerta "Cuenta bloqueada" (`US-2.2.9`) con el
formulario deshabilitado, el Administrador la encuentra filtrando por estado, ve el detalle
("se bloqueó automáticamente tras 3 intentos..."), resetea y desbloquea, el usuario vuelve a
loguear y cambia su propia contraseña sin necesidad de volver a iniciar sesión (`US-2.2.8`).
Sin no conformidades nuevas. **Cierra completa la Iteración 2 del Incremento 2** — segunda
mitad del Hito completa: el administrador resuelve problemas de cuentas sin depender del
docente.

**Iteración de ajuste `SP-ADJ-01` cerrada 2026-08-23** (`US-ADJ-01`/`US-ADJ-03`/`US-ADJ-04`/
`US-ADJ-05`): estilo visual alineado al prototipo aprobado (Banco de Preguntas y Cuentas) y
paginación en ambos listados. **BL-003 (Incremento 2 — Banco de Preguntas + Gestión de
Cuentas) cerrada el 2026-08-23** en desarrollo local
(`.cm/baselines/BL-003-banco-preguntas-cuentas.md`), PR #122. Quedan 3 candidatas diferidas,
fuera de esta baseline: `US-ADJ-06`/`07`/`08` (tocan `src/`, en cola para un próximo
incremento).

**Merge `develop → main` y tags de cierre ejecutados 2026-08-24**, a pedido explícito de
Víctor, manteniendo un tag por baseline para coherencia de hitos: `v0.3.0` (`BL-002`, tag
retroactivo sobre el commit real de cierre `75e0de9`) y `v0.4.0` (`BL-003`, commit `e31ee67`),
ambos en un único merge commit (`a2a2aee`). El deploy real a un entorno (Fly.io/servidor
FIUNER) sigue como decisión institucional pendiente, a evaluar hacia el final del desarrollo —
sin relación con este merge; `cd.yml` en `main`/tags solo construye la imagen Docker
(`build-and-deploy`), el `flyctl deploy` y el healthcheck post-deploy siguen comentados.

Incremento 3 — Actividad Evaluativa, período abierto — en curso
(`docs/plans/inc3/inc3-candidatas.md`). Primer Core Domain del sistema (`ARQ_v1.md`, driver 3)
y primer BC con Event Sourcing + CQRS (`ADR-002`); BC renombrado de "Sesiones" a "Actividad
Evaluativa" (`ADR-015`). Decisión 2026-08-24 (PR #135): los Incrementos 3 a 7 corren con datos
de prueba/locales, no datos reales de estudiantes — el gate de infraestructura de producción no
bloquea el arranque de este incremento.
**Iteración 0 — Modelado cerrada 2026-08-25/26**: `US-3.0.1` (event storming, Issue #137,
`docs/design/domain/BC-actividad-evaluativa-modelo.md`) y `US-3.0.2` (wireframes, Issue #138,
`docs/design/ux/wireframes-actividad-evaluativa.md`) aprobadas por Víctor. Matriz de
trazabilidad: RF-11, RF-11b, RF-12, RF-13 pasan de Planificado a Especificado.
**Iteración 1 — RF-11/RF-12: creación de actividad y set aleatorio por estudiante, cerrada
2026-08-26**, backend únicamente (el frontend de todo el incremento se difiere a la Iteración
4 — cruza las 3 iteraciones de backend, a diferencia de Banco de Preguntas). **US-3.1.1**
(técnica: infraestructura de Event Sourcing + CQRS, tabla `events` JSONB append/replay por
stream, Unit of Work por Use Case `ADR-009`, concurrencia optimista por `sequence_number`),
Issue #145. **US-3.1.2** (Docente crea una actividad de período abierto —
`CrearActividadPeriodoAbierto`, evento `ActividadEvaluativaCreada`, INV-AE-01/02/03), Issue
#146. **US-3.1.3** (Estudiante inicia su evaluación con set aleatorio de preguntas fijado
desde el inicio, reconexión idempotente sin regenerar el set — `IniciarEvaluacion`, evento
`EvaluacionIniciada`, INV-AE-05/06), Issue #147, PR #151 mergeado a `develop`: aggregate
`Evaluacion`, adapter in-process hacia Identidad/Banco de Preguntas, fix de CBO
(`IniciarEvaluacionUseCase` de 11 a 10, mismo patrón de CRITICAL en pre-push ya visto en
Incremento 2). Specs en `docs/specs/inc3/US-3.1.1.md` a `US-3.1.3.md`, reportes en
`docs/reports/inc3/`.
**Cierre de Iteración 1 verificado 2026-08-26** (PR #152 mergeado a `develop`): DesignReviewer
sobre `src/` completo (163 archivos) — 0 CRITICAL, 114 WARNING, `should_block: false`, 11
hallazgos propios de Actividad Evaluativa, todos WARNING, mismo patrón ya aceptado en
`US-3.1.2`. UAT Capa 1 (447/447 pytest, sin regresiones) y Capa 2 (`smoke.sh` extendido con el
flujo de Actividad Evaluativa) en verde. **Revisión manual de Víctor validada 2026-08-26**
(`tests/uat/inc3/guion_manual_iteracion1.sh`, sin frontend todavía — vía Swagger UI/HTTP
directo): sin hallazgos de ninguna severidad — idempotencia exacta en la reconexión (mismo id,
mismo set/orden), 422 en `FueraDePeriodo`, 403 por rol. Cierra completa la verificación de la
Iteración 1 (Capa 1 + Capa 2 + DesignReviewer + revisión manual), pero **no** el RF-11/RF-12
completos ni la matriz de trazabilidad — esos pasan a Validado recién cuando el flujo completo
(backend + frontend, Iteración 4) cierre en UAT, mismo criterio que Identidad/Banco de
Preguntas.

**Iteración 2 del Incremento 3 — RNF Confiabilidad, RF-13, cerrada 2026-08-27** (backend
únicamente, mismo criterio de diferir frontend a la Iteración 4 que en Iteración 1).
**US-3.2.1** (Estudiante confirma una respuesta — persistencia atómica), PR
[#155](https://github.com/vvalotto/cognion/pull/155) mergeado a `develop`: Entity `Respuesta`
dentro de `Evaluacion.respuestas`, `Evaluacion.reconstruir()` reescrito para hacer replay real
del stream completo (antes solo leía el primer evento), evento `RespuestaRegistrada`
repetible, `RegistrarRespuestaUseCase`, endpoint `POST /evaluaciones/{id}/respuestas`
(INV-AE-07/08/12). Fix de CBO en `Evaluacion` (11→10), mismo patrón de CRITICAL en pre-push ya
visto en Incrementos 2 y en `US-3.1.3`.
**US-3.2.2** (Estudiante suspende y reanuda su evaluación) cerrada 2026-08-27, PR
[#157](https://github.com/vvalotto/cognion/pull/157) mergeado a `develop`, Issue
[#156](https://github.com/vvalotto/cognion/issues/156):
`Evaluacion.validar_para_suspender()`/`validar_para_reanudar()` (INV-AE-11/12, separación
validación/mutación), `_aplicar_evento` como dispatch por `event_type` en `reconstruir()` (en
vez de asumir que todo evento posterior al primero es `RespuestaRegistrada`), eventos
`EvaluacionSuspendida`/`EvaluacionReanudada` (el primero con campo `actor`, reutilizado luego
por `US-3.2.4`), endpoints `POST /evaluaciones/{id}/suspender` y `/reanudar`.
**US-3.2.3** (Estudiante finaliza su evaluación y ve la revisión completa) cerrada 2026-08-27,
PR [#160](https://github.com/vvalotto/cognion/pull/160) mergeado a `develop`, Issue
[#158](https://github.com/vvalotto/cognion/issues/158):
`Evaluacion.validar_para_finalizar()` (único rechazo: ya `Finalizada` — finalizar siempre debe
poder hacerse, sin validación de período), `Evaluacion.respuesta_vigente_de(pregunta_id)`
(INV-AE-09, `confirmada_en` más reciente por pregunta), evento `EvaluacionFinalizada` (mismo
shape que `EvaluacionSuspendida`, con `actor`), endpoints `POST /evaluaciones/{id}/finalizar` y
`GET /evaluaciones/{id}/revision`.
**US-3.2.4** (`VerificadorDeVencimientos` — suspensión y finalización automáticas, técnica)
cerrada 2026-08-27, PR [#161](https://github.com/vvalotto/cognion/pull/161) mergeado a
`develop`, Issue [#159](https://github.com/vvalotto/cognion/issues/159),
`docs/reports/inc3/US-3.2.4-report.md`: extiende `SuspenderEvaluacionUseCase`/
`FinalizarEvaluacionUseCase` con `actor="sistema"` (no-op silencioso e idempotente sobre
`EvaluacionYaSuspendida`/`EvaluacionYaFinalizada`) en vez de duplicar lógica —
`VerificarVencimientosUseCase` orquesta Regla 1 (inactividad, umbral 15 min) y Regla 2
(vencimiento de período) reutilizando ambos Use Case sin comando ni evento propio. Read model
de evaluaciones activas (`EvaluacionActivaQueryPort`/`SQLAlchemyEvaluacionActivaQueryRepository`)
implementado como query de lectura sobre la tabla `events` existente, no como proyección
sincronizada — decisión confirmada con Víctor para evitar tocar Use Case ya cerrados; válida a
esta escala (30-60 alumnos), documentada como reversible si el volumen cambia. Background task
`asyncio` en el `lifespan` de FastAPI, cadencia 120s configurable
(`verificador_vencimientos_cadencia_segundos`). 599/599 tests (unit + integration + BDD),
quality gates APROBADO (pylint 9.74/10, CC máx 6, MI mín 67.11, coverage 100%). **Cierra
completa la Iteración 2 del Incremento 3 (backend):** a partir de esta US ninguna `Evaluacion`
puede quedar indefinidamente `EnCurso` sin actividad ni sobrevivir pasivamente al cierre del
período de su actividad. Nota dejada para `US-3.3.1`: al implementar
`ModificarPeriodoDisponibilidad`, la Regla 2 deberá reconstruir el stream completo de
`ActividadEvaluativaPeriodoAbierto` en vez de leer solo el primer evento.

**Iteración 3 del Incremento 3 — RF-11b, cerrada 2026-08-28** (backend únicamente, mismo
criterio de diferir frontend a la Iteración 4).
**US-3.3.1** (Docente extiende, o intenta acortar, el plazo de una actividad vigente) cerrada
2026-08-28, PR [#165](https://github.com/vvalotto/cognion/pull/165) mergeado a `develop`, Issue
[#163](https://github.com/vvalotto/cognion/issues/163):
`ModificarPeriodoDisponibilidadUseCase`, evento `PeriodoDisponibilidadModificado` (segundo
evento posible del stream de `ActividadEvaluativaPeriodoAbierto`, que hasta acá siempre tenía
uno solo), primer `ActividadEvaluativaPeriodoAbierto.reconstruir()` real (mismo patrón de
dispatch por `event_type` que `Evaluacion.reconstruir()`, `US-3.2.2`). Consecuencia obligatoria:
los 4 Use Case que leían `eventos[0].payload` directamente (`IniciarEvaluacion`,
`RegistrarRespuesta`, `ReanudarEvaluacion`, Regla 2 del `VerificadorDeVencimientos`) pasan a usar
`reconstruir()`. Endpoint `PATCH /actividades/{id}/periodo` (rol `docente`). El escenario BDD de
`ActividadYaCerrada` quedó diferido a `US-3.3.2` — su precondición (`cerrada_manualmente = true`)
todavía no existía. 138/138 tests unit, 67/67 integration, 6/6 BDD del BC, quality gates
APROBADO (pylint 9.71/10, CC máx 7, MI mín 60.40, coverage 100%).
**US-3.3.2** (Docente cierra una actividad manualmente antes de tiempo) cerrada 2026-08-28, PR
[#166](https://github.com/vvalotto/cognion/pull/166) mergeado a `develop`, Issue
[#164](https://github.com/vvalotto/cognion/issues/164): `CerrarActividadUseCase` — tercer
evento del stream (`ActividadEvaluativaCerrada`), `validar_para_cerrar()` (INV-AE-04b) —
implementa la Regla 3 del `VerificadorDeVencimientos` como cascada síncrona dentro del propio
Use Case, reutilizando `FinalizarEvaluacionUseCase` con `actor="sistema"` (mecanismo de
`US-3.2.4`) sin cambios en ese Use Case. Endpoint `POST /actividades/{id}/cerrar` (rol
`docente`, sin body). Verificó end-to-end el escenario BDD diferido de `US-3.3.1`
(`ModificarPeriodoDisponibilidad` sobre actividad ya cerrada) sin requerir cambios de código
adicionales. 147/147 tests unit, 74/74 integration, 6/6 BDD del BC, quality gates APROBADO
(pylint 9.70/10, CC máx 7, MI mín 60.40, coverage 100%). **Cierra completa la Iteración 3 del
Incremento 3 (backend)** — las Reglas 1, 2 y 3 del `VerificadorDeVencimientos` quedan
implementadas sin desviaciones respecto de lo modelado en
`BC-actividad-evaluativa-modelo.md` §6b.

**Detectado durante la Iteración 3:** `tests/step_defs/inc3/test_us_3_2_1_steps.py::
test_rechazo_fuera_del_período_vigente` falla de forma determinística en este entorno por una
ventana de tiempo demasiado ajustada (~1s) entre la creación de la actividad y el
`IniciarEvaluacion` vía HTTP en el propio setup del test — confirmado que no es una regresión de
ninguna US de esta iteración (falla igual en `develop` limpio antes de estos cambios). Reportado
como chip aparte (`task_471c8a04`), no bloquea el avance.

**Próximo paso:** Iteración 4 del Incremento 3 — frontend, consume las Iteraciones 1 a 3 de una
sola vez (`US-3.4.1` a `US-3.4.7`, `docs/plans/inc3/inc3-candidatas.md`). Gate de diseño UX
obligatorio antes de tocar `frontend/` — verificar contra
`docs/design/ux/wireframes-actividad-evaluativa.md` (aprobado en `US-3.0.2`) antes de escribir
código. Crear Issues y specs `docs/specs/inc3/US-3.4.*.md` antes de implementar.
**Baseline abierta:** ninguna todavía para el Incremento 3 — se abre al cerrar la Iteración 4
(frontend) con el DoD completo del incremento (estudiante completa una evaluación de principio
a fin, docente extiende el plazo de una sesión activa).
**Branch activo:** `develop`.

---

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.11 + FastAPI (async) |
| ORM | SQLAlchemy async + Alembic |
| Base de datos | PostgreSQL |
| Event store | Tabla append-only en PostgreSQL (JSONB) |
| Frontend | React 19 + TypeScript + Vite |
| Estilos / UI | Tailwind CSS + shadcn/ui |
| Containerización | Docker multi-stage |
| Hosting | Fly.io (testing/staging); producción pendiente |
| CI/CD | GitHub Actions |
| Auth | JWT — PyJWT + cryptography |
| Gestión de paquetes | uv (backend), npm (frontend) |

**Perfil `implement-us` activo:** `clean-architecture-bc`
(`.claude/skills/implement-us/customizations/clean-architecture-bc.json`) — no
`hexagonal-ddd-bc` (perfil genérico de claude-dev-kit, no usado en este proyecto). Cualquier
doc de fase de `implement-us` que condicione comportamiento por nombre de perfil debe
referenciar `clean-architecture-bc`.

---

## Estructura del repositorio

```
cognion/
├── CLAUDE.md                        ← este archivo
├── CHANGELOG.md                     ← Keep a Changelog, actualizado en cada tag de baseline
├── .cm/baselines/                   ← BL-NNN.md + reportes de calidad
├── .githooks/pre-push               ← DesignReviewer — bloquea si CRITICAL
├── .pre-commit-config.yaml          ← black, isort, ruff, mypy (bloquea), CodeGuard (advierte)
├── .github/workflows/               ← CI/CD: lint+test en develop, build+deploy en main
├── docs/
│   ├── rf/                          ← documentos de elicitación (RF, RNF, ARQ, PLAN) — históricos
│   ├── adr/                         ← ADR-NNN.md — decisiones arquitectónicas ratificadas
│   ├── architecture/                ← vista de arquitectura vigente (deriva de ARQ + ADRs)
│   ├── design/ux/                   ← wireframes-*.md + prototipos/*.html — gate obligatorio pre-frontend
│   ├── specs/incN/                  ← US-N.M.K.md — input de /implement-us
│   ├── plans/                       ← PLAN-CM.md, WORKFLOW-DESARROLLO.md, PROCEDIMIENTO-UAT.md,
│   │                                    CHECKLIST-INSTALACION.md + incN/incN-candidatas.md por incremento
│   ├── reports/                     ← reportes de cierre de /implement-us
│   ├── traceability/matrix.md       ← RF → BC → Incremento → US → estado
│   └── aprendizajes/                ← HITO-N.md — hallazgos del ensayo IEDD
├── src/<bc>/                        ← backend BC-first con Clean Architecture interna
├── frontend/                        ← React + TypeScript + Tailwind + shadcn/ui
├── quality/reports/                 ← evidencia de codeguard/, designreviewer/, architectanalyst/
└── tests/{unit,integration,features,uat}/incN/
```

---

## Arquitectura interna — reglas no negociables

Monolito modular con **Clean Architecture** interna. Bounded Contexts: Actividad Evaluativa (Core, antes "Sesiones" — ver `ADR-015`), Banco de Preguntas, Identidad, Notificaciones, Analytics.

```
src/<bc>/
├── entities/           → reglas de negocio puras — sin dependencias externas
├── use_cases/          → orquestación — solo importa entities/
├── interface_adapters/ → controllers, presenters, gateways — solo importa use_cases/
└── frameworks/         → FastAPI, SQLAlchemy, WebSockets — implementa puertos
```

**Regla de imports:** las capas internas nunca importan capas externas. Comunicación entre BCs: solo por puertos definidos en `entities/ports/` — nunca imports directos entre BCs. `shared/` es la única excepción transversal: puede tener las 4 capas (`entities/`, `use_cases/`, `interface_adapters/`, `frameworks/`) cuando el contenido es genuinamente transversal — sin lógica de negocio de un BC específico — no solo `entities/` (`ADR-017` para `shared/frameworks/db.py`, `ADR-019` para JWT/RBAC en `shared/entities/`+`frameworks/security/`+`interface_adapters/security/`). Cada BC sigue armando su propio composition root en `frameworks/dependencies.py`, importando de `shared` — nunca de otro BC.

---

## Workflow de desarrollo — resumen operativo

Referencia completa: `docs/plans/WORKFLOW-DESARROLLO.md`. Referencia de política: `docs/plans/PLAN-CM.md`.

### Jerarquía de trabajo

```
Incremento (PLAN_v1.md, 0–6) → Baseline (BL-NNN) + tag git (v0.N.0) + Milestone GitHub
  └── Iteración
        └── US-IEDD (US-N.M.K) → GitHub Issue + docs/specs/incN/US-N.M.K.md + feature branch + /implement-us
```

### Branching

```
main          ← baselines (v0.N.0) — deploy automático al mergear
  └── develop ← integración continua — recibe PRs de cada US
        ├── feature/US-N.M.K-descripcion-corta
        ├── feature/inc-N-descripcion-corta    ← incrementos técnicos sin US
        └── fix/descripcion-corta
```

- `develop → main` solo al cerrar un Incremento (Baseline).
- PRs de features siempre apuntan a `develop`. `gh pr create` siempre con `--base develop`.

### Conventional Commits

```
feat(entities): agregar aggregate ActividadEvaluativa [US-3.1.1]
fix(interface_adapters): corregir endpoint ranking
test(entities): tests unitarios ActividadEvaluativa.cerrar_periodo
docs(adr): ADR-003 SQLite vs PostgreSQL
chore(cm): registrar BL-002 cierre Incremento 2
```

Scopes: `entities | use_cases | interface_adapters | frameworks | frontend | cm | tests | design`

### Ciclo por US-IEDD (orden no negociable)

```
1. git checkout -b feature/US-N.M.K-descripcion desde develop
2. Verificar branch activo con git branch
3. tracker init US-N.M.K → start_phase(0)  ← ANTES de cualquier artefacto
4. /implement-us US-N.M.K  (lee docs/specs/incN/US-N.M.K.md)
5. Commits atómicos con referencia [US-N.M.K]
6. /pr → push + gh pr create --base develop
7. Al mergear el PR (gh pr merge): sincronizar develop local (checkout + pull --ff-only,
   borrar branch feature local/remoto), y cerrar el Issue de la US asociado — comentario con
   los SHAs de los commits de la US + `gh issue close` — sin pedir confirmación previa, salvo
   que algo resulte ambiguo (no se encuentra el Issue, hay más de un candidato, etc.)
```

**Por qué el paso 7 es manual y no vía `Closes #N` en el commit/PR:** el repo mergea PRs a
`develop`, no a `main` (rama default) — GitHub solo autocierra Issues por `Closes #N` cuando
el merge es a la rama default.

**Política de tracking:** operaciones sobre `tracker_cli.py` estrictamente secuenciales, nunca en paralelo sobre el mismo JSON. Usar `.venv/bin/python .claude/tracking/tracker_cli.py`, no `uv run`.

---

## Quality gates

| Nivel | Herramienta | Modo | Bloquea |
|-------|-------------|------|---------|
| Commit backend | mypy (`src/` completo) | Pre-commit automático | Sí |
| Commit backend | CodeGuard | Pre-commit automático | No — solo advierte |
| Push backend | DesignReviewer | Pre-push automático | Sí, si CRITICAL |
| Push/PR a develop | lint + tests + DesignReviewer | GitHub Actions CI | Sí |
| Merge/tag a main | build Docker + deploy + healthcheck | GitHub Actions CD | Sí |
| Cierre de Incremento | DesignReviewer manual + verificación UX | Manual | 0 CRITICAL requerido |
| UAT | Tests funcionales (Capa 1 + Capa 2) | Manual | Debe aprobar antes de merge a main |
| Cierre de Baseline | ArchitectAnalyst | **Siempre manual** | No bloquea — informa tendencias |

**Notas operativas críticas:**
- `designreviewer` **siempre** con `--config pyproject.toml` — sin el flag usa defaults genéricos que no reflejan el proyecto.
- El hook `.githooks/pre-push` **no se activa solo al clonar** — requiere `git config core.hooksPath .githooks` una vez por clon.
- Umbrales de `[tool.designreviewer]` se calibran **al inicio de cada Incremento completo**, no US por US.
- El check de tipos integrado en CodeGuard (`software_limpio`) invoca mypy sin `--cache-dir`
  y con timeout de 10s — en corridas en frío puede superar ese tiempo y el check queda mudo
  (ni aprueba ni reporta error real), dejando pasar errores de tipo reales sin aviso. Bug
  reportado: `vvalotto/software_limpio#70`. Mientras se corrige ahí, el hook `mypy` dedicado
  (arriba, sobre `src/` completo, mismo comando que CI) es la fuente de verdad local para
  tipos — bloquea el commit si hay errores reales.

---

## Gate de diseño UX (obligatorio antes de frontend)

Ninguna línea de `frontend/` sin artefacto aprobado en `docs/design/ux/`. Proceso:

```
1. Prototipo HTML navegable (docs/design/ux/prototipos/)
2. Validación humana (en el dispositivo real si el escenario lo exige)
3. Spec Markdown (docs/design/ux/wireframes-*.md)
4. Aprobación explícita de Víctor
5. Recién entonces escribir la spec de la US y el código
```

Toda spec de US que toca `frontend/` debe incluir el campo `## Fuente de verdad UX` con referencias a los artefactos consultados — sin ese campo la spec está incompleta.

**Por qué existe este gate:** en el proyecto de referencia (AtaraxiaDive), saltearlo produjo una US completa revertida al detectarse 14 gaps críticos en UAT. El código había sido especificado mirando el código existente en lugar del diseño aprobado (anti-patrón "spec-validatoria").

---

## Clasificación de hallazgos en UAT

Decidir el track **antes de codear**:
- Hallazgo **solo toca `frontend/`** → track informal, commit descriptivo, sin spec ni `/implement-us`.
- Hallazgo **toca cualquier archivo de `src/`** → track formal obligatorio: US-IEDD → spec → `/implement-us`.
- Si al resolver algo "de UX" la primera acción termina siendo abrir `src/`: pivotar al track formal.

---

## Convenciones de nomenclatura

| Artefacto | Patrón | Ejemplo |
|-----------|--------|---------|
| Baseline | `BL-NNN-slug.md` | `BL-001-incremento-0-walking-skeleton.md` |
| US-IEDD | `US-{inc}.{iter}.{seq}` | `US-2.3.1` |
| Branch de US | `feature/US-N.M.K-descripcion` | `feature/US-2.3.1-registrar-respuesta` |
| Branch técnico | `feature/inc-N-descripcion` | `feature/inc-0-fundacion-tecnica` |
| ADR | `ADR-NNN-slug.md` | `ADR-003-sqlite-vs-postgresql.md` |
| HITO | `HITO-N-SLUG.md` | `HITO-1-WALKING-SKELETON-FRICCION.md` |
| CI backend | `CI-C##` | `CI-C08` |
| CI frontend | `CI-F##` | `CI-F03` |
| Milestone GitHub | `Incremento N — <nombre>` | `Incremento 0 — Fundación Técnica` |
| Labels GitHub | `us-iedd`, `incremento-N`, `blocked`, `in-progress`, `done` | — |

---

## Ítems abiertos que requieren decisión

- **Algoritmo de puntaje en modo en vivo** (RF-10): combina tiempo, corrección, dificultad e importancia. Se cierra como spike en Incremento 6, Iteración 0.
- **Mecanismo de importación desde PDF** (RF-07): parseo automático vs. asistido. Se decide en Incremento 7.
- **Infraestructura definitiva** (ARQ_v1.md): Fly.io confirmado para testing; producción
  pendiente de decisión institucional (nube vs. servidor FIUNER) y del mecanismo de backup
  asociado (`RNF_v1.md` Escenario 2 — mensual, retención 12 meses). Cambio de estrategia
  2026-08-24 (`docs/rf/PLAN_v1.md` revisión 2026-08-24): los Incrementos 3 a 7 corren con datos
  de prueba/locales, no datos reales de estudiantes — esta decisión se resuelve recién en la
  última iteración antes de la prueba funcional de validación previa al despliegue real, no
  antes del Incremento 3 como decía el plan original.
- **Docker en el entorno de desarrollo local**: no instalado a la fecha (2026-07-16). Se
  usará más adelante en el proyecto — hasta entonces, PostgreSQL local corre vía Homebrew
  (ver `docs/rf/PLAN_v1.md` revisión 2026-07-16). El build de imagen Docker en CI/CD no se
  ve afectado — corre en GitHub Actions, no localmente.
- **Criterios de legibilidad en proyección** (RNF_v1.md): tamaño de fuente mínimo y contraste. Se define en etapa de diseño UX antes de Incremento 6.

---

## Al iniciar una sesión

1. Leer este archivo.
2. `git log --oneline -10` y `git status` para ver el estado real del repo.
3. Si hay una baseline abierta: leer `.cm/baselines/BL-NNN.md` en curso.
4. Si hay trackers activos: verificar con `.venv/bin/python .claude/tracking/tracker_cli.py status` antes de arrancar.
5. No preguntar por el stack ni por la arquitectura — están decididos en `docs/rf/ARQ_v1.md`.

## Al cerrar una sesión

1. Ejecutar `/checkpoint` — si hubo cambios en `docs/` durante la sesión, dispara
   `/docs-audit` automáticamente antes de guardar (ver `.claude/commands/checkpoint.md`).
