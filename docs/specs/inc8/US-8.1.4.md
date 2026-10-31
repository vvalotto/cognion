# US-8.1.4: Migraciones Alembic como paso explícito de release

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-8.1`
**Tipo**: `infra backend` (técnica — sin comando de negocio)
**Bounded Context**: transversal (`Dockerfile`, `fly.toml`, `migrations/`)
**Issue**: #517

---

## Descripcion (lenguaje de negocio)

Como **responsable de operar el sistema**,
quiero **que el esquema de la base se actualice como un paso del release, antes de que arranque la nueva versión, y no cuando arranca la app**,
para **que un deploy con una migración fallida se aborte sin tirar abajo la versión que funciona**.

---

## Contexto

- La imagen solo copia `src/`: no contiene `alembic.ini` ni `migrations/`, así que hoy **no puede migrar**.
- Ningún paso del despliegue aplica migraciones (`cd.yml` lo tiene comentado). Una instalación limpia en Fly.io
  (`ADR-021`) arrancaría con la base vacía.
- La app tampoco migra al arrancar (correcto: con varias instancias se pisarían, y el arranque debe ser rápido
  y predecible en una sesión en vivo). Esta decisión se mantiene.

## Especificacion del comportamiento

- `Dockerfile`: la imagen incluye `alembic.ini` y `migrations/`. El `CMD` sigue siendo solo `uvicorn`.
- `fly.toml` mínimo en la raíz, con `[deploy] release_command = "uv run alembic upgrade head"` y el servicio
  HTTP (puerto 8000, HTTPS forzado, healthcheck `/health`). Región, tamaño de VM y Postgres se completan en
  `US-8.2.1`/`US-8.2.2`.
- La app no ejecuta Alembic en su ciclo de vida (se verifica con un test).
- `alembic upgrade head` es **idempotente** (segunda corrida: sin cambios, exit 0) y sobre una base vacía llega a
  `head`; con la base inaccesible termina con exit ≠ 0 (el `release_command` aborta el deploy).
- Script reutilizable `tests/uat/inc8/verificar_migraciones.sh` que lo comprueba contra una base descartable
  (lo reutiliza `US-8.4.3`).

## Escenarios (BDD)

1. Base vacía → `upgrade head` crea el esquema completo y `alembic current` = `head`.
2. Segunda corrida de `upgrade head` → exit 0, sin cambios.
3. Base inaccesible → exit ≠ 0 (el deploy se aborta).
4. La imagen contiene `alembic.ini` y `migrations/`; su `CMD` no invoca Alembic.
5. `fly.toml` declara `release_command` con `alembic upgrade head`.

## Fuera de alcance

CD completo (`US-8.2.1`), `downgrade` (`US-8.3.4`), rollback (`US-8.2.3`), bootstrap del Administrador (`US-8.1.5`).

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.
