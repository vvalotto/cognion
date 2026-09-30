# /checkpoint — Checkpoint proactivo de sesión

Guarda el estado actual de la sesión, sincroniza la memoria de estado del proyecto y limpia
el flag de resumen pendiente. Usarlo antes de un corte largo o al terminar una tarea
significativa.

## Qué hace

1. Captura el estado del repo (branch, git status, últimos commits) — bookkeeping mecánico,
   siempre correcto por diseño.
2. Actualiza `~/.claude/projects/-Users-victor-PycharmProjects-cognion/memory/session-current.md`.
3. **Sincroniza `project_estado.md`** (memoria de tipo "project") contra lo que realmente
   pasó en el repo desde su último "Última actualización" — no solo contra lo que se
   conversó en la sesión actual. Este paso es el que faltaba antes: `session-current.md` es
   un volcado automático de git, pero la narrativa de qué US/iteración está cerrada vivía
   solo en la cabeza de la sesión y se perdía si nadie la reescribía antes de cortar.
4. Limpia el flag `session-needs-summary.flag` si existe.
5. Escribe un resumen breve de lo trabajado en esta sesión.

## Cuándo usarlo

- Al terminar un bloque de trabajo y hacer una pausa larga
- Antes de cerrar Claude Code si no habrá continuidad inmediata
- Después de cerrar un Incremento, Iteración o US

## Instrucciones para Claude

Al ejecutar /checkpoint:
1. Si se crearon, movieron o renombraron archivos bajo `docs/` en esta sesión, correr
   `/docs-audit` primero y resolver (o al menos reportar) los huérfanos detectados antes
   de continuar.
2. **Sincronizar `project_estado.md` contra el repo real, no solo contra la sesión:**
   a. Leer `~/.claude/projects/-Users-victor-PycharmProjects-cognion/memory/project_estado.md`
      y extraer su fecha de "Última actualización" y el último commit/PR que menciona.
   b. Correr `git log --oneline --merges -30` (y `git log --oneline -15` si hace falta más
      detalle) para ver qué se mergeó a `develop`/`main` desde esa fecha/commit — incluyendo
      lo mergeado en sesiones anteriores a la actual, no solo lo que hizo esta sesión.
   c. Si hay merges posteriores a la última actualización que la memoria no menciona
      (US/iteraciones cerradas, PRs mergeados, baselines, cambios de branch activo): revisar
      los reportes relevantes (`docs/reports/`, `docs/plans/incN*/incN*-candidatas.md`) lo
      necesario para entender qué se cerró, y reescribir `project_estado.md` reflejando el
      estado real — mismo nivel de detalle que ya tiene el archivo, sin inflar con paja.
   d. Si la memoria ya está al día con el repo, no tocar el archivo (evitar reescrituras
      sin cambio real).
   e. Actualizar el campo `modified` del frontmatter y la línea "Última actualización" al
      hacer el rewrite.
3. Escribir un resumen de 3-5 puntos de lo trabajado en esta sesión.
4. Correr `.claude/hooks/save-session.sh` para actualizar `session-current.md`/
   `session-history.md`/`session-metadata.json`.
5. Borrar `~/.claude/projects/-Users-victor-PycharmProjects-cognion/memory/session-needs-summary.flag` si existe.
6. Confirmar al usuario que el checkpoint quedó guardado — si el paso 2 encontró y corrigió
   un desajuste, decirlo explícitamente (qué estaba desactualizado y qué se corrigió).
