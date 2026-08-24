# Evidencia UAT — Iteración 2 del Incremento 2 "Cuentas y contraseñas"

| Campo | Valor |
|-------|-------|
| Diseño | `quality/reports/uat/inc2/design-iter2.md` |
| Fecha ejecución | 2026-08-21 |
| Ejecutor | Sesión de Claude Code, con recorrido en navegador real (Chrome vía claude-in-chrome) |

---

## Capa 1 — pytest + Vitest

```
.venv/bin/pytest -q
357 passed, 41 warnings in 76.82s
```

```
cd frontend && npx vitest run
Test Files  29 passed (29)
     Tests  148 passed (148)
```

Sin regresiones. Los warnings de pytest son los mismos ya documentados en la Iteración 1
(`PytestUnknownMarkWarning` de marcadores BDD, `InsecureKeyLengthWarning` de una clave de
test) — ninguno indica un fallo real.

## Capa 2 — HTTP vía `smoke.sh` extendido

`.claude/skills/run-cognion/smoke.sh` se extendió con el flujo completo de gestión de
cuentas (`US-2.2.1` a `US-2.2.5`), reutilizando el `estudiante` que el driver ya registra vía
invitación. Corrida completa, todos los pasos en verde:

```
== Flujo de gestión de cuentas (Iteración 2, US-2.2.1 a US-2.2.5) ==
== POST /identidad/login (estudiante, password incorrecta, intento 1/3) == OK (401)
== POST /identidad/login (estudiante, password incorrecta, intento 2/3) == OK (401)
== POST /identidad/login (estudiante, password incorrecta, intento 3/3 — bloquea la cuenta) == OK (401)
== POST /identidad/login (estudiante, password CORRECTA, esperado 403) == OK (403)
== GET /usuarios?estado=bloqueada (administrador) == OK
== GET /usuarios/{id} (administrador) == OK
== POST /usuarios/{id}/resetear-password (administrador) == OK
== POST /identidad/login (estudiante, password reseteada) == OK (200)
== PUT /usuarios/me/password (estudiante) — fallo 1/3 == OK (401, intentos_restantes=2)
== PUT /usuarios/me/password (estudiante) — fallo 2/3 == OK (401, intentos_restantes=1)
== PUT /usuarios/me/password (estudiante) — fallo 3/3 (bloquea) == OK (401, bloqueada=true)
== POST /identidad/login (estudiante) — confirma bloqueo cruzado == OK (403)
== POST /usuarios/{id}/resetear-password (administrador) — segundo reseteo == OK
== PUT /usuarios/me/password (estudiante) — cambio exitoso == OK (204)

SMOKE TEST OK — server bajado y datos de prueba limpiados.
```

El resto de la corrida (Identidad + Banco de Preguntas, ya cubierto en la Iteración 1) sigue
en verde sin cambios.

## UAT en navegador real

Se levantó el backend (`uvicorn`, puerto 8000) y el frontend (`npm run dev`, puerto 5173)
persistentes contra Postgres real, se sembró un Administrador y un Docente de prueba
(`uat-inc2-iter2-*@fiuner.edu.ar`), y se recorrió el flujo completo en Chrome real (no `fetch`
mockeado) vía `claude-in-chrome`:

1. Login como Administrador — OK.
2. Listado de cuentas (`/cuentas`) — filtrar por rol "Docente" — OK, tabla se reduce a la
   cuenta esperada.
3. Ver el detalle de una cuenta — OK, muestra Email/Rol/Estado/Fecha de creación.
4. Resetear/desbloquear la contraseña de una cuenta — OK, advertencia "Esta acción también
   desbloquea la cuenta", confirmación "Se reseteó la contraseña... y la cuenta quedó
   desbloqueada."
5. Login con el Docente de prueba, fallar la contraseña 3 veces seguidas — al 4to intento
   (con la contraseña correcta) se ve la alerta **"Cuenta bloqueada — Contactá a un
   Administrador para desbloquearla"** (`US-2.2.9`), formulario completo deshabilitado
   (campos y botón "Ingresar" grises, no interactivos).
6. Como Administrador, encontrar esa cuenta bloqueada en el listado (`?estado=bloqueada`,
   columna Estado = "Bloqueada") y abrir el detalle — alerta explícita: "Esta cuenta está
   bloqueada. Se bloqueó automáticamente tras 3 intentos fallidos de inicio de sesión
   consecutivos." Resetear — OK.
7. Login exitoso con la cuenta ya desbloqueada — OK, redirige a home.
8. Cambiar la propia contraseña desde `/mi-cuenta/cambiar-password` (`US-2.2.8`) — OK,
   confirmación "Contraseña actualizada... No hizo falta volver a iniciar sesión — tu sesión
   actual sigue activa."

Sin errores en la consola del navegador. En el log del backend solo apareció el 500 esperado
de una prueba deliberada (`POST /usuarios` con `perfil: estudiante`, que el dominio rechaza a
propósito — `Usuario.crear()` no crea Estudiantes, solo `Usuario.crear_estudiante()` vía
invitación); no hay otros errores ni tracebacks.

**Nota sobre el recorrido:** lo hizo la sesión de Claude Code operando el navegador (con
ayuda de `javascript_tool` para setear los campos del formulario, dado que la extensión de
gestor de contraseñas de Chrome interceptaba los clics con autofill), no Víctor en persona.
Sirve como evidencia funcional adicional (navegador real, no mockeado) pero no reemplaza la
revisión humana de UX. Si Víctor quiere hacer su propia pasada antes de cerrar la iteración,
el entorno queda descrito arriba para levantarlo de nuevo.

---

## Criterio de aceptación — resultado

- Capa 1 (pytest + Vitest): ✅ en verde, sin regresiones (357 backend / 148 frontend).
- Capa 2 (HTTP vía `smoke.sh` extendido): ✅ todos los códigos HTTP y estados
  (`bloqueada`, `intentos_restantes`) esperados en el flujo completo de bloqueo/detección/
  reseteo/desbloqueo, sin pérdida de datos.
- UAT visual en navegador real: ✅ sin hallazgos 🔴 Bloqueantes — recorrido automatizado por
  la sesión, confirmación humana de Víctor pendiente si la quiere agregar.

**Conclusión:** la Iteración 2 del Incremento 2 (Cuentas y contraseñas, `US-2.2.1` a
`US-2.2.9`) queda verificada de punta a punta. Cierra completa la segunda mitad del Hito del
Incremento 2 — el administrador resuelve problemas de cuentas sin depender del docente, y
cualquier usuario refleja correctamente el estado de bloqueo en login. No se registraron
no conformidades nuevas en este recorrido.

**Pendiente para cerrar el Incremento 2 / `BL-003`:** la iteración de ajuste conjunta
(`US-ADJ-01`/`US-ADJ-03`, ver `CLAUDE.md` — decisión de secuencia), todavía no implementada.
