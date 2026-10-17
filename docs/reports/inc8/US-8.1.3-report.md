# Reporte — US-8.1.3: Validación fail-fast de settings de producción

**Estado:** implementada en `feature/US-8.1.1-cors-configurable` (2026-10-16). PR diferido al cierre de la Iteración 1.
**Issue:** #516 · **Spec:** `docs/specs/inc8/US-8.1.3.md`

## Qué se hizo
- `Settings.entorno` (`ENTORNO`: `desarrollo` por defecto, `staging`, `produccion`).
- En staging/producción, un `model_validator` rechaza al construir `Settings`: `SECRET_KEY` < 32 caracteres o igual al ejemplo; `DATABASE_URL`, `SMTP_HOST`, `FRONTEND_URL` o cualquier origen CORS apuntando a localhost; `SMTP_FROM` con `@cognion.local`. Todas las violaciones salen juntas en un único error.
- `hide_input_in_errors=True` en `Settings`.
- `.env.example` documenta `ENTORNO` y las reglas.

## Hallazgo durante la implementación
La primera versión **filtraba el final del `SECRET_KEY`** en el mensaje de error: pydantic imprime `input_value={...}` truncado y el secreto quedó visible al final. Mi test inicial no lo detectó (otro orden de campos truncaba distinto). Se corrigió con `hide_input_in_errors=True` y un test que reproduce el caso real. Nota: `ValidationError.errors()` (API programática) sigue devolviendo el input; solo el texto impreso al arrancar es seguro.

## Decisiones
- Sin `.feature` (infra técnica, mismo precedente que US-8.1.1/8.1.2).
- No se valida la cuenta SMTP por materia (`US-8.1.7`) ni credenciales SMTP obligatorias: el servidor institucional puede no requerir usuario.

## Calidad
pylint 10.00, ruff/mypy 0 errores, CC prom. 5.2, MI 53.96, cobertura de `settings.py` 100 %, suite unit 901/901. CodeGuard full: 4 errores, todos de tooling.
