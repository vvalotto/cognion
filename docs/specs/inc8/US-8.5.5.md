# US-8.5.5: Docker Compose local (app + Postgres) y verificación de la imagen

**Estado**: `Especificada` — **opcional, no bloquea la prueba con alumnos**
**Iteracion / Sprint**: `INC-8.5`
**Tipo**: `infra` (Docker Compose)
**Bounded Context**: transversal (`docker-compose.yml`, `Dockerfile`)
**Issue**: #540

---

## Descripcion (lenguaje de negocio)

Como **responsable de operar el sistema**,
quiero **levantar la aplicación y su base en contenedores en mi máquina**,
para **verificar por fin que la imagen Docker construye y funciona, antes de llevarla a cualquier nube**.

---

## Contexto

La imagen nunca se construyó localmente (no hay Docker instalado, `CLAUDE.md` §Ítems abiertos): lo único probado hasta
hoy es el servidor sin contenedor (`US-8.1.6`). Esta US es la primera verificación real del `Dockerfile`. **Requiere
instalar Docker** (Docker Desktop, Colima u OrbStack) — decisión de Víctor. Si no se instala, la US queda abierta y el
resto de la iteración no se bloquea.

## Especificacion del comportamiento

- `docker-compose.yml` con tres servicios: `db` (Postgres de la misma versión mayor que la local, volumen persistente y
  healthcheck), `migrar` (un solo uso: `alembic upgrade head`, el mismo paso de release que `fly.toml`, `US-8.1.4`) y
  `app` (la imagen del `Dockerfile`, que espera a que `migrar` termine bien).
- Configuración por `.env.compose` (fuera de git; se documenta una plantilla `.env.compose.example`), con
  `ENTORNO=local` y `EMAIL_MODO=consola`.
- Bootstrap del primer Administrador: `docker compose run --rm app python -m src.identidad.frameworks.cli.bootstrap_administrador`.
- `app` publica el puerto 8000 en todas las interfaces para la red local.

## Escenarios (BDD)

1. `docker build` termina sin errores y la imagen incluye `alembic.ini`, `migrations/` y `frontend/dist`.
2. `docker compose up` desde cero: la base se crea, `migrar` aplica las migraciones y `app` responde `/api/health`.
3. La interfaz carga en `http://localhost:8000/` y el login del Administrador creado funciona.
4. Reiniciar los contenedores conserva los datos (volumen).
5. Si `migrar` falla, `app` no arranca.

## Fuera de alcance

Publicar la imagen en un registro; despliegue en nube.

## Fuente de verdad UX

No aplica.
