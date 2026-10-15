# Plan de pruebas — UAT de cierre del Incremento 7-ADJ

**Incremento:** 7-ADJ (`docs/plans/inc7-adj/inc7-adj-candidatas.md`) · cierre previsto como `BL-012`
**Procedimiento:** `docs/plans/PROCEDIMIENTO-UAT.md` §11 (misma mecánica que la UAT v1 de `quality/reports/uat/inc7/`)
**Fecha de escritura:** 2026-10-05
**Ejecutor:** Víctor (navegador real) · **Guía y escritor:** sesión de Claude Code, en vivo

---

## 1. Propósito y criterio de aceptación

Verificar en **navegador real, contra backend y base reales** lo que el 7-ADJ cerró solo con tests
automatizados (que mockean `fetch` y no ven lo que un navegador sí), y resolver los dos
hallazgos de la UAT v1 que seguían abiertos como verificación (#1 y #6).

**Criterio de aceptación:** cada caso queda ejecutado con resultado registrado y cada hallazgo
clasificado (§8 de `PROCEDIMIENTO-UAT.md`). La UAT cierra sin 🔴 abiertos. No es "cero hallazgos".

**Fuera de alcance:** RF-07 (importación PDF, Iteración 2 del Incremento 7), RF-18, y todo lo ya
recorrido en la UAT v1 que el 7-ADJ no tocó.

## 2. Entorno y reglas

- `develop` local (commit `1f1aac8` o posterior), backend FastAPI + PostgreSQL local, frontend Vite.
- **Base `cognion` hoy vacía (0 usuarios) y en la revisión `a6c2d4f8b1e3`: falta
  `alembic upgrade head` (`c4d1f9a27b60`, `usuario.bloqueada_hasta`).** Preparación = Bloque 0.
- **No correr `pytest` en ninguna forma** durante la UAT (vacía la base compartida). Verificar con
  `curl` + `psql`, nunca confiando en un `200` sin releer la base.
- **Sin SMTP local:** los emails (recuperación de contraseña) no salen; el token se toma de la
  tabla `token_recuperacion_password` con `psql`. Se verifica que el intento ocurre y que su
  fallo no bloquea la operación (ya verificado en la UAT v1).
- Cuentas, contraseñas y datos sembrados: `tests/uat/datos-reales/` (fuera de git).

## 3. Casos de prueba

Cada caso: **precondición → pasos → resultado esperado**. Resultado y evidencia van a
`registro-ejecuciones.md`; lo que no cumple, a `registro-hallazgos.md`.

### Bloque 0 — Preparación del entorno (Claude)
| # | Qué | Esperado |
|---|---|---|
| 0.1 | `alembic upgrade head` sobre `cognion` | revisión `c4d1f9a27b60` |
| 0.2 | Sembrar con `tests/uat/datos-reales/sembrar.py` (Administrador, 2 Docentes, Comisión con 17 Estudiantes, bancos, 2 actividades con estados variados) | `psql` confirma usuarios, comisiones, preguntas y eventos |
| 0.3 | Levantar backend (`:8000`) y frontend dev (`:5173`) | `/docs` responde; login del Administrador OK |

### Bloque 1 — Spike hallazgo #1: autoregistro `201` sin persistir (Claude + Víctor)
Hipótesis a descartar o confirmar: doble envío / `AbortController` bajo `StrictMode` en modo dev.
| # | Qué | Esperado / decisión |
|---|---|---|
| 1.1 | **Build de producción** (`npm run build` + `vite preview`): autoregistrar un Docente ≥ 5 veces mirando el log del backend (`POST` duplicados) y contrastando con `psql` | Cada `201` ↔ una fila en `usuario` |
| 1.2 | **Modo dev** (`npm run dev`): repetir ≥ 5 veces | Idem; si falla solo acá → artefacto de StrictMode |
| 1.3 | Mismo ejercicio con autoregistro de Estudiante y con "Definir nueva contraseña" (el `422` desde navegador sin explicar) | Idem |
| Resultado | (i) no reproduce en build → documentar como artefacto de dev, cerrar sin cambios; (ii) reproduce → 🔴 y track formal (`AutoregistroDocente.tsx` y hermanas) |

### Bloque 2 — `US-ADJ-59`: una cuenta deshabilitada no inicia sesión
| # | Pasos | Esperado |
|---|---|---|
| 2.1 | Administrador deshabilita a un Docente de prueba; ese Docente intenta loguearse con la contraseña correcta | Rechazo con alerta "Cuenta deshabilitada…"; **sin token**, no consume intentos |
| 2.2 | Idem con contraseña incorrecta | Mismo mensaje (no revela si la contraseña era válida) |
| 2.3 | Administrador reactiva la cuenta; el Docente vuelve a loguear | Login 200 |

### Bloque 3 — `US-ADJ-60`: siempre existe al menos un Administrador operativo
| # | Pasos | Esperado |
|---|---|---|
| 3.1 | Con **un solo** Administrador operativo, intentar deshabilitarlo (desde otro contexto no aplica: se prueba por API/`curl` con su propio token) | `409` "último Administrador operativo", no se deshabilita |
| 3.2 | Ese Administrador falla el login 3 veces | Alerta "bloqueada temporalmente" con minutos restantes; **formulario habilitado** (no permanente) |
| 3.3 | Simular vencimiento (`UPDATE usuario SET bloqueada_hasta = now() - interval '1 min'`) y loguear | Login 200 — el bloqueo se levanta solo |
| 3.4 | Crear un 2.º Administrador y deshabilitar al 1.º | Permitido (queda uno operativo) |
| 3.5 | Pantalla de eliminación de un Administrador | Variante "Deshabilitar cuenta" (nunca borrado) |

### Bloque 4 — `US-ADJ-62`: recuperar la contraseña desbloquea
| # | Pasos | Esperado |
|---|---|---|
| 4.1 | Estudiante falla 3 veces → alerta "Cuenta bloqueada" | La alerta trae el link **"recuperar tu contraseña por email"** y la opción de pedírselo a un Administrador |
| 4.2 | Click en el link → solicitar → tomar token de `psql` → definir contraseña nueva válida | Éxito |
| 4.3 | Loguear con la contraseña nueva | 200, **sin intervención de un Administrador**; `bloqueada = false` y contadores en 0 (`psql`) |
| 4.4 | Repetir 4.1-4.3 con el Administrador bloqueado temporalmente (3.2) | Queda libre (`bloqueada_hasta` NULL) |
| 4.5 | Cuenta **deshabilitada** + recuperar contraseña | Sigue sin poder entrar (`cuenta_deshabilitada`) |

### Bloque 5 — `US-ADJ-61`: la actividad cerrada se ve como cerrada
| # | Pasos | Esperado |
|---|---|---|
| 5.1 | Docente cierra a mano una actividad que un Estudiante no rindió; el Estudiante abre "Actividades" | Badge **"Cerrada"** (gris), no "Pendiente de responder" |
| 5.2 | Click en la tarjeta | "Esta actividad ya cerró" + fecha de cierre; sin "volvé a entrar" |
| 5.3 | "Mis materias" del Estudiante | No cuenta la cerrada como pendiente |
| 5.4 | Actividad **vencida por fecha** sin rendir | Mismo badge "Cerrada" |
| 5.5 | Estudiante que ya finalizó una actividad luego cerrada | Sigue viendo "Finalizada — ver revisión" |
| 5.6 | Abrir directamente la ruta de una actividad ya cerrada | Texto neutro "no está disponible en este momento" |

### Bloque 6 — Hallazgos #7, #9 y fixes ya mergeados
| # | Pasos | Esperado |
|---|---|---|
| 6.1 | "Preguntas más falladas" en una materia sin presentaciones | Mensaje "…sin preguntas presentadas en actividades de **período abierto**. Las sesiones en vivo no se incluyen" |
| 6.2 | Ranking con datos | "1 presentación · 1 fallo" en singular |
| 6.3 | "Evolución temporal" con **1 dato** y con **≥ 2 estudiantes / ≥ 2 actividades** | Etiqueta del eje no truncada (o truncada por ancho + tooltip); promedio de la comisión visible como anillo |
| 6.4 | Modal de eliminación de una cuenta / revisión numerada (fixes #3 y #8 del PR #472) | Avisa el borrado permanente; la revisión empieza en 1 |

### Bloque 7 — Hallazgo #6: demora en el iPhone (requiere el dispositivo) — *no ejecutado; hallazgo desestimado por Víctor el 2026-10-15*
| # | Pasos | Esperado |
|---|---|---|
| 7.1 | Sesión en vivo con el iPhone por el proxy de dev, misma red que el iPad de la UAT v1; mostrar opciones de la 1.ª pregunta | Sin demora notable (≈ ≤ 2 s) |
| 7.2 | Apagar/encender pantalla y finalizar la sesión | Reconecta sin intervención |
| Resultado | Si anda: cerrar como puntual. Si repite: caso de "WebSocket zombi" de Safari iOS → `US-ADJ` con repro. Staging con WSS real sigue pendiente (ítem aparte) |

## 4. Entregables y cierre
- `registro-ejecuciones.md` (bitácora narrada), `registro-hallazgos.md`, `plan-de-correccion.md` (solo si hay hallazgos), todos en esta carpeta.
- Gate de cierre: `plan-de-correccion.md` aprobado por Víctor (o "sin hallazgos"). Con eso se
  habilita `BL-012` (matriz, merge `develop → main`, tag).
