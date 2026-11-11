# UAT del Incremento 10, Iteración 1 — Estabilidad de la v0.10.0 (`US-10.1.1`)

**Issue:** [#620](https://github.com/vvalotto/cognion/issues/620) · **Procedimiento:** `docs/plans/PROCEDIMIENTO-UAT.md`

## Objetivo
Verificar lo que `BL-015` (`v0.10.0`) dejó sin verificar, para poder llamar estable a la versión antes de la `1.0.0`.

## Estrategia
- **Entorno:** el propio de pruebas, instalado con `scripts/local/levantar.sh` (puerto 8010, base descartable `cognion_uat_v1`, archivo de entorno en `logs/uat10/`). No se tocaron `cognion`, `cognion_local` ni `cognion_uat`. Es además una prueba del camino de instalación local.
- **Capa 1 (pytest):** la suite completa de `BL-015` (2378 tests) sobre el mismo código; `src/`, `frontend/` y `migrations/` no cambiaron desde ese commit.
- **Capa 2 (HTTP):** `tests/uat/inc10/capa2_http.py` contra el servidor real; `tests/uat/inc10/carga_logins.py` para el efecto de `US-ADJ-63`.
- **Navegador real:** recorrido manual con el navegador integrado (escritorio y viewport emulado de 375 px).
- **Celular real:** lo hace Víctor, por la red local.

## Escenarios
1. Salud y readiness.
2. Link de invitación grupal: generar, duración válida e inválida, un administrador no puede, preview, varios registros con el mismo link, contador, desactivar, generar otro revoca el anterior.
3. Motivos de error del registro: email repetido, contraseña corta, contraseña sin complejidad, link desactivado; un rechazo no suma uso.
4. Aviso del último intento (1.er fallo sin aviso, 2.º con aviso, 3.º bloquea, 4.º 403).
5. El log de acceso no muestra el token de la invitación.
6. 30 logins simultáneos sin que `/health` quede bloqueado.
7. Navegador: login con aviso, tarjeta del docente, registro del estudiante (contraseña débil y válida), pantalla de link desactivado, ancho de celular.

## Criterio de aceptación
Sin hallazgos 🔴 abiertos y evidencia en `quality/reports/uat/inc10/`.
