# Plan de Implementación — US-8.5.2

## Tareas
1. `src/settings.py`: `email_modo: Literal["smtp", "consola"] = "smtp"`. En el validador de staging/producción,
   `email_modo == "consola"` agrega el error `EMAIL_MODO no puede ser 'consola'...` (nombra `EMAIL_MODO`).
   `local` y `desarrollo` lo permiten. Para no subir la CC (ya 14), el chequeo va en un helper
   `_errores_email_modo()`.
2. `src/shared/frameworks/smtp.py`: en `enviar_email`, si `settings.email_modo == "consola"` escribe a INFO
   destinatario, asunto y cuerpo completo y retorna sin resolver cuenta ni abrir hilo/conexión.
3. `.env.example`: documentar `EMAIL_MODO`.
4. Tests `tests/unit/inc8/test_us_8_5_2_email_consola.py`: escenarios 1-3 y 4 (solicitar recuperación en
   modo consola: el link queda en el log, respuesta idéntica a la de siempre).

## Riesgos
- Leer `settings.email_modo` en cada llamada (no en la importación), como `resolver_cuenta_smtp`.
- El log contiene tokens: por eso se prohíbe en staging/producción.
