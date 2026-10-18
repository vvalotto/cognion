# Reporte — US-8.5.2: Canal de email por consola para uso sin SMTP

**Estado:** implementada en `feature/US-8.5.1-entorno-local` (2026-10-18), apilada sobre `US-8.5.1`. PR diferido al cierre de la Iteración 5 (CI lento).
**Issue:** #537 · **Spec:** `docs/specs/inc8/US-8.5.2.md`

## Qué se hizo
- `Settings.email_modo` (`EMAIL_MODO`: `smtp` por defecto, `consola`).
- `enviar_email` (`src/shared/frameworks/smtp.py`): en modo `consola` escribe destinatario, asunto y cuerpo completo (con los links de token) a INFO y retorna sin resolver cuenta ni abrir conexión. Un único punto de corte cubre invitación, recuperación de contraseña y Notificaciones, que pasan todos por esa función.
- En staging/producción `consola` se rechaza al arrancar con un error que nombra `EMAIL_MODO` (el cuerpo contiene tokens). `local` y `desarrollo` lo permiten. El chequeo vive en `_errores_email_modo()` para no subir la CC de `_validar_entorno_estricto`.
- `.env.example` documenta la variable.
- 8 tests unitarios en `tests/unit/inc8/test_us_8_5_2_email_consola.py`. El escenario 4 usa el caso de uso real de recuperación con el canal real: el link queda en el log, no se invoca `smtplib` y la respuesta es idéntica para email existente e inexistente (`INV-ID-17`).

## Decisiones
- Sin `.feature` ni integración (infra técnica, mismo precedente que `US-8.5.1`).
- `smtp.py` queda fuera de la medición de cobertura por `omit = src/*/frameworks/*` del proyecto; sus dos ramas están ejercitadas por los tests.

## Calidad
Unit inc8 68/68, `settings.py` 100 %, pylint 10.00, ruff/black/mypy limpios, MI mín. 48.15, designreviewer 0 blocking. CC máx. 14 preexistente. CodeGuard full: solo errores de tooling. Evidencia en `quality/reports/inc8/US-8.5.2-*.json`.
