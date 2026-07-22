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

Cognión es un backend FastAPI (`src/app.py`) contra PostgreSQL, sin
autenticación en el gateway HTTP todavía. El frontend (`frontend/`, Vite +
React) es por ahora solo scaffold sin páginas propias — no hay UI que
recorrer hasta que se cruce el gate de diseño UX (`docs/design/ux/`), así
que este skill cubre exclusivamente el backend.

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

El driver está en `.claude/skills/run-cognion/smoke.sh`. Arranca el
backend en el puerto 8000, ejercita el flujo real de negocio vía `curl`,
verifica el caso de error, limpia los datos de prueba de Postgres y baja
el server — todo en una sola invocación, sin dejar residuos:

```bash
.claude/skills/run-cognion/smoke.sh
```

Salida esperada (todo termina en `SMOKE TEST OK`):

```
== Postgres ==
OK
== Arrancando backend (puerto 8000) ==
== GET /health ==
OK (200)
== POST /usuarios (administrador) ==
OK (id=...)
== POST /usuarios (docente) ==
OK (id=...)
== POST /comisiones ==
OK (id=...)
== POST /comisiones/{id}/docentes ==
OK (200)
== POST /usuarios con email duplicado (esperado 409) ==
OK (409)

SMOKE TEST OK — server bajado y datos de prueba limpiados.
```

Cualquier paso que falle aborta el script (`set -euo pipefail`) y muestra
el log de uvicorn. El `trap cleanup EXIT` corre siempre — aunque falle a
mitad de camino, mata el server y borra los datos de prueba (filtra por
el prefijo de email único `smoketest-$$` de esa corrida, así que no
interfiere con datos reales).

Variables de entorno opcionales: `COGNION_SMOKE_PORT` (default `8000`)
si el puerto está ocupado.

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
  única transacción implícita** — si el último `DELETE` falla por
  violación de FK, se hace rollback de los anteriores también, aunque
  cada uno haya reportado `DELETE 1`. Por eso el driver borra en el
  orden correcto de dependencias (`comision_docentes` → `comision` →
  `administrador`/`docente` → `usuario`) en un solo bloque bien ordenado,
  no en pasos que puedan fallar a mitad de camino.
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