# UAT de regresión de la `v1.0.1` — Incremento 12, Iteraciones 1 y 2 (`BL-018`)

**Procedimiento:** `docs/plans/PROCEDIMIENTO-UAT.md` · **Plan de cierre:** `docs/plans/inc12/inc12-cierre-bl018.md`

## Objetivo
Verificar que las Iteraciones 1 y 2 del Incremento 12 (calidad de diseño, sin funcionalidad nueva) dejan la `1.0.0` funcionando igual, **salvo los tres cambios de comportamiento declarados en la Iteración 1**, que se prueban como tales:

- **Cambian lo observable (Iteración 1):** el canal en vivo solo lo abre quien pertenece a la comisión (`US-12.1.1`); unirse, consultar el estado y ver el ranking de una sesión en vivo exigen pertenecer a la comisión, con 403 si no (`US-12.1.2`); el token de sesión dura 8 horas en lugar de 1 (`US-12.1.3`).
- **No deben cambiar lo observable (Iteración 2, refactors):** manejador único de errores de dominio (`ADR-029`), presentadores en los controllers (`ADR-031`), repositorios SQL en `frameworks/repositories/` (`ADR-030`), unidad de trabajo (`ADR-028`), pool de conexiones con un solo proceso (`ADR-018` enmendado, `IM-05`) y bloqueo del verificador (`IM-05`).
- **Sin efecto en el producto:** herramientas, hook de push, análisis de seguridad, respaldo e imagen (`IQ-05`, `IQ-06` y operación).

## Estrategia
- **Entorno:** servidor local instalado con `scripts/local/levantar.sh` (puerto 8010, base descartable `cognion_uat_bl018`, archivo de entorno y logs en `logs/uat12/`), con el **pool real** (no `NullPool`). No se tocaron `cognion`, `cognion_local`, `cognion_uat` ni las bases `*_test`.
- **Capa 1 (pytest):** la suite completa sobre `develop` (dos corridas, una con cobertura).
- **Capa 2 (HTTP y WebSocket):** `tests/uat/inc10/capa2_http.py` (los escenarios de la `1.0.0`), `tests/uat/inc10/carga_logins.py` (30 logins simultáneos con el pool), `tests/uat/inc12/capa2_regresion.py` (códigos de error por categoría, bloqueo de cuenta, alta/login masivo y sesión en vivo con respuestas simultáneas) y `tests/uat/inc12/capa2_autorizacion.py` (dos comisiones: miembros y ajenos frente a la sesión en vivo y su canal WebSocket, y vencimiento del token).
- **Navegador real:** recorrido manual con el navegador integrado, escritorio y viewport emulado de 375 px, sobre los circuitos de la `1.0.0`.
- **Celular real:** no se hace en este UAT (se declara como no verificado).

## Escenarios
1. Salud y readiness.
2. Errores por categoría con el manejador único: 401, 403, 404, 409 y 422, con el mismo cuerpo y código que antes.
3. Login: aviso del último intento, bloqueo al 3.er fallo, 403 con contraseña correcta estando bloqueada, reseteo por el administrador.
4. Invitación grupal y registro de N estudiantes, N logins simultáneos.
5. Sesión en vivo: crear, unirse, iniciar, mostrar opciones, N respuestas simultáneas, cerrar pregunta, ranking.
6. Autorización de la sesión en vivo (`US-12.1.1` y `US-12.1.2`): un estudiante o un docente de otra comisión recibe 403 al unirse, consultar el estado, ver el ranking o los participantes, y conducir la sesión; una sesión inexistente da 404; los miembros de la comisión siguen entrando (200). El canal WebSocket rechaza sin token, con token inválido, a ajenos y una sesión inexistente, y abre para el estudiante y el docente de la comisión.
7. Vencimiento del token (`US-12.1.3`): el valor por defecto de `Settings` es 480 minutos, y un token emitido por el servidor vence a los 480 minutos.
8. Navegador: login del docente, banco de preguntas, creación de actividad, registro del estudiante por link, sesión en vivo del estudiante (incluida la transición de vista corregida), analytics, ancho de celular.

## Criterio de aceptación
Sin hallazgos 🔴 abiertos y evidencia en `quality/reports/uat/inc12/`.
