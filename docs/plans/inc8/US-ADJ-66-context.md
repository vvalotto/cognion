# Contexto de Ejecución — US-ADJ-66

## Fuentes
- **Fuente HU:** `docs/specs/ajustes/US-ADJ-66.md`, Issue [#586](https://github.com/vvalotto/cognion/issues/586)
- **Origen:** revisión del envío de emails al preparar el despliegue en GCP (2026-11-05)
- **Código existente:** `src/shared/frameworks/smtp.py` (`US-8.1.7`, `_enviar_sync`), consumido por `src/notificaciones/frameworks/adapters/smtp_canal_envio.py` y `src/identidad/frameworks/smtp/notificador_smtp.py`; `ADR-023`

## Historia de Usuario
- **ID:** US-ADJ-66 — El envío de email valida el certificado del servidor SMTP
- **Tipo:** mejora de seguridad, infraestructura compartida (`shared/frameworks`); sin cambios en dominio ni casos de uso
- **Puntos:** 3 · **Patrón activo:** `clean-architecture-bc`

## Decisiones de Ejecución
- **Contexto TLS con `certifi`** (`ssl.create_default_context(cafile=certifi.where())`) para que Mac, imagen Docker y CI den el mismo resultado. Propuesto en la spec; **a confirmar con Víctor en la Fase 2**.
- **Hallazgo de Fase 0:** `certifi` hoy solo llega como dependencia transitiva de `httpx` (grupo de desarrollo) y la imagen se arma con `uv sync --no-dev`. Debe declararse como **dependencia directa** en `pyproject.toml` (y regenerar `uv.lock`), o producción no lo tendría.
- **Solo cambia el caso con usuario** (el único que hace STARTTLS). Sin usuario (`localhost:25`) y `EMAIL_MODO=consola` no cambian.
- **Sin interruptor para desactivar la validación.**
- **Pruebas sin internet:** servidor SMTP de prueba con TLS y certificados generados en el test (válido contra una autoridad de prueba inyectada, autofirmado, nombre distinto).
- **Tests existentes** que parchean `src.shared.frameworks.smtp.smtplib.SMTP` (`US-8.1.7`, `US-ADJ-64`) deben seguir pasando.
- **Fases:** todas, con BDD. Integración y BDD solo contra base descartable inline (regla del proyecto).

## Rutas
- Plan: docs/plans/inc8/US-ADJ-66-plan.md · Reporte: docs/reports/inc8/US-ADJ-66-report.md · Quality: quality/reports/inc8/US-ADJ-66-quality.json
- Feature: tests/features/inc8/US-ADJ-66-certificado-smtp.feature
- Branch: `feature/US-ADJ-66-validar-certificado-smtp`, apilada sobre `chore/preparar-smtp-gcp`.
