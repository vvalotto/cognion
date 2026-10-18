# Plan de Implementación — US-8.5.4

## Tareas
1. `scripts/local/_conexion.sh` (helper `source`, no ejecutable): lee `COGNION_LOCAL_ENV` (default `.env.local`) y deja
   usuario/clave/host/puerto/base y las funciones `admin`/`en_base`. Si falta `.env.local`, aborta con un mensaje
   que indica correr `levantar.sh` primero. Sin tocar `levantar.sh` (ya verificado).
2. `scripts/local/respaldar.sh`: `pg_dump -Fc` a `${COGNION_RESPALDOS:-~/CognionRespaldos}/cognion_local-AAAAMMDD-HHMMSS.dump`
   (carpeta 700); verifica no vacío y `pg_restore --list`; guarda `.sha256` (formato `shasum -c`); rota conservando
   los últimos `COGNION_RESPALDOS_N` (default 30) ordenando por nombre; si el dump es defectuoso lo borra y falla.
3. `scripts/local/restaurar.sh <archivo> [--sobre-local]`: valida `sha256` (si existe) y `pg_restore --list`
   (archivo corrupto → error claro, exit ≠ 0, sin tocar nada). Por defecto restaura con `--no-owner --exit-on-error`
   en una base temporal, compara conteos de `usuario`, `events`, `pregunta_plantilla` contra la base actual,
   imprime la tabla y borra la temporal (trap). Diferencia → exit 3 con explicación (puede ser actividad posterior).
   Con `--sobre-local`: pide escribir `RESTAURAR`; sin esa confirmación no hace nada. Con ella, restaura primero a la
   temporal (un dump malo nunca toca `cognion_local`), exige que no haya conexiones a la base y reemplaza por rename.
4. `tests/uat/inc8/verificar_respaldo_local.sh`: base descartable con migraciones y datos sembrados (admin vía
   bootstrap, un evento, materia→banco→pregunta); verifica los 5 escenarios + el ensayo completo; limpia todo.
5. `.gitignore`: nada nuevo (la carpeta de respaldos vive en `$HOME`, fuera del repo).

## Riesgos
- Reemplazo de la base: solo por rename tras validar; falla si hay conexiones (servidor encendido).
- `pg_restore` de un dump con roles ajenos: se usa `--no-owner`; se verificó que no hay extensiones más allá de plpgsql.
