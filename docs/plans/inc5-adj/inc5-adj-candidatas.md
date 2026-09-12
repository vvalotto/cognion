# Incremento 5-ADJ — Identidad Autoservicio y Analytics del Docente — US candidatas

> Estado documental: **Especificadas, ninguna implementada todavía.**
> Incremento no planificado originalmente en `docs/rf/PLAN_v1.md` — inserción fuera de la
> secuencia numérica 0-7, inmediatamente después de `BL-009` (Incremento 5 — Notificaciones,
> RF-14, cerrado 2026-09-12), mismo criterio que `Incremento 3-ADJ`/`4-ADJ`: no se renumeran
> los Incrementos 6-7 ya mapeados a RF. A diferencia de `3-ADJ` (deuda de tooling) y `4-ADJ`
> (deuda de producto sobre navegación), este agrupa dos frentes independientes que comparten
> el mismo motivo de secuenciación — cerrar backlog que quedó "Sin asignar"/sin resolver antes
> de abrir el Incremento 6 (Sesión en Vivo):
>
> 1. **RF-20 a RF-23** (Analytics, agregados 2026-09-09 durante la prueba manual E2E de
>    estabilización, `docs/traceability/matrix.md` — story points "Sin asignar", sin
>    incremento asignado desde su elicitación).
> 2. **Hallazgos de Identidad y cuentas** relevados por Víctor en revisión manual
>    (`hallazgos-cognion.md`, 2026-09-12): mostrar/ocultar contraseña, política de contraseña
>    segura, descubribilidad de "Cambiar contraseña" (ya implementada, `US-2.2.8`, pero sin
>    entrada en el menú de navegación desde `US-ADJ-27`), recuperación de contraseña por
>    autoservicio (RF nuevo), autoregistro de Docente/Estudiante con selección de perfil
>    (RF nuevo, convive con el registro por invitación existente) y cierre de sesión voluntario
>    (`clearSession()` ya existe en `frontend/src/lib/session.ts`, pero solo se invoca desde el
>    interceptor de error 401 — no hay botón).
>
> **Decisiones de producto confirmadas con Víctor antes de este documento:**
> - Autoregistro **convive** con la invitación existente (no la reemplaza) — `RF-01` y su UI
>   (`US-ADJ-23` a `26`) quedan sin cambios.
> - Estudiante que se autoregistra elige Materia → Comisión de una lista pública (mismo patrón
>   de selector ya usado en `US-2.1.11`/`US-4.1.3`).
> - Docente que se autoregistra queda **activo de inmediato**, sin aprobación del
>   Administrador ni verificación de email — mismo criterio de confianza que el resto del
>   sistema (docente único, entorno controlado, 30-60 alumnos).
> - Recuperación de contraseña reusa el `SmtpCanalEnvio` ya existente de Notificaciones
>   (RF-14) — sin esperar la decisión institucional de SMTP real de producción, todavía
>   pendiente (`CLAUDE.md` §"Ítems abiertos").
> - Contraseña segura: sube el mínimo actual de 8 caracteres (`Usuario.validar_password_nueva`,
>   único chequeo hoy) y agrega mezcla de tipos (mayúscula, número, símbolo).
>
> **Iteración de cierre añadida a pedido de Víctor** (a diferencia de `3-ADJ`/`4-ADJ`, que
> cerraban con Baseline directa): una iteración final de revisión documental *transversal* —
> no solo `RF_v1.md`/matriz/wireframes/`CLAUDE.md` (lo ya habitual en cada cierre de Baseline),
> sino también los ADRs afectados (`ADR-012` "rechazo sin recuperación automática" queda
> matizado por la recuperación nueva; revisar si amerita ADR propio el autoregistro) y los
> modelos de dominio + event storming ya elaborados de Identidad y Analytics
> (`BC-identidad-modelo.md`, `BC-analytics-modelo.md`) — para que el material de modelado
> quede consistente con lo implementado, no solo los documentos de seguimiento operativo.

---

## Por qué agrupar RF-20/23 (Analytics) con los hallazgos de Identidad en un solo incremento

Ambos frentes son independientes entre sí (no hay dependencia técnica entre Analytics y los
ajustes de Identidad) pero comparten el mismo motivo de secuenciación: son backlog que quedó
pendiente de asignación antes de que se abriera el Incremento 6 (`RF-08/09/10`, Sesión en
Vivo). Se evaluó abrir dos incrementos ADJ separados (mismo criterio de aislamiento que separó
`3-ADJ` de `4-ADJ`); se descartó porque ninguno de los dos frentes es lo bastante grande por sí
solo para justificar su propio ciclo completo de Modelado → Baseline, y ambos comparten la
misma motivación de "cerrar antes de Incremento 6, ya que ninguno estaba en la secuencia
original". Sí quedan como **iteraciones separadas** dentro del mismo incremento (no mezclados
en una misma iteración), dado que no comparten ningún artefacto de dominio ni de UI.

---

## Iteración 0 — Modelado

Tres US-IEDD tipo `Modelado` (`WORKFLOW-DESARROLLO.md` §1, §2) — DoD = artefacto aprobado
explícitamente por Víctor en el comentario que cierra el Issue.

| US | Tipo | Descripción | Postcondición (DoD) | Path del artefacto |
|---|---|---|---|---|
| **US-ADJ-32** | Modelado | Ampliación del event storming/modelo de dominio de Identidad: invariante de contraseña segura ampliada, comando/evento de recuperación de contraseña (`SolicitarRecuperacionPassword`/`RecuperacionPasswordSolicitada`, `ConfirmarNuevaPassword`/`PasswordRecuperada`, expiración de token — mismo criterio de expiración que la invitación de `ADR-012`), comando/evento de autoregistro (`AutoregistrarUsuario`/`UsuarioAutoregistrado`, distinto de `UsuarioInvitadoAceptado` ya existente) | Víctor aprueba la ampliación del modelo en el comentario de cierre del Issue | `docs/design/domain/BC-identidad-modelo.md` (ampliado, no reemplazado) |
| **US-ADJ-33** | Modelado | Modelo de los 4 read models nuevos de Analytics (RF-20 a RF-23): forma de cada consulta, de dónde se computa cada uno (reutilización de `EvaluacionDesempenoConsultaPort`/`ComisionConsultaPort`/`PreguntaMetadatoConsultaPort` ya existentes de `US-4.1.1`/`US-4.2.2`/`US-4.2.3` vs. puertos nuevos que haga falta agregar) | Víctor aprueba el modelo en el comentario de cierre del Issue | `docs/design/domain/BC-analytics-modelo.md` (ampliado, no reemplazado) |
| **US-ADJ-34** | Modelado | Wireframes/prototipo — gate UX obligatorio para todas las US de Iteración 1 a 4: (a) toggle mostrar/ocultar contraseña sobre los 5 formularios existentes, indicador de fortaleza; (b) pantallas "Olvidé mi contraseña" (solicitar) y "Definir nueva contraseña" (con token); (c) pantalla de autoregistro con selección de perfil (Docente/Estudiante) y formulario dinámico según el perfil elegido (Estudiante agrega selector Materia→Comisión); (d) entrada "Cambiar contraseña" y botón "Cerrar sesión" en `AppNav.tsx`; (e) las 4 pantallas de Analytics de RF-20 a RF-23 | Víctor aprueba wireframes/prototipo en el comentario de cierre del Issue | `docs/design/ux/wireframes-identidad-autoservicio.md` + ampliación de `docs/design/ux/wireframes-analytics.md` + prototipos en `docs/design/ux/prototipos/` |

**Orden:** `US-ADJ-32` y `US-ADJ-33` pueden ir en paralelo (BCs distintos, sin dependencia
entre sí). `US-ADJ-34` depende de ambas — el wireframe visualiza los dos modelos ya aprobados,
mismo orden que `US-ADJ-21`→`US-ADJ-22` en Incremento 4-ADJ.

~~US-ADJ-32~~ Cerrada 2026-09-12, Issue [#318](https://github.com/vvalotto/cognion/issues/318)
— modelo ampliado aprobado por Víctor: aggregate `TokenRecuperacionPassword`, comandos
`AutoregistrarDocente`/`AutoregistrarEstudiante`, `INV-ID-11` ampliada,
`docs/design/domain/BC-identidad-modelo.md` §13 (PR #322).

~~US-ADJ-33~~ Cerrada 2026-09-12, Issue [#319](https://github.com/vvalotto/cognion/issues/319)
— modelo ampliado aprobado por Víctor: 4 queries nuevas (RF-20 a RF-23),
`EvaluacionDesempenoConsultaPort`/`MetadatoPreguntaResumen` ampliados, sin puertos nuevos,
`docs/design/domain/BC-analytics-modelo.md` §8 (PR #324, #325). Hallazgo de deriva documental
en `BC-actividad-evaluativa-modelo.md` anotado para la Iteración 5.

~~US-ADJ-34~~ Cerrada 2026-09-12, Issue [#320](https://github.com/vvalotto/cognion/issues/320)
— wireframes/prototipo aprobados por Víctor: `docs/design/ux/prototipos/identidad-autoservicio.html`
(11 pantallas) + `docs/design/ux/wireframes-identidad-autoservicio.md`, ampliación de
`docs/design/ux/prototipos/analytics-portal-desempeno.html` (+4 pantallas) y
`docs/design/ux/wireframes-analytics.md` §3.2-3.5 (PR #327). **Cierra completa la Iteración 0**
del Incremento 5-ADJ.

---

## Iteración 1 — Identidad: contraseña segura y accesible

Backend + frontend juntos, sin diferir (mismo criterio que Banco de Preguntas/Cuentas). Sin RF
propio — ajuste de UX/seguridad sobre `RF-02`/`RF-19` ya Validados, mismo criterio de
"no mueve fila de la matriz" que `US-1.1.0`/`US-2.1.2`.

| US | Descripción | Toca | Actor |
|---|---|---|---|
| **US-ADJ-35** | Componente compartido `PasswordInput` con toggle mostrar/ocultar, reemplaza los 10 inputs `type="password"` de los 5 formularios existentes (`Login.tsx`, `Registro.tsx` ×2, `CambiarPassword.tsx` ×3, `AltaDocente.tsx` ×2, `cuentas/ResetearPassword.tsx` ×2) | Frontend puro | Docente, Estudiante, Administrador |
| **US-ADJ-36** | Contraseña segura: `Usuario.validar_password_nueva` sube el mínimo a 12 caracteres y agrega mezcla de tipos (mayúscula, número, símbolo); **cierra un gap real** — `CrearUsuario`/`RegistrarEstudiante` hoy no llaman esa validación (solo `CambiarPassword`/`ResetearPassword` lo hacen); frontend agrega indicador de fortaleza a `PasswordInput` (`US-ADJ-35`) | Backend (`entities/usuario.py`, 2 use cases, 4 routers) + Frontend | Docente, Estudiante, Administrador |
| **US-ADJ-37** | Descubribilidad: el bloque de avatar/nombre de `AppLayout.tsx` (hoy estático) pasa a menú desplegable con "Cambiar contraseña" (sin link hoy hacia `/mi-cuenta/cambiar-password`) y "Cerrar sesión" (invoca `clearSession()`, hoy solo se dispara desde el interceptor 401) | Frontend puro (`AppLayout.tsx`) | Docente, Estudiante, Administrador |

~~US-ADJ-35~~ Cerrada 2026-09-12, Issue [#329](https://github.com/vvalotto/cognion/issues/329),
PR [#333](https://github.com/vvalotto/cognion/pull/333) — componente `PasswordInput.tsx`
implementado y en `develop`, reemplaza los 10 inputs de contraseña de los 5 formularios.
Reporte `docs/reports/inc5-adj/US-ADJ-35-report.md`.
~~US-ADJ-36~~ Cerrada 2026-09-12, Issue [#330](https://github.com/vvalotto/cognion/issues/330),
PR [#335](https://github.com/vvalotto/cognion/pull/335) — `INV-ID-11` ampliada (12 caracteres +
mayúscula/número/símbolo) en `develop`; **cierra el gap real** de `CrearUsuario`/
`RegistrarEstudiante`, que no validaban contraseña del lado del dominio. `PasswordInput` gana
indicador de fortaleza. Reporte `docs/reports/inc5-adj/US-ADJ-36-report.md`.
**US-ADJ-37** Issue [#331](https://github.com/vvalotto/cognion/issues/331), spec
`docs/specs/ajustes/US-ADJ-37.md` — backlog, pendiente de implementar. Última US de la
Iteración 1 — la cierra completa.

**Orden:** las 3 son independientes entre sí — pueden implementarse en cualquier orden o en
paralelo.

---

## Iteración 2 — Identidad: recuperación de contraseña (RF nuevo)

Backend + frontend juntos. Concreta el nuevo RF de recuperación de contraseña por
autoservicio — numeración definitiva (`RF-24` o la que corresponda tras revisar
`RF_v1.md`) a confirmar en la Iteración 5 (revisión documental), mismo criterio que otros RF
que se numeraron formalmente después de acordar el alcance con Víctor.

| US | Descripción | Consume/agrega | Actor |
|---|---|---|---|
| **US-ADJ-38** | Endpoint público `POST /identidad/recuperar-password/solicitar` (email → genera token con expiración, dispara email vía `SmtpCanalEnvio` de Notificaciones — mismo canal de `RF-14`); no revela si el email existe o no (mismo criterio de no filtrar existencia de cuentas) | Backend nuevo | Público (sin autenticar) |
| **US-ADJ-39** | Endpoint público `POST /identidad/recuperar-password/confirmar` (token + password nueva → aplica `Usuario.validar_password_nueva` ampliada de `US-ADJ-36`, invalida el token tras el uso) | Backend nuevo, reutiliza `US-ADJ-36` | Público (sin autenticar) |
| **US-ADJ-40** | Pantallas "Olvidé mi contraseña" (solicitar, accesible desde `Login.tsx`) y "Definir nueva contraseña" (con el token de la URL) | Frontend, consume `US-ADJ-38`/`US-ADJ-39` | Público (sin autenticar) |

**Orden:** `US-ADJ-38` → `US-ADJ-39` (confirmar necesita que el token ya se pueda generar) →
`US-ADJ-40`.

---

## Iteración 3 — Identidad: autoregistro con selección de perfil (RF nuevo)

Backend + frontend juntos. Numeración definitiva a confirmar en la Iteración 5, igual que
`US-ADJ-38` a `40`.

| US | Descripción | Consume/agrega | Actor |
|---|---|---|---|
| **US-ADJ-41** | Endpoint público `POST /identidad/autoregistro` para perfil Docente (nombre, email, password — valida `US-ADJ-36` —, cuenta activa de inmediato) | Backend nuevo | Público (sin autenticar) |
| **US-ADJ-42** | Mismo endpoint (o variante), perfil Estudiante: agrega `comision_id` obligatorio (`GET /materias` + `GET /materias/{id}/comisiones` ya existentes para poblar el selector), cuenta activa de inmediato | Backend, reutiliza endpoints de `US-2.1.9`/`US-4.2.2` | Público (sin autenticar) |
| **US-ADJ-43** | Pantalla de autoregistro: selección de perfil (Docente/Estudiante) → formulario dinámico según el perfil, con selector Materia→Comisión solo para Estudiante | Frontend, consume `US-ADJ-41`/`US-ADJ-42` | Público (sin autenticar) |

**Orden:** `US-ADJ-41` → `US-ADJ-42` (mismo endpoint ampliado, o endpoint hermano — a decidir
en la spec) → `US-ADJ-43`.

---

## Iteración 4 — Analytics: RF-20 a RF-23

Backend + frontend juntos por RF, mismo criterio que Iteración 1/2 del Incremento 4
(RF-15/16/17: no se difiere el frontend). Reutiliza la infraestructura de puertos ya existente
donde alcance (`EvaluacionDesempenoConsultaPort`, `ComisionConsultaPort`,
`PreguntaMetadatoConsultaPort`) — la Iteración 0 (`US-ADJ-33`) determina si hace falta algún
puerto nuevo.

| US | RF | Descripción | Actor |
|---|---|---|---|
| **US-ADJ-44** | RF-20 | Backend: tabla de desempeño por comisión (% aciertos acumulado + actividades pendientes por estudiante) y drill-down a la revisión completa de una evaluación puntual de un estudiante de esa comisión | Docente |
| **US-ADJ-45** | RF-21 | Backend: evolución temporal del % de aciertos (individual y promedio de comisión), respetando el orden cronológico de actividades efectivamente rendidas | Docente |
| **US-ADJ-46** | RF-22 | Backend: ranking de preguntas más falladas por tasa de error (no conteo bruto), filtrable por comisión o agregado de materia, misma escala de severidad que `RF-17` | Docente |
| **US-ADJ-47** | RF-23 | Backend: completitud/participación por actividad — estado de cada estudiante de la comisión (sin iniciar/en curso/suspendida/finalizada) | Docente |
| **US-ADJ-48** | RF-20 | Pantalla "Desempeño por comisión" con drill-down a detalle de estudiante y de ahí a la revisión de una evaluación puntual | Docente |
| **US-ADJ-49** | RF-21 | Pantalla/gráfico de evolución temporal (individual, desde el drill-down de `US-ADJ-48`, y por comisión) | Docente |
| **US-ADJ-50** | RF-22 | Pantalla "Preguntas más falladas" (ranking ordenable, filtro por comisión/materia) | Docente |
| **US-ADJ-51** | RF-23 | Pantalla "Completitud por actividad" (estado por estudiante de una actividad puntual) | Docente |

**Orden:** cada par backend→frontend es independiente de los otros 3 RF (`US-ADJ-44`→`48`,
`US-ADJ-45`→`49`, `US-ADJ-46`→`50`, `US-ADJ-47`→`51`) — pueden implementarse en cualquier
orden entre RFs, backend siempre antes que su propio frontend.

---

## Iteración 5 — Revisión documental de cierre

Una única US-IEDD tipo `Documentación` (no genera código de producción) — DoD = revisión
completa confirmada por Víctor.

| US | Tipo | Descripción | Postcondición (DoD) |
|---|---|---|---|
| **US-ADJ-52** | Documentación | Revisión documental transversal de todo lo tocado por el incremento: `RF_v1.md` (numeración definitiva de los RF nuevos de recuperación y autoregistro, y ajuste de "Decisiones de alcance" — el autoregistro coexiste con "Registro de estudiantes por invitación por comisión" ya listado), `docs/traceability/matrix.md` (altas y transición de estado de RF-20 a 23 y de los RF nuevos), `docs/design/ux/wireframes-*.md` (que reflejen lo efectivamente implementado, no solo lo aprobado en Iteración 0, si hubo ajustes en el camino), `CLAUDE.md`, **ADRs afectados** (revisar si `ADR-012` — "rechazo sin recuperación automática" — necesita una nota aclaratoria dado que ahora sí existe recuperación de contraseña, aunque para un caso distinto — password olvidada, no invitación rechazada —, y si el autoregistro amerita un ADR propio dado que introduce una segunda vía de alta de cuenta), y **modelos de dominio + event storming** ya elaborados (`BC-identidad-modelo.md`, `BC-analytics-modelo.md`) para que queden consistentes con la implementación final, no solo con lo aprobado en la Iteración 0 | Víctor confirma la revisión en el comentario de cierre del Issue; sin inconsistencias pendientes entre código e documentación de arquitectura/dominio |

---

## DoD del Incremento

Cualquier usuario puede recuperar su contraseña sin depender del Administrador, mostrar/ocultar
la contraseña al escribirla, y cerrar sesión voluntariamente; un Docente o Estudiante puede
autoregistrarse sin invitación (Estudiante asociándose a su Comisión real); la política de
contraseña segura rige en todos los formularios que la piden; el Docente tiene los 4 informes
de Analytics de RF-20 a RF-23 completos (backend + frontend); y toda la documentación de
arquitectura, dominio y trazabilidad queda auditada y consistente con lo implementado.

---

## Próximos pasos

1. ~~Revisar esta propuesta de candidatas con Víctor.~~ Hecho — 2026-09-12.
2. ~~Crear Milestone GitHub `Incremento 5-ADJ — Identidad Autoservicio y Analytics del
   Docente` + Issues para `US-ADJ-32` a `34`.~~ Hecho — Milestone
   [#13](https://github.com/vvalotto/cognion/milestone/13), Issues
   [#318](https://github.com/vvalotto/cognion/issues/318) (`US-ADJ-32`),
   [#319](https://github.com/vvalotto/cognion/issues/319) (`US-ADJ-33`),
   [#320](https://github.com/vvalotto/cognion/issues/320) (`US-ADJ-34`).
3. Ejecutar Iteración 0: modelo de Identidad (`US-ADJ-32`), modelo de Analytics (`US-ADJ-33`),
   wireframes/prototipo (`US-ADJ-34`), cada uno con aprobación explícita de Víctor.
4. Crear Issues y `docs/specs/ajustes/US-ADJ-NN.md` de las Iteraciones 1 a 4 a medida que se
   van habilitando (Iteración 1 no depende de nada más que `US-ADJ-34`; Iteración 2 y 3 ídem;
   Iteración 4 depende de `US-ADJ-33`/`34`).
5. Implementar Iteraciones 1 a 4 (independientes entre sí — se pueden intercalar según
   prioridad de Víctor, no hay dependencia técnica cruzada).
6. Ejecutar Iteración 5 (revisión documental) recién con las 4 iteraciones de código
   cerradas.
7. Cerrar baseline (`BL-010`) siguiendo `WORKFLOW-DESARROLLO.md` §7.
