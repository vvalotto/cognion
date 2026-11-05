# Plan de Implementación: US-ADJ-66 - El envío de email valida el certificado del servidor SMTP

**Patrón:** clean-architecture-bc · **Producto:** cognion · **BC:** transversal (`shared`) · **Capa:** `frameworks`

## Diseño
Hoy `_enviar_sync` hace `servidor.starttls()` sin contexto: cifra pero no valida cadena ni nombre. La corrección es solo de `src/shared/frameworks/smtp.py`; el dominio, los casos de uso y los dos adaptadores (`SmtpCanalEnvio`, `NotificadorSmtp`) no cambian.

```
enviar_email(materia_id, ...)
   EMAIL_MODO=consola ─────────────────────────▶ solo log, sin conexión              (igual)
   _enviar_sync(cuenta, ...)
      cuenta SIN usuario ──────────────────────▶ sin TLS, sin login                   (igual: localhost:25)
      cuenta CON usuario ── starttls(context=_contexto_tls()) ──▶ login ──▶ envío
                                  │
                                  └─ ssl.SSLCertVerificationError ─▶ logger.error(host, motivo) ─▶ re-lanza
                                     (nunca llega AUTH ni el mensaje)
```

- `_contexto_tls()` = `ssl.create_default_context(cafile=certifi.where())`: verifica la cadena **y** el nombre (`check_hostname=True`, `CERT_REQUIRED`). Una función aparte es la costura de prueba: los tests le inyectan una autoridad propia, sin red ni internet.
- El nombre que se valida es el `host` de la cuenta (la de la materia o la global), porque `smtplib` usa el host de la conexión como `server_hostname`.
- El error **se registra y se re-lanza**: los dos adaptadores y los casos de uso ya propagan la excepción; no se oculta ni se convierte en éxito.
- El log lleva host y motivo del certificado. **Nunca** usuario, contraseña ni cuerpo.
- **Sin variable para desactivar la validación.**

## Decisión a confirmar
**Almacén de certificados: `certifi`** (propuesto en la spec) en lugar del almacén del sistema (`ssl.create_default_context()` a secas): da el mismo resultado en la Mac de Víctor (Python de python.org, sin certificados del sistema, falló en la prueba real), en la imagen `python:3.12-slim` y en CI.
**Hallazgo de Fase 0:** `certifi` hoy es solo transitiva de `httpx` (grupo de desarrollo) y la imagen se arma con `uv sync --no-dev` → hay que **declararlo como dependencia directa**.

## Componentes a Implementar

### 1. Módulo compartido (`src/shared/frameworks/smtp.py`)
- [ ] `_contexto_tls() -> ssl.SSLContext` con el bundle de `certifi`.
- [ ] `_enviar_sync`: `servidor.starttls(context=_contexto_tls())` (solo en la rama con usuario).
- [ ] Capturar `ssl.SSLCertVerificationError` en `_enviar_sync`: `logger.error("No se pudo verificar el certificado del servidor SMTP %s: %s", host, error.verify_message)` y re-lanzar.

### 2. Dependencias
- [ ] `pyproject.toml`: agregar `certifi` a `dependencies`; regenerar `uv.lock` (`uv lock`).

### 3. Sin cambios
- Dominio, casos de uso, `SmtpCanalEnvio`, `NotificadorSmtp`, `settings`, `frontend/`.
- `scripts/probar_smtp.py` no necesita cambios: usa `enviar_email` y hereda la validación. Se ajusta su mensaje de error para el caso de certificado.

## Tests (Fases 4 a 6)
- **Servidor de prueba** (`tests/unit/inc8/_servidor_smtp_tls.py`): SMTP mínimo en un hilo (EHLO, STARTTLS, AUTH, MAIL/RCPT/DATA) que **registra los comandos recibidos**; certificados generados al vuelo con `cryptography` (autoridad de prueba + certificado de `localhost`, uno autofirmado y uno emitido para otro nombre). Sin internet.
- **Unitarios (`test_us_adj_66_certificado_smtp.py`):** certificado válido (inyectando la autoridad de prueba) → sale y el servidor recibió `AUTH`; autofirmado → falla y **no hubo `AUTH` ni `DATA`**; nombre distinto → falla; materia con cuenta inválida vs. cuenta global válida; sin usuario → sin `STARTTLS`; consola → sin conexión; el log indica el problema y **no contiene la contraseña ni el cuerpo**; `_contexto_tls()` tiene `verify_mode=CERT_REQUIRED` y `check_hostname=True`.
- **Regresión:** `test_us_8_1_7_smtp_por_materia.py`, `test_us_adj_64_logging.py`, `test_us_8_5_2_email_consola.py`, `test_smtp_canal_envio.py`, `test_notificador_smtp.py` sin tocar (parchean `smtplib.SMTP`, que sigue aceptando `starttls(context=...)`).
- **Integración (Fase 5):** el envío completo desde `SmtpCanalEnvio` contra el servidor de prueba con TLS, sin base de datos (no toca la DB de desarrollo).
- **BDD (Fase 6):** los 7 escenarios aprobados, en `tests/step_defs/inc8/test_us_adj_66_steps.py`.

## Documentación (Fase 8)
- `docs/plans/DESPLIEGUE-GCP.md` Paso 11b: quitar el "límite conocido" del STARTTLS sin validar.
- `ADR-023`: nota breve de la validación del certificado.
- Spec `US-ADJ-66.md`: estado → `Implementada`.

## Riesgos
- **Un servidor institucional con certificado propio no firmado por una autoridad pública** (p. ej. un relay interno de la facultad) pasaría a fallar. Es el comportamiento buscado; si aparece, la salida correcta es agregar esa autoridad al almacén, no desactivar la validación (fuera de alcance, se evaluaría como otra US).
- **Un certificado de Gmail rotado o una autoridad nueva** se resuelve actualizando `certifi` (Dependabot ya lo propone).
