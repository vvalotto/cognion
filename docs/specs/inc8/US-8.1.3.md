# US-8.1.3: Validación fail-fast de settings de producción

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-8.1`
**Tipo**: `infra backend` (técnica — sin comando de negocio)
**Bounded Context**: transversal (`src/settings.py`)
**Issue**: #516

---

## Descripcion (lenguaje de negocio)

Como **responsable de operar el sistema**,
quiero **que la aplicación se niegue a arrancar en staging o producción si la configuración quedó con valores de desarrollo**,
para **no descubrir en uso real un secreto de ejemplo, una base local o un SMTP que no envía**.

---

## Contexto

`Settings` acepta cualquier valor: `SECRET_KEY=cambiar-por-un-secreto-seguro` (el de `.env.example`) firma JWT
válidos, `SMTP_HOST=localhost` pierde los emails en silencio y `FRONTEND_URL`/`CORS_ALLOWED_ORIGINS` apuntando
a `localhost` rompen links y navegador (`US-8.1.1`). Ninguna de esas fallas da error al arrancar.

## Especificacion del comportamiento

- Nuevo `Settings.entorno: Literal["desarrollo", "staging", "produccion"]`, env `ENTORNO`, default `desarrollo`.
  Un valor distinto es error de configuración.
- En `desarrollo` no se valida nada adicional (los tests y el desarrollo local siguen igual).
- En `staging` y `produccion`, al construir `Settings`, se verifica y se reportan **todas** las violaciones juntas
  en un único `ValueError`:
  1. `secret_key`: al menos 32 caracteres y distinta del valor de ejemplo.
  2. `database_url`: el host no es `localhost`/`127.0.0.1`.
  3. `smtp_host`: no es `localhost`/`127.0.0.1`; `smtp_from` no termina en `@cognion.local`.
  4. `frontend_url` y cada origen de `cors_allowed_origins`: no apuntan a `localhost`/`127.0.0.1`.
- El mensaje nombra la variable de entorno afectada y nunca incluye el valor del secreto.

## Escenarios (BDD)

1. `ENTORNO` omitido con valores de ejemplo → arranca (desarrollo).
2. `ENTORNO=produccion` con todo configurado correctamente → arranca.
3. `ENTORNO=produccion` con `SECRET_KEY` de ejemplo → falla nombrando `SECRET_KEY`.
4. `ENTORNO=produccion` con varias cosas mal → un solo error que las lista todas.
5. `ENTORNO=otro` → falla.

## Fuera de alcance

Cuenta SMTP por materia (`US-8.1.7`); migraciones (`US-8.1.4`); bootstrap del Administrador (`US-8.1.5`).

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.
