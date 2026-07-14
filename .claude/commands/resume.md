# /resume — Restaurar contexto de sesión anterior

Restaura el contexto de la sesión anterior al iniciar una nueva sesión.
Siempre ejecutar al empezar si el hook de inicio avisó que hay una sesión sin resumir.

## Qué hace

1. Lee `~/.claude/projects/-Users-victor-PycharmProjects-cognion/memory/session-current.md`
2. Lee `CLAUDE.md` para el estado operativo actual del proyecto
3. Corre `git log --oneline -10` y `git status` para ver el estado real del repo
4. Presenta un resumen de contexto al usuario
5. Limpia el flag `session-needs-summary.flag`

## Instrucciones para Claude

Al ejecutar /resume:
1. Leer `~/.claude/projects/-Users-victor-PycharmProjects-cognion/memory/session-current.md`
2. Leer `CLAUDE.md` (estado operativo)
3. Correr `git log --oneline -10` y `git status`
4. Si hay una baseline abierta en `.cm/baselines/`, leerla
5. Si hay trackers activos, verificar con `.venv/bin/python .claude/tracking/tracker_cli.py status`
6. Presentar resumen conciso: branch activo, último trabajo, próximo paso
7. Borrar `~/.claude/projects/-Users-victor-PycharmProjects-cognion/memory/session-needs-summary.flag`
