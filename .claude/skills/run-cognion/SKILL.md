---
name: run-cognion
description: >
  Levanta el backend FastAPI de Cognión contra PostgreSQL local y lo somete
  a un smoke test real (alta de usuario, comisión, asignación de docente,
  caso de error). Usar cuando se pida correr, levantar, arrancar o hacer
  un smoke test de la app Cognión, o verificar que el backend responde
  end-to-end después de un cambio.
---

Todas las rutas de este documento son relativas a la raíz del repo
(`cognion/`), no a este directorio de skill.

Cognión es un backend FastAPI (`src/app.py`) contra PostgreSQL. Desde
`US-1.1.5` los endpoints de administración (`POST /usuarios`,
`POST /comisiones`, `POST /comisiones/{id}/docentes`) y de invitaciones
(`POST /comisiones/{id}/invitaciones`) están protegidos por RBAC — el
driver hace bootstrap del primer Administrador (`ADR-016`,
`scripts/seed_admin.py`) y login para obtener JWTs antes de llamarlos.
El frontend (`frontend/`, Vite + React) tiene páginas propias desde
`US-1.1.6`+ (login, registro), pero este skill sigue cubriendo solo el
backend — no hay driver de smoke test de UI todavía.

## Prerrequisitos

- PostgreSQL local corriendo (Homebrew, no Docker):
  ```bash
  brew services start postgresql@16
  pg_isready   # -> "accepting connections"
  ```
- `.env` en la raíz con `DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/cognion`
  (ya versionado como `.env.example`; copiarlo si falta `.env`).
- Entorno virtual instalado (`uv sync` si `.venv/` no existe).

## Run (agent path) — driver de smoke test

El driver está en `.claude/skills/run-cognion/smoke.sh`. Arranca un fake
SMTP local (`.claude/skills/run-cognion/fake_smtp.py` — necesario porque
`GenerarInvitacionUseCase` manda el email de forma síncrona, `US-1.1.1`,
y no hay servidor SMTP real en este entorno de desarrollo) y el backend
en el puerto 8000, hace bootstrap del primer Administrador
(`scripts/seed_admin.py`, `ADR-016` — `POST /usuarios` está protegido por
RBAC desde `US-1.1.5`, no se puede crear el primero por HTTP), ejercita
el flujo real de negocio (alta de usuario/comisión/asignación de
docente, invitación + registro de Estudiante con token real, `US-1.1.8`)
vía `curl`, verifica los casos de error, limpia los datos de prueba de
Postgres y baja todo — todo en una sola invocación, sin dejar residuos:

```bash
.claude/skills/run-cognion/smoke.sh
```

Salida esperada (todo termina en `SMOKE TEST OK`):

```
== Postgres ==
OK
== Arrancando fake SMTP (puerto 2525) ==
OK
== Arrancando backend (puerto 8000) ==
== GET /health ==
OK (200)
== Bootstrap Administrador (scripts/seed_admin.py, ADR-016) ==
Administrador creado: ...
OK
== POST /identidad/login (administrador) ==
OK (token obtenido)
== POST /usuarios (docente) ==
OK (id=...)
== POST /comisiones ==
OK (id=...)
== POST /comisiones/{id}/docentes ==
OK (200)
== POST /identidad/login (docente) ==
OK (token obtenido)
== POST /comisiones/{id}/invitaciones (docente) ==
OK (id=...)
== POST /identidad/registro con invitación vigente (US-1.1.8) ==
OK (materia=Smoke Test)
== POST /identidad/registro con token ya usado (esperado 422) ==
OK (422)
== POST /usuarios con email duplicado (esperado 409) ==
OK (409)

SMOKE TEST OK — server bajado y datos de prueba limpiados.
```

Si `POST /comisiones/{id}/invitaciones` falla (p. ej. el fake SMTP no
arrancó), el paso se reporta como `SKIPPED` en vez de abortar todo el
smoke test — el resto de la suite (alta de usuarios/comisión/asignación)
sigue corriendo igual.

Cualquier otro paso que falle aborta el script (`set -euo pipefail`) y
muestra el log de uvicorn. El `trap cleanup EXIT` corre siempre — aunque
falle a mitad de camino, mata el server y el fake SMTP, y borra los
datos de prueba (filtra por el prefijo de email único `smoketest-$$` de
esa corrida, así que no interfiere con datos reales).

Variables de entorno opcionales: `COGNION_SMOKE_PORT` (default `8000`),
`COGNION_SMOKE_SMTP_PORT` (default `2525`) si alguno de los dos puertos
está ocupado.

## Run (human path)

```bash
.venv/bin/uvicorn src.app:app --port 8000
curl http://localhost:8000/health
# Ctrl-C para bajarlo
```

Ver todos los endpoints y sus schemas: `http://localhost:8000/openapi.json`
(o `/docs` para la UI de Swagger).

## Direct invocation (tests)

Para tocar solo la capa que te interesa (entities/use_cases) sin levantar
el server ni Postgres:

```bash
.venv/bin/pytest tests/unit/incN/  -q
```

## Gotchas

- **Las FK de `administrador`/`docente` NO tienen columna `usuario_id`** —
  su propia PK (`id`) *es* la FK a `usuario.id`. Un `DELETE ... WHERE
  usuario_id = ...` falla con `column "usuario_id" does not exist`.
  Filtrar por `id IN (SELECT id FROM usuario WHERE ...)`.
- **`psql -c` con varios statements separados por `;` corre todo en una
  única transacción implícita** — si un `DELETE` falla por violación de
  FK, se hace rollback de los anteriores también, aunque cada uno haya
  reportado `DELETE 1`. Por eso el driver borra en el orden correcto de
  dependencias en un solo bloque bien ordenado, no en pasos que puedan
  fallar a mitad de camino: `invitacion` → `estudiante` →
  `comision_docentes` → `comision` → `administrador`/`docente` →
  `usuario`. **`estudiante.comision_id` referencia `comision.id`** — si
  se borra `comision` antes que `estudiante` (como en una versión
  anterior de este driver, previa a `US-1.1.8`), el `DELETE` de
  `comision` falla y se pierde silenciosamente la limpieza de esa
  corrida entera; el síntoma es filas `smoketest-*` acumulándose entre
  corridas sin que el script reporte error (el `|| true` del cleanup
  las traga).
- **`POST /usuarios`, `POST /comisiones`, `POST /comisiones/{id}/docentes`
  y `POST /comisiones/{id}/invitaciones` requieren `Authorization: Bearer
  <jwt>` desde `US-1.1.5`** — sin token responden `401 {"detail":"No
  autenticado."}` con un body sin `id`, que rompe cualquier
  `json.load(...)['id']` corriente abajo con un `KeyError` poco obvio.
  El primer Administrador no puede loguearse sin existir — de ahí el
  bootstrap vía `scripts/seed_admin.py` (bypassa la API, usa el use case
  directo contra la DB).
- **El token de una invitación no se expone en la respuesta de
  `POST /comisiones/{id}/invitaciones`** (solo se manda por email,
  `US-1.1.1`) — para poder ejercitar `POST /identidad/registro` en un
  smoke test hay que leerlo directo de la tabla `invitacion` por su `id`.
- **`POST /usuarios` y `POST /comisiones` exigen campos que no son
  obvios por el nombre del endpoint**: `perfil` (enum
  `administrador|docente|estudiante`) en usuarios; `materia` y
  `horario` (no solo `nombre`) en comisiones. Confirmar siempre contra
  `/openapi.json` antes de armar el payload a mano.
- El log de arranque de uvicorn a veces tarda un instante en escribirse
  a disco — un `curl` inmediato después del `&` puede fallar con
  connection refused aunque el server vaya a levantar bien 1-2s después.
  El driver hace polling a `/health` en vez de asumir que ya está arriba.

## Troubleshooting

- `psql: error: connection to server ... failed` → Postgres no está
  corriendo: `brew services start postgresql@16`.
- `relation "usuarios" does not exist` → la tabla es `usuario` (singular),
  no `usuarios`. Los nombres de tabla no siguen el plural del endpoint.
- `uuid_parsing ... invalid length` en `/comisiones` → se mandó
  `administrador_id` vacío o mal formado; confirmar que el `POST
  /usuarios` previo devolvió `id` antes de usarlo.