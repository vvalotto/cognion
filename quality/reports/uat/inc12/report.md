# Reporte UAT — regresión de la `v1.0.1`, Incremento 12 Iteraciones 1 y 2 (`BL-018`, 2026-11-28)

**Versión probada:** `develop` en `5163faf` (la `1.0.0` más las Iteraciones 1 y 2 del Incremento 12; sin funcionalidad nueva, pero con **tres cambios de comportamiento declarados** en la Iteración 1: autorización por comisión del canal y de la sesión en vivo, y token de 8 horas).
**Resultado:** ✅ **Sin hallazgos 🔴.** 1 observación 🟡 sobre la configuración de esta máquina (no del producto). La prueba en un celular real **no se hizo** y queda como no verificada.

## Resultados

| Verificación | Resultado | Evidencia |
|---|---|---|
| Capa 1: suite completa, dos corridas independientes (una con cobertura) | ✅ 2831 pasan y 1 omitido, en ambas; cobertura 96.72 % | consola; `coverage.json` |
| Capa 2 HTTP de la `1.0.0` (`tests/uat/inc10/capa2_http.py`): salud, readiness, link grupal, errores del registro, revocación, aviso del último intento, log sin token | ✅ 27/27 | `capa2-http.json` |
| Capa 2 de regresión (`tests/uat/inc12/capa2_regresion.py`): 401/403/404/409/422 con el manejador único, aviso y bloqueo del login, reseteo por el administrador, 60 registros simultáneos, sesión en vivo con 60 estudiantes y 60 respuestas casi simultáneas, ranking de 60 | ✅ 21/21 | `capa2-regresion.json` |
| Capa 2 de autorización (`tests/uat/inc12/capa2_autorizacion.py`, `US-12.1.1` y `US-12.1.2`): con dos comisiones, un estudiante y un docente **de otra comisión** reciben 403 al unirse, consultar el estado, ver el ranking o los participantes y conducir la sesión; sesión inexistente 404; los miembros entran (200); el canal WebSocket rechaza sin token, con token inválido, a ajenos y sesión inexistente (el handshake se rechaza con HTTP 403) y abre para los miembros | ✅ 22/22 | `capa2-autorizacion.json` |
| Vencimiento del token (`US-12.1.3`): `Settings` sin `.env` da 480 min por defecto; un token emitido por el servidor vence a los 480 min | ✅ (con `ACCESS_TOKEN_EXPIRE_MINUTES=480` en el servidor de UAT, ver la observación 🟡) | `capa2-autorizacion.json` |
| 30 logins simultáneos con el **pool real** de conexiones | ✅ 30 logins en 1,51 s (`BL-016`, sin pool: 2,90 s); login mediana 898 ms (antes 1739 ms); `/health` durante la ráfaga: mediana 8 ms, máx 107 ms | `carga-logins.txt` |
| Log del servidor durante toda la prueba | ✅ 0 respuestas 5xx y 0 trazas en 771 líneas | `logs/uat12/` (no versionado) |
| Navegador (escritorio): login del docente, inicio, Banco, Actividades, Reportes | ✅ sin errores de consola; todas las llamadas 200 | recorrido manual |
| Navegador (escritorio): Reportes → Desempeño por comisión (presentadores de Analytics) con 60 estudiantes | ✅ | recorrido manual |
| Navegador (escritorio): Banco → editar una pregunta y guardar (`PUT` 200, el listado muestra el texto nuevo) | ✅ | recorrido manual |
| Navegador a 375 px (emulado): login del estudiante, inicio, Mis actividades | ✅ sin desbordes | recorrido manual |
| Navegador a 375 px: sesión en vivo del estudiante completa (sala de espera → pregunta → respuesta correcta 2922 pts → espera → "¡Terminó la sesión!" con ranking), cambiando de vista sola | ✅ 43 llamadas, todas 200; sin errores de consola | recorrido manual |
| Navegador a 375 px: pantalla de registro con link (resuelve "Materia — horario", medidor de contraseña "Débil") | ✅ | recorrido manual |

## Observaciones sobre la propia prueba

- La primera corrida de `capa2_regresion.py` dio 18/20. Los dos fallos eran **expectativas equivocadas del script**, no del sistema: el aviso `intentos_restantes = 1` llega en el 2.º fallo (no en el 1.º, `US-ADJ-69`) y el código `cuenta_bloqueada_temporal` es solo para el último Administrador (un docente bloqueado recibe un 403 de texto). Se corrigió el script y la segunda corrida dio 21/21. `capa2_http.py` ya confirmaba el comportamiento correcto antes del cambio.
- Hubo que recrear el servidor de PostgreSQL por un `postmaster.pid` obsoleto tras la pausa de la sesión; no tiene relación con el producto.

## Hallazgos

| # | Sev. | Descripción | Track |
|---|---|---|---|
| H-1 | 🟡 | El `.env` de desarrollo de esta máquina (raíz del repo, no versionado) todavía tiene `ACCESS_TOKEN_EXPIRE_MINUTES=60`, copiado del `.env.example` anterior. `pydantic-settings` lo lee del directorio actual y **pisa el nuevo valor por defecto de 480**: el primer servidor de UAT, que arrancó con ese `.env`, emitió tokens de 60 minutos. No es un defecto del producto (el valor por defecto es 480 y `.env.example` ya dice 480; las instalaciones hechas con `preparar-env.sh` no fijan el valor). Alcanza a **cualquiera que actualice con un `.env` viejo**. | Documentarlo en el `CHANGELOG` de la `1.0.1` (quien tenga el valor fijado lo conserva). El `.env` de Víctor no se toca: es suyo. |

## No verificado

- **Celular real:** el registro y la sesión en vivo del estudiante se probaron con un viewport emulado de 375 px, no con un teléfono.
- **Servidor con dominio, certificado y firewall, y medición del pool allí** (Issue #624): la carga se midió en la Mac, con el pool real pero sin la red ni el hardware del servidor.
- **Falla intermitente de una corrida parcial de integración** (inc3/inc5/inc6, una sola vez, bajo carga): no se identificó la causa. No volvió a aparecer en las dos corridas completas ni en la corrida de BL-018.
- **Secuencias de runtime** de `docs/architecture/30-runtime-interactions.md`: no se ejecutaron.
- **Alta de estudiante desde la pantalla de registro con el botón:** el navegador mostró la pantalla y el medidor; el alta se cubrió por HTTP (60 registros, 201), no enviando el formulario a mano.
- **Camino de Docker real en el servidor** (`deploy/servidor/`): sin cambios respecto de `BL-016`.

## Conclusión

Las Iteraciones 1 y 2 del Incremento 12 dejan la `1.0.0` funcionando igual en lo que no se quiso cambiar (mismos códigos y cuerpos de error, mismas pantallas y circuitos, con mejor tiempo de respuesta bajo carga gracias al pool) y cambian solo lo declarado: la sesión en vivo y su canal quedan restringidos a la comisión y el token dura 8 horas. Sin hallazgos bloqueantes para publicar la `v1.0.1`.
