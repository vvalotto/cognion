# Incremento 7-ADJ — Ciclo de vida de la cuenta y ajustes de la UAT v1 (antes de RF-07)

**Estado:** en planificación (abierto 2026-10-02; specs e Issues creados el mismo día)
**Milestone:** [Incremento 7-ADJ — Ciclo de vida de la cuenta y ajustes de la UAT v1](https://github.com/vvalotto/cognion/milestone/15)
**Política:** mismo criterio de nomenclatura que `Incremento 3-ADJ` a `6-ADJ` — ajuste insertado
fuera de la secuencia numérica 0-7 de `docs/rf/PLAN_v1.md`, sin renumerar. Va **antes** de la
Iteración 2 del Incremento 7 (RF-07), decisión de Víctor 2026-10-02.

## Origen y decisión de secuencia

La UAT manual de cierre de alcance v1 (Incremento 7, Iteración 1, cerrada 2026-10-02,
`quality/reports/uat/inc7/`) dejó 11 hallazgos: 3 resueltos en el momento (#2, #3, #8) y 8
abiertos. Los dos 🔴 (**#11** una cuenta deshabilitada puede seguir iniciando sesión, **#4** el
sistema puede quedar sin Administrador operativo) son reglas del ciclo de vida de la cuenta que
el sistema no hace cumplir; tocan `src/` y por eso van por el track formal
(`CLAUDE.md` §"Clasificación de hallazgos en UAT"). El `plan-de-correccion.md` fue aprobado por
Víctor con sus 6 decisiones (§7 de ese documento) y es la fuente de verdad de este incremento —
este archivo solo lo baja a una lista de trabajo.

Se hace antes de RF-07 porque `59` y `60` son de seguridad e integridad del acceso, y porque el
spike de RF-07 (parseo automático vs. asistido) necesita a Víctor presente de todas formas.

## Alcance

| # | Ítem | Hallazgo | Qué | Track | Issue |
|---|---|---|---|---|---|
| 0 | Verificación | #1, #6 | Spike de #1 (autoregistro `201` sin persistir) contra un build de producción (`npm run build` + `vite preview`, ≥ 5 repeticiones mirando el log y la base; incluir el `422` inexplicado de la recuperación de contraseña). Re-prueba de #6 con el iPhone (y staging con WSS cuando exista) | Verificación — no se codea hasta ver el resultado | — |
| 1 | `US-ADJ-59` | #11 🔴 | Una cuenta deshabilitada no puede iniciar sesión (solo en login; sesiones ya emitidas viven hasta expirar, `ADR-013`) | Formal | [#474](https://github.com/vvalotto/cognion/issues/474) |
| 2 | `US-ADJ-60` | #4 🔴 | Siempre existe ≥ 1 Administrador operativo: nunca se borra físicamente, no se deshabilita el último activo, y el último activo se bloquea solo de forma **temporal** (~15 min) en vez de permanente | Formal | [#475](https://github.com/vvalotto/cognion/issues/475) |
| 3 | `US-ADJ-62` | #5 🟡 | Recuperar la contraseña también desbloquea la cuenta (resetea `bloqueada` y los contadores de intentos) | Formal | [#477](https://github.com/vvalotto/cognion/issues/477) |
| 4 | `US-ADJ-61` | #10 🟡 | Estado `cerrada` visible para el Estudiante: nuevo valor en `EstadoVisible`, badge "Cerrada", mensaje propio en `FueraDePeriodo`, y "Mis materias" no cuenta una cerrada como pendiente | Formal, con gate UX previo | [#476](https://github.com/vvalotto/cognion/issues/476) |
| 5 | Texto del ranking | #7 🟡 | "Todavía no hay evaluaciones de período abierto finalizadas con preguntas de esta materia." No se toca "Desempeño por tema" | Informal (solo `frontend/`) | — |
| 6 | Evolución temporal | #9 ⚪ | Etiqueta del eje X truncada y serie "Promedio de la comisión" no visible con un solo dato — revisar con ≥ 2 estudiantes antes de corregir | Informal (solo `frontend/`) | — |
| 7 | Cierre | — | `BL-012`: DesignReviewer + ArchitectAnalyst manual, pase de navegador real que repite los pasos de la UAT afectados (login/baja/bloqueo/recuperación de cuenta, actividad cerrada), matriz de trazabilidad, `CHANGELOG.md` | Cierre de baseline | — |

**Orden:** `59` → `60` → `62` → `61`. Se reordenó respecto del §5 del plan de corrección, donde
`62` iba al final por ser condicional: ya quedó firme (decisión 4) y comparte bounded context
(Identidad) y flujo de bloqueo con `59`/`60`, así que conviene hacerlas seguidas. `61` va
después porque vive en Actividad Evaluativa y exige gate UX. Los informales (#7, #9) pueden
entrar en cualquier hueco.

**Dependencias:**
- `60` depende de `59`: "Administrador activo" solo tiene sentido si `deshabilitada` se hace cumplir.
- `62` interactúa con `60` (regla 3): el desbloqueo por recuperación también libera al último
  Administrador bloqueado temporalmente — dejarlo escrito en ambas specs.
- `62` reabre una decisión de `US-ADJ-39` ("no desbloquea la cuenta"): actualizar esa spec y el
  docstring de `recuperacion_password_router.py`.
- `61` tiene que actualizar antes el wireframe/prototipo aprobado
  (`docs/design/ux/wireframes-actividad-evaluativa.md`, `US-3.4.5` fijó solo 3 badges "fieles al
  prototipo") y verificar si "Desempeño por comisión" sigue contando como pendiente a quien no
  rindió una actividad ya cerrada.

## Decisiones de Víctor (2026-10-02), tomadas en el plan de corrección

1. El 7-ADJ va **antes** de RF-07.
2. `US-ADJ-59`: rechazar **solo en el login**; no se revalida el estado en cada request (ventana
   de hasta 60 min por el JWT sin blacklist, `ADR-013`). Si más adelante molesta, revalidar en
   el guard se puede sumar sin deshacer esto.
3. `US-ADJ-60`, regla 3: bloqueo **temporal** para el último Administrador activo; el resto de
   las cuentas conserva el bloqueo actual hasta que un Administrador las desbloquee. El valor
   exacto del tiempo (se propone ~15 min) se fija en la spec.
4. `US-ADJ-62`: recuperar la contraseña **sí desbloquea**.
5. #7: solo se corrige el texto del ranking (el alcance "el vivo no cuenta en los informes" ya
   se decidió el 2026-09-27 en `US-ADJ-56`).
6. Los fixes de #3 y #8 se commitearon aparte (PR #472, mergeado).

## Decisiones por defecto de las specs (a confirmar por Víctor)

Las specs (`docs/specs/ajustes/US-ADJ-59.md` a `62.md`) cerraron los detalles que el plan dejaba
abiertos con una propuesta por defecto. **Ninguna está confirmada todavía:**

- **`US-ADJ-59`:** error propio `403` con `detail` estructurado `cuenta_deshabilitada` (en vez de
  reutilizar el `401` de credenciales inválidas); se chequea **antes** de verificar la contraseña
  y de `bloqueada`, sin consumir intentos.
- **`US-ADJ-60`:** campo nuevo `usuario.bloqueada_hasta` con vencimiento **perezoso** (sin proceso
  de fondo); duración 15 min en `settings.py` (`administrador_bloqueo_temporal_minutos`);
  "operativo" = Administrador ni deshabilitado ni bloqueado (el bloqueo temporal también deja de
  contarlo); la regla cubre los **dos** caminos de bloqueo (login y cambio de la propia
  contraseña); `409` con `detail` estructurado para la baja del último; el conteo va en
  `UsuarioRepositoryPort` para no sumar dependencias (CBO). Condición de carrera entre dos
  Administradores aceptada y documentada.
- **`US-ADJ-61`:** badge "Cerrada" neutro; cierre manual y vencimiento por fecha se muestran
  igual; `finalizada` gana sobre `cerrada`; texto neutro cuando se llega por el `422` sin
  contexto.
- **`US-ADJ-62`:** `recuperar_password` delega en `resetear_password` (misma lógica de
  desbloqueo); no reactiva cuentas deshabilitadas; revierte una decisión de `US-ADJ-39`.

**Gate UX pendiente en las cuatro:** la Parte A (backend) de cada una se puede implementar sin
él; la Parte B (frontend) necesita antes wireframes/prototipo actualizados y aprobados.

## Fuera de alcance

- **RF-07** (importación desde PDF): Iteración 2 del Incremento 7, después de este incremento.
- **RF-18** (KPIs históricos): sigue diferido, sin incremento asignado.
- **Revalidar el estado de la cuenta en cada request** (guard JWT en `shared/`, `ADR-019`):
  descartado por la decisión 2.
- **Contenido real de los emails, proyector real, staging con WSS, selector multi-materia:** no
  cubiertos por la UAT, ya declarados en el §6 del plan de corrección; no entran acá.

## DoD de la iteración

- Las 4 US formales (`59`, `60`, `61`, `62`) cerradas con su PR mergeado a `develop` y su Issue
  cerrado.
- Spike de #1 resuelto: o se cierra como artefacto de StrictMode/dev (documentado), o pasa a
  🔴 y se abre su `US-ADJ`.
- #6 re-probado con el iPhone; si repite, se abre `US-ADJ` con repro.
- #7 y #9 corregidos (informales).
- Un solo pase de navegador real al cierre, con la base resembrada, que repite los pasos de la
  UAT afectados — mismo criterio que `5-ADJ`/`6-ADJ`.
- `BL-012` cerrada. Tag a decidir al cierre (PATCH, mismo criterio de versionado que `BL-005`/`BL-007`).
