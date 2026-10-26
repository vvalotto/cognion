# Reporte — US-ADJ-65: El comando que crea el Administrador pide la contraseña dos veces

**Estado:** implementada en `feature/US-ADJ-65-bootstrap-confirmacion` (2026-10-26), apilada sobre `feature/US-ADJ-64-logging-local`. PR único al final de la Iteración 8.
**Issue:** [#571](https://github.com/vvalotto/cognion/issues/571) · **Spec:** `docs/specs/ajustes/US-ADJ-65.md` · **Origen:** hallazgo #3 de la UAT de `v0.9.0`

## Qué se hizo
- `src/identidad/frameworks/cli/bootstrap_administrador.py`: `pedir_password_confirmada(leer, avisar)` pide la contraseña y su repetición, hasta 3 intentos, avisando cuántos quedan; al tercer desencuentro levanta `ContrasenasNoCoinciden` y el comando termina con código `1` sin crear nada. `pedir_password_por_terminal()` la usa con `getpass` y `print`.
- `ejecutar` consulta `contar_administradores_operativos()` **antes** de pedir la contraseña (si ya hay uno: mensaje y código `0`) y delega el alta en `_crear`, lo que baja su complejidad de 11 a 8.
- Sin cambios en dominio, casos de uso, repositorios, `levantar.sh` ni frontend. `ADMIN_PASSWORD` y "sin terminal" quedan como estaban.

## Decisiones
- La confirmación vive en el comando, no en el caso de uso: el dominio no sabe de terminales.
- Los avisos no revelan la contraseña ni nada derivado de ella.
- Se probó con una terminal real (`pty.fork()`, biblioteca estándar) además de las entradas guiadas, porque el error original ocurrió con `getpass` verdadero.

## Hallazgo al probar
El helper de la terminal simulada confundía dos pedidos iguales seguidos: tecleaba antes de tiempo y el eco dejaba ver la contraseña en la salida. Era un defecto del test; ahora espera cada texto después de lo ya consumido, y los tests comprueban que la contraseña no aparece en la salida.

## Calidad
Suite completa 2151 pasaron, 0 fallos (base descartable). 10 tests unitarios nuevos, 4 de integración bajo terminal real y 7 casos BDD. Con el comando anterior fallan los 4 de terminal real. Pylint 10,00/10, `mypy` y `ruff` limpios, CodeGuard sin advertencias reales, DesignReviewer 0 bloqueantes. Evidencia: `quality/reports/inc8/US-ADJ-65-quality.json`.

## Pendiente
- Eliminar la base descartable `cognion_test_adj65` al cerrar la iteración.
- Verificar en una instalación limpia con `levantar.sh` que la contraseña se pide dos veces (parte de repetir la UAT, paso 5).
