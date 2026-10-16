# US-8.1.1: CORS configurable por entorno

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-8.1`
**Tipo**: `infra backend` (técnica — sin comando de negocio)
**Bounded Context**: transversal (`src/app.py`, `src/settings.py`)
**Issue**: #514

---

## Descripcion (lenguaje de negocio)

Como **responsable de operar el sistema**,
quiero **definir por variable de entorno qué orígenes pueden llamar a la API**,
para **desplegar en staging y producción (`ADR-021`, `ADR-024`) sin recompilar ni tocar código**.

---

## Contexto

`src/app.py` fija `allow_origins=["http://localhost:5173"]`. En Fly.io el origen del frontend es
otro, y un navegador real rechaza toda llamada (bug ya visto en `US-1.1.9`). `settings.py` ya
tiene `frontend_url` (usado para links de email) pero no gobierna CORS.

## Especificacion del comportamiento

- `Settings.cors_allowed_origins: str`, lista de orígenes separados por coma. Default
  `http://localhost:5173` (el desarrollo local sigue funcionando sin configurar nada).
- Propiedad `cors_origins_list` → `list[str]`: separa por coma, recorta espacios, descarta vacíos.
- `src/app.py` usa `settings.cors_origins_list` en `CORSMiddleware`.
- Un origen `*` no se admite junto con `allow_credentials=True`: si aparece, la configuración
  es inválida y la app falla al arrancar con un mensaje claro (el resto de la validación
  fail-fast de producción es `US-8.1.3`).

## Escenarios (BDD)

1. Sin variable definida → solo `http://localhost:5173` recibe `Access-Control-Allow-Origin`.
2. `CORS_ALLOWED_ORIGINS="https://a.fly.dev, https://b.fly.dev"` → ambos orígenes reciben el
   header; un tercero no.
3. Origen no listado → la respuesta no incluye `Access-Control-Allow-Origin`.
4. `CORS_ALLOWED_ORIGINS="*"` → error de configuración al construir la app.

## Fuera de alcance

Validación del resto de settings de producción (`US-8.1.3`); URL base del frontend (`US-8.1.2`).

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.
