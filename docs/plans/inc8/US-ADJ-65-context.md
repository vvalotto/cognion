# Contexto de Ejecución — US-ADJ-65

## Fuentes
- **Fuente HU:** `docs/specs/ajustes/US-ADJ-65.md`, Issue [#571](https://github.com/vvalotto/cognion/issues/571)
- **Origen:** UAT `US-8.7.2`, hallazgo #3 (`quality/reports/uat/inc8/registro-hallazgos.md`)
- **Código existente:** `src/identidad/frameworks/cli/bootstrap_administrador.py` (`US-8.1.5`), `BootstrapAdministradorUseCase`, `scripts/local/levantar.sh` (lo invoca)

## Historia de Usuario
- **ID:** US-ADJ-65 — El comando que crea el Administrador pide la contraseña dos veces
- **Tipo:** mejora de usabilidad de un comando operativo (`src/identidad/frameworks/cli/`); sin cambios en dominio ni casos de uso
- **Puntos:** 3 · **Patrón activo:** `clean-architecture-bc`

## Decisiones de Ejecución
- **La confirmación vive en el comando** (`frameworks/cli`), no en el caso de uso: el dominio no sabe de terminales.
- **Costura de prueba:** una función `pedir_password_confirmada(leer, avisar)` recibe cómo leer y cómo avisar; la terminal real le pasa `getpass.getpass` y `print`, los tests, entradas guiadas. Tras 3 desencuentros levanta `ContrasenasNoCoinciden`, y `ejecutar` la convierte en código `1` sin crear nada.
- **Escenario 7 (ya existe un Administrador):** `ejecutar` consulta `repositorio.contar_administradores_operativos()` **antes** de pedir la contraseña y termina con `0`; el caso de uso mantiene su propia comprobación (defensa ante una carrera).
- **`ADMIN_PASSWORD`** y **sin terminal** no cambian (no se pide nada / código `2`).
- **Verificación con una terminal de verdad:** además de los tests con entradas guiadas, un test de integración corre el comando bajo un pseudoterminal (`pty` de la biblioteca estándar) contra una base descartable, porque el error se produjo justamente con `getpass` real.
- **Fases:** todas, con BDD. Integración y BDD solo contra una base descartable inline.

## Rutas
- Plan: docs/plans/inc8/US-ADJ-65-plan.md · Reporte: docs/reports/inc8/US-ADJ-65-report.md · Quality: quality/reports/inc8/US-ADJ-65-quality.json
- Feature: tests/features/inc8/US-ADJ-65-bootstrap-confirmacion.feature
- Branch: `feature/US-ADJ-65-bootstrap-confirmacion`, apilada sobre `feature/US-ADJ-64-logging-local`; PR único al final de la Iteración 8.
