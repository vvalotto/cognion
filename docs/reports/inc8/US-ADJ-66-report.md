# Reporte — US-ADJ-66: El envío de email valida el certificado del servidor SMTP

**Estado:** implementada en `feature/US-ADJ-66-validar-certificado-smtp` (2026-11-05), apilada sobre `chore/preparar-smtp-gcp`. Sin PR todavía.
**Issue:** [#586](https://github.com/vvalotto/cognion/issues/586) · **Spec:** `docs/specs/ajustes/US-ADJ-66.md` · **Origen:** revisión del envío de emails al preparar el despliegue en GCP

## Qué se hizo
- `src/shared/frameworks/smtp.py`: `_contexto_tls()` arma un contexto que verifica la cadena de certificados y el nombre del servidor con el bundle de `certifi`; `_iniciar_tls()` lo usa en `starttls(context=...)`. Si el certificado no es verificable, registra host y motivo (nunca usuario, contraseña ni cuerpo) y vuelve a lanzar `ssl.SSLCertVerificationError`: el envío falla **antes** de transmitir credenciales o mensaje.
- `pyproject.toml` y `uv.lock`: `certifi` pasa a dependencia directa.
- Sin cambios en dominio, casos de uso, `SmtpCanalEnvio`, `SmtpNotificador`, `settings` ni frontend. Sin usuario (servidor local) y `EMAIL_MODO=consola` quedan como estaban. No hay variable para desactivar la validación.

## Decisiones
- `certifi` y no el almacén del sistema: en la Mac de Víctor (Python de python.org) el almacén del sistema falló con `CERTIFICATE_VERIFY_FAILED`; `certifi` da el mismo resultado en la Mac, la imagen Docker y CI.
- `_contexto_tls()` es la costura de prueba: los tests le inyectan una autoridad propia, sin red.
- Los errores se registran y se re-lanzan; los adaptadores y casos de uso ya los propagaban.

## Hallazgo de Fase 0
`certifi` llegaba solo como dependencia transitiva de `httpx` (grupo de desarrollo) y la imagen se construye con `uv sync --no-dev`: en producción no habría estado. Se declaró dependencia directa.

## Calidad
Suite completa 2169 pasaron, 0 fallos (base descartable, ya eliminada). 8 unitarios, 3 de integración y 7 casos BDD, con un servidor SMTP de prueba con TLS y certificados generados con `cryptography` (autoridad de prueba, válido, autofirmado, otro nombre). Con el código anterior (`starttls()` sin contexto) fallan 4 de los 8 unitarios. Pylint 10,00/10, CC máx A (3), MI 76,42, `mypy` 0 errores en 315 archivos, `bandit` sin problemas, cobertura total 97,22 %. CodeGuard sin advertencias reales (timeouts y herramientas no instaladas). Evidencia: `quality/reports/inc8/US-ADJ-66-quality.json`.

## Tiempo
54 min efectivos (Fase 7: 28 min, casi todos esperando la suite completa; Fase 8: 19 min, esperando aprobación).

## Pendiente
- Commit, push y PR hacia `develop` (el PR lleva también el commit de preparación de SMTP, por la rama apilada). DesignReviewer corre en el pre-push, no en esta US.
- Verificar con `scripts/probar_smtp.py` desde la Mac que Gmail sigue enviando con la validación activa, y en la VM de GCP cuando exista (`cognion.sh email probar`).
