# Registro de ejecuciones — UAT manual de cierre de alcance v1

Narrado por Víctor, escrito por la sesión de Claude Code en vivo. Entorno: `develop` local,
backend (`:8000`) + frontend (`npm run dev`, `:5173`) levantados al inicio de la sesión,
PostgreSQL local (Homebrew) ya corriendo.

---

## Bloque 3.1 — Identidad y acceso

### Paso 1 — Autoregistro de Docente (RF-25)

- **Intento 1:** Víctor crea una cuenta Docente con `DocentePrueba@Test.com` desde
  `/autoregistro` → elige perfil Docente → completa el formulario → el flujo lo manda a
  `/login`. Backend logueó `POST /identidad/autoregistro/docente` → `201 Created`.
  **Verificado con `psql` directo:** la tabla `usuario` no tiene esa cuenta — solo existía el
  admin preexistente. Ver hallazgo #1.
- **Intento 2:** Víctor repite con `docente.uat7b@test.com` / `‹contraseña de prueba local›`, un solo clic en
  "Crear cuenta". Backend logueó **dos** `POST /identidad/autoregistro/docente` → `201
  Created` seguidos. Verificado con `psql`: esta vez sí quedó persistida una fila
  (`d30b1dc3-8071-4f8a-a548-9ba4ade6b101`, `docente.uat7b@test.com`).
- Primer intento de login con esa cuenta → error. Verificado por `curl` directo que la cuenta
  y la contraseña están bien guardadas (login 200 OK por `curl`).
- Víctor reintenta el login desde el navegador → **entra bien**.
- **Resultado:** cuenta de Docente autoregistrada funcional tras reintento. Hallazgo #1
  registrado (`registro-hallazgos.md`), no bloquea continuar.

### Paso 2 — Autoregistro de Estudiante (RF-25) — INTERRUMPIDO

Víctor intenta autoregistrarse como Estudiante: el selector de Materia/Comisión no tiene
nada para mostrar — la base estaba completamente limpia (0 materias, 0 comisiones, 0
administradores). Se reordena el recorrido: primero 3.2 (Administrador crea la base), después
se retoma este paso.

---

## Bloque 3.2 — Portal del Administrador (intercalado, para desbloquear 3.1 Paso 2)

### Hallazgo de entorno — sin cuenta de Administrador

La base no tenía ninguna fila en `administrador` — la única cuenta preexistente
(`victor.valotto@fiuner.edu.ar`) resultó ser **Docente**, no Administrador (coincide con
`tests/uat/datos-reales/usuarios.md`, que documenta un Docente con ese email y un
Administrador aparte, `admin@fiuner.edu.ar`, que no estaba sembrado en esta base). Se corrió
el bootstrap (`scripts/seed_admin.py`, `ADR-016`) con los datos documentados —
`admin@fiuner.edu.ar` / `‹contraseña de prueba local›` — y quedó creado y verificado por `psql`.

### Paso 1 — Login de Administrador

Login con `admin@fiuner.edu.ar` / `‹contraseña de prueba local›` → entra bien, portada y menú correctos.

### Paso 2 — Alta de Materia

Crea "Materia UAT7" → aparece en el listado. Verificado por `psql`: persistida correctamente
(`materia.activa = true`).

**Hallazgo de dato sucio (no bloqueante):** la cuenta Docente preexistente
(`victor.valotto@fiuner.edu.ar`) tiene el campo `nombre` cargado como
`docente.nuevo@test.com` en vez de "Victor Valotto" — dato residual de alguna prueba
anterior a esta sesión, no reproducido en esta UAT. Visible en cualquier selector de Docente.

### Paso 3 — Alta de Comisión + asignación de Docente

Crea "Comisión 1 - Lunes 10 a 13" dentro de "Materia UAT7" → pide asignar Docente. Víctor
asigna "Docente UAT7" (la cuenta autoregistrada en el Paso 1 de 3.1). Verificado por `psql`:
fila en `comision_docentes` correcta (`comision_id` → `docente_id` de Docente UAT7).

### Paso 4 — Edición de Materia

Víctor edita el nombre a "Materia - UAT7". Verificado por `psql`: persistido correctamente.

### Paso 5 — Baja lógica de Materia (con Comisión asociada)

Baja de "Materia - UAT7" (tiene una Comisión asociada) → queda inactiva en el listado.
Verificado por `psql`: `materia.activa = false`.

### Paso 6 — Reactivar Materia

Reactiva "Materia - UAT7". Verificado por `psql`: `materia.activa = true`.

### Paso 7 — Detalle de Comisión

Víctor confirma que el detalle de "Comisión 1 - Lunes 10 a 13" se ve bien, con el Docente
asignado correcto (sin estudiantes inscriptos todavía — se prueba más adelante).

---

## Bloque 3.2 (cont.) — Cuentas

### Paso 8 — Listado y filtros de Cuentas

Listado muestra las 4 cuentas (Administrador, Docente garbled, Docente Prueba Curl, Docente
UAT7), coincide con la base. Filtro Rol=Docente + búsqueda "UAT" → 2 resultados correctos
(Docente Prueba Curl, Docente UAT7). Los 3 filtros (rol, estado, búsqueda) probados por
Víctor, sin hallazgos.

### Paso 9 — Detalle y edición de cuenta (resuelve el hallazgo #2 de paso)

Víctor entra al detalle de `victor.valotto@fiuner.edu.ar` y corrige el nombre a "VICTOR
OCTAVIO VALOTTO". Verificado por `psql`: persistido correctamente.

### Paso 10 — Resetear contraseña de cuenta

Reseteo de contraseña de "Docente Prueba Curl" a `‹contraseña de prueba local›`. Verificado por `curl`:
login con la nueva contraseña → 200 OK.

### Paso 11 — Baja de cuenta sin datos asociados

Baja de "Docente Prueba Curl" (sin Comisiones asociadas) → la fila desaparece del listado.
Verificado por `psql`: la cuenta fue **borrada físicamente** de `usuario` (no deshabilitada) —
comportamiento documentado y correcto (`CLAUDE.md`: baja lógica solo si hay datos
asociados). Hallazgo #3: el modal de confirmación no distinguía este caso permanente del caso
reversible — **corregido en el momento** (frontend, 3 pantallas), ver `registro-hallazgos.md`.

### Observación de Víctor — el sistema puede quedar sin Administrador

Al revisar el bloque, Víctor nota que nada protege al Administrador de quedar sin ningún
usuario operativo con ese rol. Verificado en el código (`eliminar_cuenta.py`,
`iniciar_sesion.py`): el Administrador se borra físicamente igual que Docente/Estudiante si
no tiene Comisiones creadas, no hay guardia contra deshabilitar al último Administrador
activo, y el bloqueo automático por 3 intentos fallidos de login tampoco distingue este caso.
Hallazgo #4 (🔴, track formal) — no se corrige en caliente, queda para el
`plan-de-correccion.md`.

**Cierra el bloque 3.2 — Portal del Administrador.**

### Paso 2 (retomado) — Autoregistro de Estudiante (RF-25)

Con "Materia - UAT7" / "Comisión 1 - Lunes 10 a 13" ya disponibles, Víctor se autoregistra
como Estudiante (`estudiante.uat7a@test.com`). Selector Materia → Comisión funcionó bien.
Verificado por `psql`: persistido correctamente, `comision_id` correcto, sin repetirse el
problema intermitente del hallazgo #1.

**Cierra el bloque 3.1 — Identidad y acceso** (pasos 1-2 completos; los pasos 3-8 del plan de
pruebas —bloqueo por reintentos, recuperación de contraseña, cambio de la propia contraseña,
registro por invitación, mostrar/ocultar contraseña— quedan para retomar si hace falta, o se
cubren de forma natural en los bloques 3.3/3.4).

### Paso 3 — Portada post-login por rol

Administrador ya confirmado (3.2 Paso 1). Víctor loguea como "Docente UAT7" y reporta **3
cards** en la home, no 4 como decía `CLAUDE.md`. Verificado en código
(`frontend/src/pages/HomeDocente.tsx` + `git log`): correcto — PR #374 ("unificar Reportes en
Home del Docente") consolidó los informes de Analytics bajo una sola card "Reportes" después
de `US-ADJ-28`. La nota de deuda en `CLAUDE.md` sobre esto está **desactualizada**, no es un
hallazgo de esta UAT — se corrige en el barrido documental, no en `plan-de-correccion.md`.

### Paso 4 — Bloqueo por 3 intentos fallidos

3 intentos fallidos contra `docente.uat7b@test.com` → bloqueada en el tercero. Verificado por
`psql` (`bloqueada = true`, `intentos_fallidos_login = 3`) y por `curl` (login con la
contraseña *correcta* ahora da `403 Forbidden`). En el navegador se ve la alerta "Cuenta
bloqueada" con el formulario completo deshabilitado, igual que especifica `US-2.2.9`. Sin
hallazgos.

### Paso 5 — Recuperación de contraseña (RF-24)

Solicitud de recuperación para `docente.uat7b@test.com` → `202 Accepted`. Sin SMTP de prueba
levantado en este entorno (`ConnectionRefusedError` en el log, esperado — item de
infraestructura pendiente, no bug). Token verificado por `psql`
(`token_recuperacion_password`, expira en 1 hora). Primer intento de confirmar falló con
`422` porque la URL armada por la sesión era incorrecta (`?token=` en vez del path param
`/recuperar-password/:token`) — error de la sesión, no del producto. Segundo intento (URL
correcta) también dio `422` en el navegador real, pero el mismo token+password funcionó por
`curl` — no se identificó la causa puntual del navegador (posible variante del patrón de
doble envío de los formularios con `AbortController`, no confirmado). Con un token nuevo,
tercer intento desde el navegador **funcionó** (contraseña actualizada). Al intentar loguear
con la cuenta recuperada, Víctor ve "cuenta bloqueada" — confirmado en código
(`recuperacion_password_router.py`): la recuperación de contraseña **no desbloquea la
cuenta**, diseño intencional de `US-ADJ-39`. Hallazgo #5 registrado para revisar como posible
mejora de producto, sin tocar código.

### Paso 6 — Cambio de la propia contraseña

Víctor cambia la contraseña de "Docente UAT7" a `‹contraseña de prueba local›` desde el menú de usuario.
Verificado por `curl`: login con la nueva contraseña → 200 OK.

### Paso 7 — Registro de Estudiante por invitación (RF-01)

Víctor genera el link de invitación de "Comisión 1 - Lunes 10 a 13" como Docente, lo abre sin
sesión (vista previa pública, `US-ADJ-08`) y registra un Estudiante nuevo ("Jose Perez",
`jose.perez@fiuner.edu.ar`). Verificado por `psql`: persistido correctamente en la Comisión
correcta. Sin hallazgos.

### Paso 8 — Mostrar/ocultar contraseña e indicador de fortaleza

Víctor confirma, probado varias veces en distintos formularios: correcto.

**Cierra completo el bloque 3.1 — Identidad y acceso (8/8 pasos).**

---

## Resumen de la mini-sesión (3.1 + parte de 3.2)

- **3.1 — Identidad y acceso:** 8/8 pasos ejecutados.
- **3.2 — Portal del Administrador:** Materias, Comisiones, Cuentas cubiertos (pasos 1-11).
  Quedan sin ejecutar explícitamente: ver detalle de Cuenta con datos asociados (baja lógica
  + reactivar sobre una cuenta CON Comisiones/evaluaciones, a diferencia del caso sin datos ya
  probado).
- **Hallazgos:** 5 registrados — 2 resueltos en el momento (#2 dato sucio, #3 copy del modal),
  1 abierto técnico de severidad media (#1, 201 sin persistir intermitente), 1 abierto de
  producto 🔴 (#4, Administrador sin protección contra quedar sin ninguno operativo), 1 abierto
  de producto a decidir (#5, recuperación de contraseña no desbloquea).
- **Pendiente:** bloques 3.3 (Docente) y 3.4 (Estudiante) completos, más el resto de
  recorridos del plan de pruebas.

## Bloque 3.3 — Portal del Docente

Criterio acordado con Víctor: no sembrar datos sintéticos aparte — los datos de Reportes
(recorrido 20) salen orgánicamente del propio recorrido (Docente prepara → Estudiante rinde →
Docente revisa), manteniendo todo bajo "Materia - UAT7" / "Docente UAT7" para no mezclar con
la cuenta Docente real y ensuciar la verificación de RBAC del paso 13.

### Paso 13 — Materias y Comisiones propias (RBAC, `US-ADJ-57`)

Login como "Docente UAT7". El menú muestra solo "Materia - UAT7" — RBAC correcto, sin
hallazgos.

### Paso 14 — Banco de preguntas

Víctor carga 3 preguntas (2 opción múltiple, 1 Verdadero/Falso) en unidades temáticas
distintas ("Requerimientos"/"Testing"/"Ingeniería de Software"). Verificado por `psql`:
persistidas correctamente, `activa = true`. Sin hallazgos.

### Paso 14b — Filtro del banco

Filtro por unidad temática y dificultad probado por Víctor: correcto.

### Paso 15 — Actividad de período abierto (RF-11)

Víctor crea "Parcial 1" para "Comisión 1 - Lunes 10 a 13". Verificado por `psql` contra el
event store: `ActividadEvaluativaCreada` con el título y la comisión correctos. Sin
hallazgos.

### Paso 15b — Extender plazo y editar título (RF-11b, `US-ADJ-10`)

Víctor extiende el plazo y edita el título a "Parcial numero 1". Verificado por `psql` contra
el event store: `PeriodoDisponibilidadModificado` (nueva fecha 2026-10-03) y
`TituloActividadModificado` correctos. Sin hallazgos.

### Preparación para sesión en vivo — frontend de red + autoregistro desde iPhone

Se reinicia el frontend con la variante de red (`cognion-frontend-red`, IP de la Mac
`192.168.1.71:5173`) para que el iPhone de Víctor pueda unirse. Autoregistro de Estudiante
hecho directo desde el iPhone (`estudiante.iphone@test.com` / `‹contraseña de prueba local›`, "Materia -
UAT7" / "Comisión 1 - Lunes 10 a 13"). Verificado por `psql`: persistido correctamente.
Legibilidad y tamaño táctil en el celular: correcto, sin hallazgos.

### Paso 16 — Docente crea la sesión en vivo (RF-08)

Víctor, como "Docente UAT7" en la Mac, crea la sesión en vivo desde el detalle de la Comisión
y queda en la sala de espera. El Estudiante ("Prueba") se une desde el iPhone y aparece en la
sala de espera de la Mac en tiempo real (WebSocket). Sin hallazgos.

### Pasos 17-19 — Sesión en vivo completa (RF-08, RF-09, RF-10)

Sesión completa de 3 preguntas, Docente en la Mac + Estudiante real en el iPhone (vía
`cognion-frontend-red`). Verificado por `psql` contra el event store: 11 eventos en el stream
de la actividad (creada → iniciada → 3× opciones/cierre → finalizada) y 4 eventos en el
stream de participación (unido + 3 respuestas, todas correctas, con puntaje y tiempo de
respuesta reales). **Hallazgo #6** (🟡): demora de ~10s mostrando las opciones de la primera
pregunta en el iPhone y reconexión necesaria al finalizar — sin pérdida de datos, mismo
patrón ya documentado del "WebSocket zombi" de Safari iOS. Registrado para revisar contra un
entorno más parecido a producción.

**Cierra el recorrido de sesión en vivo del bloque 3.3.**

### Paso 20 — Reportes (RF-16/17/20-23)

"Desempeño por alumno" sobre "Prueba" (el Estudiante del iPhone): 3 correctas, 0 incorrectas,
5676 pts (suma exacta de los 3 puntajes de la sesión en vivo), 1° de 1, correctamente separa
"sesiones en vivo" de "evaluaciones finalizadas" (vacío, esperado — todavía no rindió
"Parcial numero 1"). Sin hallazgos.

"Desempeño por comisión": los 3 estudiantes con "Sin datos" en % Aciertos (correcto — nadie
finalizó todavía una evaluación de período abierto, la sesión en vivo se contabiliza aparte)
y "1 actividad pendiente" cada uno. Sin hallazgos.

"Desempeño por tema": mensaje correcto "Esta materia todavía no tiene ninguna evaluación
finalizada". Sin hallazgos.

"Preguntas más falladas": mensaje "todavía no tiene ninguna pregunta presentada" — impreciso
o gap, ver hallazgo #7 (las 3 preguntas de la sesión en vivo sí se presentaron, solo que
ninguna se falló).

Quedan por recorrer: evolución temporal, completitud por actividad — se revisan más a fondo
después de 3.4, con más datos de período abierto disponibles.

### Paso 21 — Notificación por email (RF-14)

Verificado por log del backend: al crear "Parcial numero 1" se intentó notificar a los 2
estudiantes de la Comisión (`estudiante.uat7a@test.com`, `jose.perez@fiuner.edu.ar`) — falla
el envío real por falta de SMTP local (esperado, mismo motivo que el hallazgo del paso 5), sin
bloquear la creación de la actividad. Sin hallazgos.

**Cierra el bloque 3.3 — Portal del Docente**, salvo: cerrar manualmente "Parcial numero 1"
(diferido hasta después de 3.4) y confirmar las 2 pantallas de Reportes restantes (evolución
temporal, completitud por actividad) con más datos.

---

## Bloque 3.4 — Portal del Estudiante (sesión 2026-10-02)

Servidores levantados de nuevo (backend :8000, `cognion-frontend-red` :5173, IP de la Mac
`192.168.1.71` sin cambios). Datos de la sesión anterior intactos en la base (6 usuarios).

### Paso 22 — Home, materias y actividades disponibles (RF-12)

Víctor loguea como Estudiante (`estudiante.iphone@test.com`): ve la home con sus cards y
"Parcial numero 1" de "Materia - UAT7" disponible. Sin hallazgos.

### Paso 23 — Rendir: responder, suspender, reanudar (RF-12, RF-13, RNF-CONF-1)

Víctor inicia/continúa "Parcial numero 1", responde una pregunta, suspende, cierra la pestaña,
vuelve a entrar y retoma donde estaba, y responde las siguientes. Verificado contra el event
store (stream `Evaluacion` `def66b81…`, 8 eventos): `EvaluacionIniciada` (2026-10-01 19:00
UTC, de la sesión anterior) → `EvaluacionSuspendida` con `actor=sistema` (2026-10-02 11:37,
`VerificadorDeVencimientos` Regla 1 por inactividad al arrancar el backend — correcto,
`US-3.2.4`) → `EvaluacionReanudada` → `RespuestaRegistrada` (correcta) →
`EvaluacionSuspendida` (`actor=estudiante`) → `EvaluacionReanudada` → 2 `RespuestaRegistrada`
más (una incorrecta, una correcta). Set de preguntas y respuestas confirmadas intactos tras
reanudar — RNF-CONF-1 cumplido. Sin hallazgos.

### Paso 24 — Finalizar y ver la revisión completa (RF-13)

Víctor finaliza la evaluación y ve "Revisión completa": 2 correctas, 1 incorrecta, 3 total,
con "Tu respuesta" y, en la incorrecta, "Respuesta correcta". Verificado por `psql`:
`EvaluacionFinalizada` (`actor=estudiante`) como evento 9 del stream, y el detalle coincide
con las 3 `RespuestaRegistrada`. **Hallazgo #8** (⚪): las preguntas se numeran desde 0 —
corregido en el momento (`fila.orden + 1`).

### Paso 20 (retomado) — Reportes del Docente con datos de período abierto

Con "Prueba" habiendo finalizado "Parcial numero 1" (2/3): "Desempeño por comisión" muestra
66,67 % para Prueba y "Sin datos"/1 pendiente para los otros dos; "Desempeño por alumno"
coincide con "Mi desempeño"; "Desempeño por tema" (Requerimientos/Procesos 100 % de error,
Ingeniería de Software/General y Testing/Conceptos 0 %, 1 respuesta cada uno); "Preguntas más
falladas" (1. Ciclo de Requerimientos 100 %, 2./3. 0 %, 1 presentación cada una — confirma
que el informe no cuenta sesiones en vivo, ver hallazgo #7); "Evolución temporal" vía
drill-down (un punto a ~67 %). Hallazgo #9 (⚪, evolución temporal con 1 dato).

"Completitud por actividad" (RF-23) — se accede desde el detalle de la actividad ("Ver
completitud"), no desde la landing de Reportes (anotado: poco descubrible, a evaluar en el
plan de corrección): 1 finalizada (Prueba), 0 en curso, 0 suspendidas, 2 sin iniciar (Estudiante
UAT7, Jose Perez). Coincide con la base. Sin hallazgos. **Con esto los 6 informes de Analytics
quedan revisados.**

### Paso 15c — Cierre manual de la actividad (RF-11b) y vista del Estudiante que no rindió

Víctor cierra "Parcial numero 1" como Docente (2026-10-02 12:05 UTC; verificado en el event
store: `ActividadEvaluativaCerrada`, 4.º evento del stream; el período por fecha seguía
vigente hasta 3/10 15:39 UTC). Como Estudiante sin rendir (`estudiante.uat7a@test.com`, a quien
se le reseteó la contraseña por el endpoint de Administrador para poder usarla): el listado
sigue mostrando "Pendiente de responder" y al entrar aparece "Todavía no está disponible". El
backend rechaza iniciar correctamente. **Hallazgo #10** (🟡): mensaje/estado engañosos para una
actividad cerrada.

### Paso 29 — Baja lógica de una cuenta con datos asociados (RF-03)

Víctor, como Administrador, da de baja a "Docente UAT7" (con una Comisión asignada). Verificado
por `psql`: `deshabilitada = true`, fila y asignación a la Comisión conservadas; el listado la
muestra "Inactiva" con botón de reactivar. **Hallazgo #11** (🔴): esa cuenta deshabilitada
**sigue pudiendo iniciar sesión** (200 + token válido, `GET /materias` 200) — la baja no
revoca el acceso. Reactivación desde el listado verificada por `psql`
(`deshabilitada = false`).

### Paso 26 — Reconexión durante una sesión en vivo (RF-08/09, RNF-CONF-1)

Segunda sesión en vivo, esta vez con un **iPad** como dispositivo del Estudiante (cuenta
`estudiante.iphone@test.com`) en lugar del iPhone. Víctor reporta que **funcionó
correctamente**, incluida la resincronización tras apagar/encender la pantalla. Verificado
por `psql`: stream de la actividad completo (creada → iniciada → 3 ciclos opciones/cierre →
finalizada) y 2 respuestas registradas (correctas, 1759 y 2144 pts; la primera con 12,6 s de
tiempo de respuesta). Dato nuevo para el hallazgo #6: el iPad no mostró la demora que el
iPhone tuvo el día anterior — apunta a algo específico del dispositivo/condición de red de
esa primera prueba más que a un fallo general del canal (aún sin confirmar; el iPhone no se
volvió a probar).

### Paso 30 — Baja y reactivación de Comisión y Materia (con datos asociados)

Víctor desactiva la Comisión y la Materia ("Materia - UAT7", con 3 estudiantes inscriptos) y
las vuelve a activar. Verificado por `psql`: ambas `activa = true` al final, los 3 estudiantes
conservados (baja lógica sin pérdida de datos). Sin hallazgos propios de este paso. **Cierra
el bloque 3.2 por completo.**

### Paso 28 — RBAC transversal (RNF-SEG-1, RF-02)

Frontend: Víctor, como Estudiante, pega a mano `/cuentas`, `/materias`, `/analytics` → "Acceso
denegado" en las tres (`RequireRole`). Backend, por `curl` con tokens reales: Estudiante →
`GET /usuarios`, `GET /materias`, `POST /materias`, `POST /preguntas/verdadero-falso`,
analytics de la materia: **403** en los 5; Docente → `GET /usuarios`, `POST /materias`
(exclusivo del Administrador desde PR #370), `POST /comisiones`: **403** en los 3; sin token →
`GET /usuarios`: **401**. Sin hallazgos.

### Paso 27 — Mi desempeño (RF-15, `US-ADJ-56`)

"Mi desempeño" de "Materia - UAT7": 2 correctas / 1 incorrecta (acum.), 67 % de acierto, 1
evaluación finalizada; detalle "Parcial numero 1" finalizada 2/10 08:45 (hora local
correcta); sección "Sesiones en vivo" separada con la sesión de ayer (3 ✓, 0 ✗, 5676 pts, 1°
de 1). Todo coincide con el event store. Sin hallazgos.

*(continúa a medida que se ejecutan los siguientes pasos del `plan-de-pruebas.md`)*
