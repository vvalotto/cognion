# Plan de Implementación — US-8.1.7

| # | Tarea | Archivo |
|---|-------|---------|
| 1 | `CuentaSmtpMateria` + `smtp_cuentas_por_materia: dict[UUID, ...]`; validación estricta por cuenta en staging/produccion | `src/settings.py` |
| 2 | `CuentaSmtp`, `resolver_cuenta_smtp`, `enviar_email` (reemplaza el SMTP duplicado) | `src/shared/frameworks/smtp.py` |
| 3 | `materia_id` opcional en `CanalEnvioPort.enviar` y `NotificadorPort.enviar_invitacion` | `entities/ports/*` |
| 4 | Adapters usan el módulo compartido | `smtp_canal_envio.py`, `notificador_smtp.py` |
| 5 | Use cases pasan `materia_id` (apertura, cierre, invitación) | `notificar_*.py`, `generar_invitacion.py` |
| 6 | Actualizar fakes de tests (`enviar`, `enviar_invitacion`) | `tests/unit/inc1/_fakes.py`, `tests/unit/inc5/*` |
| 7 | Tests nuevos (resolver, settings, SMTP stub real por materia) | `tests/unit/inc8/test_us_8_1_7_*.py` |
| 8 | Regresión de integración (invitaciones, recuperación, notificaciones) contra base descartable | evidencia en el reporte |
| 9 | `.env.example` y nota en `ADR-023` | docs |

Sin frontend. Base de desarrollo intacta.
