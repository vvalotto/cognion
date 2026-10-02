# Plan de corrección — UAT manual de cierre de alcance v1

**Incremento:** 7, Iteración 1 (`docs/plans/inc7/inc7-candidatas.md`)
**Procedimiento:** `docs/plans/PROCEDIMIENTO-UAT.md` §11
**Fecha:** 2026-10-02
**Estado:** **aprobado por Víctor el 2026-10-02** (6 decisiones, §7) — **gate de cierre de la Iteración 1 cumplido**
**Insumos:** `plan-de-pruebas.md`, `registro-ejecuciones.md` (30 pasos), `registro-hallazgos.md` (11 hallazgos)

> Documento de **priorización, no de ejecución**: propone qué se hace con cada hallazgo y en
> qué orden; no implementa nada. Track según `CLAUDE.md` §"Clasificación de hallazgos en UAT":
> solo `frontend/` → informal; cualquier archivo de `src/` → formal (US-IEDD/US-ADJ + spec).

---

## 1. Resumen

| | Total | Resueltos en la UAT | Abiertos |
|---|---|---|---|
| 🔴 Bloqueante | 2 | 0 | **2** (#4, #11) |
| 🟡 Observación | 6 | 1 (#3) | 5 (#1, #5, #6, #7, #10) |
| ⚪ Estético | 3 | 2 (#2, #8) | 1 (#9) |
| **Total** | **11** | **3** | **8** |

El recorrido de los 4 roles (3.1 Identidad, 3.2 Administrador, 3.3 Docente, 3.4 Estudiante,
más RBAC transversal) se completó sin interrupciones de flujo: **ningún hallazgo impidió
continuar y no hubo pérdida de datos** en ningún paso verificado contra la base. Los dos 🔴 no
son fallos de una pantalla sino **reglas del ciclo de vida de la cuenta** que el sistema no
hace cumplir; ambos son de producto/seguridad y se descubrieron por tocar `src/` y la base, no
por la UI.

Cambios de código hechos durante la UAT, **sin commitear** (solo `frontend/`, `tsc -b` y
`oxlint` limpios, tests de las pantallas afectadas en verde):
- #3 — aviso de borrado permanente en `EliminarCuenta.tsx`, `EliminarMateria.tsx`,
  `EliminarComision.tsx`.
- #8 — numeración de la revisión desde 1 en `RevisionEvaluacionContenido.tsx`.

---

## 2. Propuesta por hallazgo

| # | Sev. | Hallazgo (resumen) | Track | Prioridad | Acción propuesta |
|---|---|---|---|---|---|
| 11 | 🔴 | Una cuenta deshabilitada puede iniciar sesión y usar la API | **Formal** (`src/`) | **P1** | `US-ADJ-59` |
| 4 | 🔴 | El sistema puede quedar sin Administrador operativo (borrado físico, baja del último, bloqueo por reintentos) | **Formal** (`src/`) | **P1** | `US-ADJ-60` (después de `59`) |
| 10 | 🟡 | Actividad cerrada manualmente se ve "Pendiente de responder" / "Todavía no está disponible" | **Formal** (backend `EstadoVisible`) + gate UX | P2 | `US-ADJ-61` |
| 5 | 🟡 | Recuperar contraseña no desbloquea una cuenta bloqueada | **Formal** (`src/`), decisión de producto previa | P3 | `US-ADJ-62` si Víctor decide desbloquear |
| 7 | 🟡 | "Preguntas más falladas": mensaje vacío dice "ninguna pregunta presentada" | **Informal** (solo texto) | P3 | Fix directo; el alcance (excluir vivo) ya está decidido |
| 1 | 🟡 | Autoregistro: `201` sin persistir, intermitente, solo desde el navegador en dev | **Investigación** (no codear todavía) | P2 | Spike acotado, ver §4 |
| 6 | 🟡 | ~10 s de demora en el iPhone al mostrar opciones (el iPad anduvo bien) | **Verificación** (no codear todavía) | P3 | Reprobar iPhone y staging, ver §4 |
| 9 | ⚪ | Evolución temporal: etiqueta del eje truncada, promedio no visible con 1 dato | **Informal** (solo `frontend/`) | P4 | Revisar con más datos y corregir |
| 3 | 🟡 | Modal de eliminación no avisaba el borrado permanente | Informal | — | **Resuelto**, solo falta commit |
| 8 | ⚪ | Revisión numerada desde 0 | Informal | — | **Resuelto**, solo falta commit |
| 2 | ⚪ | Dato sucio en una cuenta Docente del entorno local | — | — | **Resuelto** (dato, no código) |

---

## 3. Detalle de las propuestas formales

### `US-ADJ-59` — Una cuenta deshabilitada no puede iniciar sesión (#11) · P1 · tamaño S

- **Qué:** `IniciarSesionUseCase` rechaza una cuenta con `deshabilitada = true`, antes de
  verificar la contraseña (no filtrar si la contraseña era correcta). El mensaje de la pantalla
  de login no debe revelar el motivo más de lo necesario.
- **Por qué primero:** hoy la "baja" es cosmética — un Docente o Estudiante dado de baja conserva
  acceso completo (login 200 + token válido, `GET /materias` 200). Es el único hallazgo con
  efecto de seguridad real y es la base de `US-ADJ-60` ("Administrador activo" solo tiene
  sentido si `deshabilitada` se hace cumplir).
- **Decisión de Víctor requerida:** ¿alcanza con rechazar el **login** y aceptar que las
  sesiones ya emitidas viven hasta expirar (JWT de 60 min sin blacklist, ADR-013), o el guard
  debe revalidar el estado en cada request (una consulta a la base por request, contradice la
  simplicidad de ADR-013)? **Recomendación:** solo login; 60 min de ventana es razonable a esta
  escala (30–60 alumnos) y evita tocar el guard compartido (`shared/`, ADR-019).
- **Dónde toca:** `src/identidad/use_cases/iniciar_sesion.py`, error de dominio nuevo o
  reutilizado; frontend: mensaje en `Login.tsx` si se distingue el caso.

### `US-ADJ-60` — El sistema siempre conserva al menos un Administrador operativo (#4) · P1 · tamaño M

Tres reglas, una invariante nueva ("existe ≥ 1 Administrador no deshabilitado y no bloqueado"):
1. **Un Administrador nunca se borra físicamente:** siempre baja lógica, tenga o no
   Comisiones creadas (`eliminar_cuenta.py`).
2. **No se puede deshabilitar/eliminar al último Administrador activo.**
3. **El bloqueo automático por 3 intentos fallidos no puede bloquear al último
   Administrador activo** (`iniciar_sesion.py`).

- **Decisión de Víctor requerida (regla 3):** hay una tensión real. Si el último Administrador
  nunca se bloquea, queda expuesto a fuerza bruta sin límite. Alternativas: (a) no bloquear
  pero con retardo creciente/bloqueo temporal por tiempo que se levanta solo; (b) permitir el
  bloqueo y documentar un procedimiento de desbloqueo directo en la base (`ADR-016` ya trata
  el alta del Administrador como bootstrap fuera del producto); (c) exigir ≥ 2 Administradores
  como práctica operativa. **Recomendación:** (a) — mantiene el sistema operable y no deja el
  ataque gratis; es lo único que no requiere intervención manual.
- **Depende de** `US-ADJ-59` (la noción de "activo" incluye "no deshabilitado").
- **Spec:** nueva invariante `INV-ID-xx` en `BC-identidad-modelo.md`; posible ADR chico si se
  elige (a).

### `US-ADJ-61` — La actividad cerrada se ve como cerrada para el Estudiante (#10) · P2 · tamaño M

- **Qué:** nuevo estado visible `cerrada` en `EstadoVisible` (`listar_actividades_visibles.py`),
  badge "Cerrada" en `MisActividades.tsx`, y en `FueraDePeriodo.tsx` mensaje propio ("Esta
  actividad ya cerró" vs "Todavía no abrió"), en lugar del mensaje único con nota al pie.
  "Mis materias" no debe contarla como "pendiente".
- **Gate UX obligatorio antes de `frontend/`:** el estado actual es **fiel al prototipo
  aprobado** (`wireframes-actividad-evaluativa.md`, `US-3.4.5`: "solo 3 badges"). Hay que
  actualizar wireframes/prototipo y que Víctor lo apruebe, no solo cambiar el código.
- **Verificar al especificar:** si "Desempeño por comisión" del Docente sigue contando como
  "actividad pendiente" a un estudiante que no rindió una actividad ya cerrada (no se verificó
  en la UAT).

### `US-ADJ-62` — Recuperar contraseña también desbloquea la cuenta (#5) · P3 · tamaño S · **condicional**

- **Decisión de producto de Víctor** (pidió anotarlo para revisar). **Recomendación:** sí
  desbloquear: abrir el link del mail y definir una contraseña nueva prueba el mismo control
  que el reseteo del Administrador, que ya desbloquea (`US-2.2.4`). Hoy el usuario bloqueado
  hace todo el recorrido de recuperación y sigue sin poder entrar, y depende del Administrador.
- Reabre una decisión tomada en `US-ADJ-39` (queda en el código como "no desbloquea la
  cuenta"), así que requiere actualizar esa spec y el docstring del router.
- Si se elige desbloquear, resetea también `intentos_fallidos_login` y
  `intentos_fallidos_password`. Interactúa con `US-ADJ-60` regla 3 (más razón para no dejar al
  último Administrador bloqueado).

---

## 4. Verificaciones antes de decidir (no codear todavía)

- **#1 — autoregistro `201` sin persistir.** Spike acotado (≈ 30 min): `npm run build` +
  `vite preview`, repetir el autoregistro de Docente ≥ 5 veces mirando el log del backend por
  `POST` duplicados y contrastando con la base (`psql`). Resultado posible: (i) no reproduce en
  build → documentar como artefacto de StrictMode/dev, cerrar sin cambios; (ii) reproduce →
  pasa a 🔴 y a track formal (revisar `AbortController`/doble envío en
  `AutoregistroDocente.tsx` y pantallas hermanas). **Dato extra:** en la recuperación de
  contraseña hubo un `422` desde el navegador con URL y token correctos que no se reprodujo por
  `curl` ni con un token nuevo — misma familia, tampoco explicado; incluirlo en el spike.
- **#6 — demora en el iPhone.** Reprobar el iPhone (misma sesión en vivo que el iPad) y, cuando
  exista, contra staging con WSS real (`PROCEDIMIENTO-UAT.md` §4, ítem abierto). Si el iPhone
  anda bien, cerrar como puntual de la primera corrida. Si repite, es un caso del "WebSocket
  zombi" de Safari iOS y se abre `US-ADJ` con repro.

---

## 5. Secuencia y dónde se hace

`inc7-candidatas.md` establece: hallazgo chico → Iteración 2 del Incremento 7; grande →
incremento de ajuste nuevo. Los hallazgos formales de arriba tocan `src/` y dos son 🔴, por lo
que propongo un incremento de ajuste, **igual que `3-ADJ` a `6-ADJ`** (fuera de la secuencia
0–7 de `PLAN_v1.md`, sin renumerar):

**Incremento 7-ADJ — Ciclo de vida de la cuenta y ajustes de la UAT v1**

| Orden | Ítem | Track |
|---|---|---|
| 0 | Commit de los fixes #3 y #8 (rama + PR a `develop`, que tiene branch protection) | Informal |
| 1 | Spike #1 (reproducir en build de producción) y re-prueba #6 | Verificación |
| 2 | `US-ADJ-59` (#11) | Formal |
| 3 | `US-ADJ-60` (#4) | Formal |
| 4 | `US-ADJ-61` (#10) con gate UX | Formal |
| 5 | #7 (texto) y #9 (evolución temporal) | Informal |
| 6 | `US-ADJ-62` (#5) solo si Víctor decide desbloquear | Formal |

**Recomendación de orden respecto de RF-07:** hacer el `7-ADJ` **antes** de la Iteración 2 del
Incremento 7 (RF-07, importación desde PDF): `59` y `60` son de seguridad y de integridad del
acceso, y el spike de RF-07 (parseo automático vs. asistido) sigue pendiente y necesita a
Víctor presente de todos modos. Con `59` y `60` hechos, el v1 puede cerrarse sin una cuenta
dada de baja con acceso vigente ni un riesgo de quedar sin Administrador.

---

## 6. Qué no cubrió esta UAT (declarado, no oculto)

- **RF-07** (importación desde PDF) y **RF-18** (KPIs históricos): sin implementar, fuera de
  alcance.
- **Contenido real de los emails** (RF-14 apertura/cierre manual y RF-24 recuperación): no hay
  SMTP de prueba en el entorno local (`ConnectionRefusedError`, esperado). Se verificó que el
  intento ocurre y que su fallo no bloquea la operación, y el token de recuperación se tomó de
  la base. Sigue abierto el ítem de la cuenta SMTP real (`CLAUDE.md`, "Ítems abiertos").
- **RNF-USA-2** (legibilidad en un proyector real) y el **checkpoint de staging con WSS real**
  (`PROCEDIMIENTO-UAT.md` §4): no se hicieron; la sesión en vivo se probó con Mac + iPhone/iPad
  por WiFi con el proxy de desarrollo.
- **Selector multi-materia de "Mi desempeño"**: no se pudo ejercitar (el dominio liga a un
  Estudiante con una sola comisión, limitación ya conocida).
- **Notificación de cierre manual** (RF-14): se verificó el intento de apertura; el de cierre
  no se revisó por separado.
- **Carga y volumen**: 3 estudiantes y 3 preguntas por sesión; el rendimiento bajo 60
  participantes ya se midió en `US-6.2.9` (p95 43,81 ms) y no se repitió.

---

## 7. Decisiones que necesito de Víctor para aprobar este plan

1. ¿Aprobás el **Incremento 7-ADJ** antes de RF-07, con el orden de §5?
   **✅ Aprobado por Víctor (2026-10-02).**
2. `US-ADJ-59`: ¿rechazar solo en login (60 min de ventana) o revalidar en cada request?
   **✅ Opción A — solo login (2026-10-02), confirmada explícitamente por Víctor.**
3. `US-ADJ-60`, regla 3: ¿bloqueo temporal/retardo creciente (recomendado), desbloqueo manual
   en base, o exigir ≥ 2 Administradores?
   **✅ Opción A — bloqueo temporal (2026-10-02).** El último Administrador activo se bloquea
   por tiempo (se propone ~15 min, valor a fijar en la spec) y se libera solo; el resto de las
   cuentas conserva el bloqueo actual hasta que un Administrador las desbloquee.
4. `#5`: ¿recuperar contraseña desbloquea? (si no, se descarta `US-ADJ-62`).
   **✅ Sí, desbloquea (2026-10-02).** `US-ADJ-62` queda confirmada: al canjear el token de
   recuperación también se resetean `bloqueada` e `intentos_fallidos_login`/`password`.
   Reabre la decisión de `US-ADJ-39`: actualizar esa spec y el docstring de
   `recuperacion_password_router.py`.
5. `#7`: ¿confirmás solo corregir el texto (el alcance "vivo excluido" ya se decidió el
   2026-09-27 en `US-ADJ-56`)?
   **✅ Solo el texto del ranking (2026-10-02).** Fix informal en `frontend/`; texto
   propuesto: "Todavía no hay evaluaciones de período abierto finalizadas con preguntas de
   esta materia." No se toca el mensaje de "Desempeño por tema".
6. ¿Commiteamos ya los fixes #3 y #8 en una rama y PR aparte?
   **✅ Sí (2026-10-02)**, rama `fix/uat-v1-hallazgos-3-y-8` con 3 commits (#3, #8, docs de la
   UAT); #7 queda para el 7-ADJ. Las contraseñas de las cuentas de prueba se redactaron de
   `registro-ejecuciones.md` antes de commitear (viven solo en el entorno local).

Con tu aprobación quedan cerrados la Iteración 1 del Incremento 7 y este plan; los números
`US-ADJ-59` a `62` y el Milestone se crean recién entonces (no hay Issues ni specs todavía).
