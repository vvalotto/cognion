# /checkpoint — Checkpoint proactivo de sesión

Guarda el estado actual de la sesión y limpia el flag de resumen pendiente.
Usarlo antes de un corte largo o al terminar una tarea significativa.

## Qué hace

1. Captura el estado del repo (branch, git status, últimos commits)
2. Actualiza `~/.claude/projects/-Users-victor-PycharmProjects-cognion/memory/session-current.md`
3. Limpia el flag `session-needs-summary.flag` si existe
4. Escribe un resumen breve de lo trabajado en esta sesión

## Cuándo usarlo

- Al terminar un bloque de trabajo y hacer una pausa larga
- Antes de cerrar Claude Code si no habrá continuidad inmediata
- Después de cerrar un Incremento o US

## Instrucciones para Claude

Al ejecutar /checkpoint:
1. Si se crearon, movieron o renombraron archivos bajo `docs/` en esta sesión, correr
   `/docs-audit` primero y resolver (o al menos reportar) los huérfanos detectados antes
   de continuar
2. Escribir un resumen de 3-5 puntos de lo trabajado en la sesión actual
3. Correr `.claude/hooks/save-session.sh` para actualizar los archivos de memoria
4. Borrar `~/.claude/projects/-Users-victor-PycharmProjects-cognion/memory/session-needs-summary.flag` si existe
5. Confirmar al usuario que el checkpoint quedó guardado
