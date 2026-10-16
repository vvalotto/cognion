# Reporte — US-8.1.5: Bootstrap del primer Administrador

**Estado:** implementada en `feature/US-8.1.1-cors-configurable` (2026-10-16). PR diferido al cierre de la Iteración 1.
**Issue:** #518 · **Spec:** `docs/specs/inc8/US-8.1.5.md`

## Punto de partida
`scripts/seed_admin.py` ya existía (`US-1.1.0`, `ADR-016`) pero no servía para un despliegue real: no está en la imagen Docker, la contraseña solo entraba por variable de entorno, los errores terminaban en traceback y la idempotencia era solo por email (con otro email crearía un segundo Administrador).

## Qué se hizo
- `AdministradorYaExiste` + `BootstrapAdministradorUseCase`: delega en `CrearUsuarioUseCase` y no hace nada si ya hay un Administrador operativo (`contar_administradores_operativos`, ya existente).
- Comando `python -m src.identidad.frameworks.cli.bootstrap_administrador` (dentro de `src/`, va en la imagen). `ejecutar()` recibe entorno, función para pedir la contraseña, repositorio y hasher, así que se prueba sin infraestructura. Exit `0` creado/ya existía, `1` entrada inválida, `2` sin contraseña ni terminal.
- Contraseña: `ADMIN_PASSWORD` o `getpass` sin eco; nunca por argumento ni impresa.
- `scripts/seed_admin.py` queda como envoltorio. Nota de actualización en `ADR-016`.
- `verificar_migraciones.sh` suma la sección 4 (bootstrap real contra la base descartable).

## Verificación
10 tests nuevos (use case y 6 escenarios del comando); suite unit 916/916. Script real contra Postgres: 6/6 OK; sin bases residuales.

## Hallazgo
Mi primera versión del script de verificación probaba la contraseña débil *después* de crear el Administrador y fallaba: con uno ya existente el comando sale en no-op (exit 0) antes de mirar la contraseña. Era un error de orden en la prueba, no del código; se reordenó (la contraseña débil se prueba sin Administradores).

## Límites
- No verificado en Fly.io (`fly ssh console`); lo cubre `US-8.4.3`.
- Si todos los Administradores quedaran inoperables, este comando no los recupera (fuera de alcance; `US-ADJ-60` lo previene).
- Decisiones propias (no pedidas): no-op ante cualquier Administrador operativo, y contraseña por terminal sin eco como alternativa a la variable de entorno.
