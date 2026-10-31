# US-8.5.5: Verificación de la imagen Docker en CI

**Estado**: `Desestimada` (decisión de Víctor, 2026-10-18; no se implementa en este incremento)
**Iteracion / Sprint**: `INC-8.5`
**Tipo**: `infra CI` (GitHub Actions, sin código de producción)
**Bounded Context**: transversal (`.github/workflows/ci.yml`, `Dockerfile`)
**Issue**: #540

---

## Descripcion (lenguaje de negocio)

Como **responsable de operar el sistema**,
quiero **que cada PR construya la imagen Docker y la haga arrancar contra una base de datos, sin instalar Docker en mi máquina**,
para **enterarme de que el `Dockerfile` está roto cuando se rompe, y no el día del despliegue**.

---

## Contexto

La imagen nunca se construyó ni se ejecutó localmente (no hay Docker en la máquina de Víctor y por falta de espacio
se decidió **no instalar Docker Desktop por ahora**). Hoy solo `cd.yml` hace `docker build`, y únicamente al mergear a
`main` o a un tag: un error en el `Dockerfile` se descubriría tarde. Lo probado hasta ahora es el servidor **sin**
contenedor (`US-8.1.6`).

Riesgo a verificar (hipótesis, no confirmada): el `CMD` y el `release_command` de `fly.toml` usan `uv run`, que por
defecto puede intentar sincronizar el grupo de desarrollo (incluye una dependencia desde Git) al arrancar el
contenedor, que fue instalado con `uv sync --frozen --no-dev`. Si ocurre, falla o tarda sin red. Esta US lo confirma o
lo descarta, y se corrige en el `Dockerfile` si hace falta.

## Especificacion del comportamiento

Nuevo job `Imagen Docker` en `ci.yml` (corre en cada PR a `develop`), reutilizando el servicio Postgres 16 que ya usa
el job de tests:

1. `docker build` de la imagen, sin publicarla.
2. Comprueba que la imagen contiene `alembic.ini`, `migrations/` y `frontend/dist/index.html`.
3. Aplica las migraciones **con la propia imagen** (el mismo comando que el `release_command` de `fly.toml`,
   `US-8.1.4`) contra la base del servicio.
4. Ejecuta el bootstrap del primer Administrador dentro de la imagen (`US-8.1.5`) con una contraseña de prueba.
5. Arranca el contenedor con el `CMD` real y espera a que `/api/health` responda.
6. Verifica con `curl`: `/api/health` ok, `/` y una ruta del SPA devuelven el `index.html`, `/api/materias` sin token
   responde 401, y el login del Administrador creado devuelve un token.
7. Siempre muestra los logs del contenedor si algún paso falla.

Configuración de la prueba por variables del job (sin secretos reales): `ENTORNO=local` (depende de `US-8.5.1`),
`EMAIL_MODO=consola` (`US-8.5.2`), `SECRET_KEY` generada en el job.

## Escenarios (BDD)

1. Un `Dockerfile` válido → el job pasa de punta a punta.
2. Un `Dockerfile` al que le falte copiar `migrations/` → el job falla en el paso 2 o 3, con mensaje claro.
3. Si `uv run` intenta instalar dependencias al arrancar → el job falla en el paso 3 o 5 y el `Dockerfile` se ajusta
   (por ejemplo con `uv run --no-sync` o ejecutando el entorno ya instalado).
4. El job no requiere ningún secreto del repositorio.

## Fuera de alcance

Publicar la imagen en un registro; desplegar; Docker Compose para uso local diario (queda como mejora si más adelante
se libera espacio; Colima u OrbStack serían las alternativas livianas a evaluar entonces).

## Fuente de verdad UX

No aplica.
