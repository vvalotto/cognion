# Plan de pruebas — UAT manual de cierre de alcance v1

**Incremento:** 7, Iteración 1 (`docs/plans/inc7/inc7-candidatas.md`)
**Procedimiento:** `docs/plans/PROCEDIMIENTO-UAT.md` §11
**Fecha de escritura:** 2026-10-01
**Ejecutor:** Víctor (manual, en navegador real — Mac/iPhone/iPad según corresponda)
**Escritor:** sesión de Claude Code, narrado en vivo

---

## 1. Propósito y criterio de aceptación

Aceptación manual y exploratoria de **todo el sistema** (los 7 incrementos acumulados de
`docs/rf/PLAN_v1.md`, Incrementos 0 a 6 + sus ADJ) antes de dar el alcance v1 por cerrado,
previo a sumar RF-07 (Iteración 2 de este incremento). No es una repetición de las UAT por
incremento ya ejecutadas y aprobadas (`quality/reports/uat/inc1/` a `inc6/`) — esas certifican
cada feature puntual. Esta es la primera vez que alguien recorre el sistema **completo, de
punta a punta, con los 4 roles, sin cortes por incremento**.

**Criterio de aceptación de la iteración:** no es "cero hallazgos" — es tener el sistema
recorrido por completo y cada hallazgo clasificado por severidad (§8 de
`PROCEDIMIENTO-UAT.md`) y priorizado en el `plan-de-correccion.md`. La iteración cierra
cuando Víctor aprueba ese plan de corrección, no cuando no queda nada por corregir.

**Fuera de alcance de esta UAT** (sin implementar todavía, no se recorren):
- RF-07 (migración desde PDF) — Iteración 2 de este mismo incremento.
- RF-18 (KPIs históricos) — diferido, sin incremento asignado.

---

## 2. Entorno

- Rama `develop` local, backend FastAPI + PostgreSQL local (Homebrew), frontend `npm run dev`.
- **Regla operativa** (ya vigente desde la prueba de estabilización del Incremento 4-ADJ,
  `feedback_pytest_vacia_db_local`): no correr `pytest` en ninguna forma durante esta UAT —
  trunca la base de datos local compartida. Verificar hallazgos de backend con `curl` +
  `psql` directo, nunca confiando en un `200` sin releer la base.
- Datos: se reutilizan los datos reales ya sembrados en incrementos anteriores
  (`tests/uat/datos-reales/`, fuera de git) cuando alcancen para el recorrido — comisiones,
  materias, preguntas y cuentas de Ingeniería de Software y Gestión de Proyectos. Donde haga
  falta estado nuevo (ej. una sesión en vivo fresca, una cuenta recién autoregistrada), se
  crea en el momento, igual que en las bitácoras de estabilización.
- Si algún hallazgo requiere aislar una regresión, se puede usar una rama de verificación
  aparte (mismo criterio que `revision-manual-app.md`), sin tocar `develop` hasta clasificar
  el hallazgo.

---

## 3. Alcance — qué se recorre

Organizado por **recorrido real de usuario** (login → función), no por RF suelto — mismo
criterio que reveló el gap del portal de entrada en el Incremento 4-ADJ
(`docs/aprendizajes/HITO-9-PORTAL-DE-ENTRADA-SIN-DUENO-DE-PRODUCTO.md`). Cada bloque indica
los RF que cubre, ya "Validado" en `docs/traceability/matrix.md`.

### 3.1 — Identidad y acceso (sin rol todavía / los 3 roles)

| # | Recorrido | RF cubiertos |
|---|---|---|
| 1 | Autoregistro de un Docente nuevo (selección de perfil, cuenta activa de inmediato) | RF-25 |
| 2 | Autoregistro de un Estudiante nuevo (selección de perfil + Materia → Comisión) | RF-25 |
| 3 | Login con los 3 roles (Administrador, Docente, Estudiante) — portada post-login correcta por rol | RF-02 |
| 4 | 3 intentos fallidos de login → cuenta bloqueada, mensaje visible, formulario deshabilitado | RF-03, RF-19 |
| 5 | Recuperación de contraseña por autoservicio (solicitar → email → confirmar) | RF-24 |
| 6 | Cambio de la propia contraseña ya logueado, desde el menú de usuario | RF-19 |
| 7 | Registro de Estudiante por invitación (generar link desde una Comisión, vista previa sin login, registro) | RF-01 |
| 8 | Mostrar/ocultar contraseña e indicador de fortaleza en los formularios con password | — (ajuste Identidad Autoservicio) |

### 3.2 — Portal del Administrador

| # | Recorrido | RF cubiertos |
|---|---|---|
| 9 | Navegación completa por el menú persistente — todas las secciones accesibles | — (portal de entrada) |
| 10 | Materias: alta, edición, ver detalle, baja lógica (con/sin preguntas o comisiones asociadas), reactivar | — (CRUD de soporte) |
| 11 | Comisiones: alta desde el detalle de Materia, asignar Docente, ver detalle con estudiantes inscriptos, baja/reactivar | RF-01 (soporte) |
| 12 | Cuentas: listado con filtros por rol/estado/búsqueda, ver detalle, editar nombre/email, resetear contraseña (desbloqueo incluido), baja/reactivar según rol | RF-03 |

### 3.3 — Portal del Docente

| # | Recorrido | RF cubiertos |
|---|---|---|
| 13 | Materias y Comisiones propias únicamente (no debe ver ni operar sobre materias/comisiones de otro Docente) | — (`US-ADJ-57`) |
| 14 | Banco de preguntas: alta de pregunta opción múltiple y Verdadero/Falso, edición, baja lógica, filtro por unidad/tema/dificultad/importancia (con datalist) | RF-04, RF-05, RF-06 |
| 15 | Actividad de período abierto: crear (restringible a Comisión y a unidad/tema), ver listado y detalle, extender el plazo, cerrar manualmente, editar el título | RF-11, RF-11b |
| 16 | Generar y copiar/regenerar el link de invitación de una Comisión | RF-01 (soporte) |
| 17 | Sesión en vivo: crear desde el detalle de una Comisión, sala de espera con participantes en vivo, no permite iniciar sin participantes, cancelar una sesión en espera | RF-08 |
| 18 | Sesión en vivo: proyectar pregunta → mostrar opciones → cerrar (histograma + ranking) → avanzar, repetido para varias preguntas de distinto tipo (opción múltiple, V/F) | RF-09 |
| 19 | Sesión en vivo: finalizar desde cualquier etapa (no solo desde el ranking), podio final | RF-09, RF-10 |
| 20 | Reportes (landing unificada): Desempeño por alumno, por tema, por comisión (con drill-down a la revisión de un estudiante), evolución temporal, ranking de preguntas falladas, completitud por actividad | RF-16, RF-17, RF-20, RF-21, RF-22, RF-23 |
| 21 | Email de notificación recibido al abrir y al cerrar manualmente una actividad de período abierto (revisar el fake SMTP o la cuenta configurada) | RF-14 |

### 3.4 — Portal del Estudiante

| # | Recorrido | RF cubiertos |
|---|---|---|
| 22 | Ver sus materias y actividades disponibles, incluidas las "fuera de período" | RF-12 |
| 23 | Rendir una evaluación de período abierto: responder, pausar, reanudar (otra sesión/dispositivo), reintentar una respuesta con feedback de acierto/error | RF-12, RF-13 |
| 24 | Finalizar la evaluación como acción independiente de responder la última pregunta, ver la revisión completa | RF-13 |
| 25 | Unirse a una sesión en vivo desde el celular, sala de espera, responder con tarjetas táctiles, feedback personal inmediato (acierto + puntos), ver resultado/ranking final (Top 3) | RF-08, RF-09, RF-10 |
| 26 | Reconexión durante una sesión en vivo (apagar pantalla del celular y volver) sin perder sincronía | RF-08, RF-09 (RNF confiabilidad) |
| 27 | Ver "Mi desempeño" — resumen acumulado + detalle por evaluación, incluye lo rendido en modo en vivo | RF-15 |

### 3.5 — RNF explícitos a observar durante el recorrido (sin medición formal, solo lectura exploratoria)

No se remide bajo carga (eso ya está verificado — `US-6.2.9`, p95 43,81 ms) ni se abre el
checkpoint de staging con WSS real (`PROCEDIMIENTO-UAT.md` §4, sigue como ítem abierto fuera
de esta UAT salvo que Víctor decida resolverlo en el mismo momento). Sí se observa:

- **Legibilidad en proyección** (RNF-USA-2): si hay oportunidad de probar en un proyector o
  pantalla grande real durante el recorrido 17-19.
- **Reconexión sin pérdida de respuestas confirmadas** (RNF-CONF-1): recorrido 23 (pausa/
  reanuda) y 26 (reconexión en vivo).
- **RBAC transversal**: en cada recorrido de 3.2-3.4, intentar acceder a una URL de otro rol
  directamente (sin pasar por el menú) y confirmar que `RequireRole` bloquea.

---

## 4. Cosas puntuales a confirmar durante el recorrido

Deuda y notas abiertas ya registradas en `CLAUDE.md` que esta UAT es la oportunidad natural
de revisar:

- `HomeDocente.tsx` todavía no pasa por la landing "Reportes" ni incluye los 2 informes
  nuevos (RF-21/23) — confirmar si sigue así y si vale la pena resolverlo en el plan de
  corrección.
- El selector de materia de "Mi desempeño" nunca se ejercitó con una cuenta real
  multi-comisión (limitación conocida, sin bloquear el DoD de RF-15) — si hay un Estudiante
  real en más de una Comisión, probarlo; si no, dejarlo anotado como no verificable todavía.
- Decisión de infraestructura de producción / cuenta SMTP real — mencionar si Víctor quiere
  resolverla en esta misma sesión (no es parte del recorrido funcional, es una decisión
  institucional).

---

## 5. Cómo se registra

Cada paso ejecutado va al `registro-ejecuciones.md` (bitácora narrada por Víctor, escrita por
la sesión en vivo, mismo espíritu que `tests/uat/datos-reales/bitacora*.md`). Cada hallazgo
va al `registro-hallazgos.md`, clasificado 🔴/🟡/⚪ (§8). Al terminar el recorrido completo, la
sesión redacta el `plan-de-correccion.md` a partir del registro de hallazgos, para que Víctor
lo confirme — ese documento es el gate de cierre de esta iteración.

No hay un orden obligatorio entre los bloques 3.1-3.4 — Víctor puede recorrerlos en el orden
que le resulte más natural (por ejemplo, siguiendo el ciclo real: Administrador da de alta →
Docente prepara → Estudiante rinde → Docente revisa resultados), deteniéndose en cualquier
hallazgo antes de seguir.
