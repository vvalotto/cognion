# Evidencia UAT — Iteración 1 del Incremento 3 "Actividad Evaluativa"

| Campo | Valor |
|-------|-------|
| Diseño | `quality/reports/uat/inc3/design.md` |
| Fecha ejecución | 2026-08-26 |
| Ejecutor | Sesión de Claude Code |

---

## DesignReviewer — `src/` completo

Ver `quality/reports/designreviewer/inc3-iter1-designreviewer-report.md` para el detalle. Resumen:

```
163 archivos analizados · 0 blocking issues (CRITICAL) · 114 advertencias (WARNING) · 0 infos
should_block: false
```

0 CRITICAL en todo el árbol — no bloquea. Los 11 hallazgos propios de Actividad Evaluativa son
WARNING (métodos de orquestación algo largos, serialización de eventos vía Ley de Demeter),
mismo patrón ya aceptado en `US-3.1.2`.

---

## Capa 1 — pytest

```
.venv/bin/python -m pytest tests/unit tests/integration tests/step_defs -v --tb=short
447 passed, 43 warnings in 154.79s
```

Sin regresiones. Los warnings son `PytestUnknownMarkWarning` de marcadores BDD (nombres de
tags no registrados como marks de pytest) — no indican fallo real.

---

## Capa 2 — HTTP vía `smoke.sh` extendido

`.claude/skills/run-cognion/smoke.sh` se extendió con el flujo de Actividad Evaluativa,
insertado dentro del bloque que ya arma un Estudiante real (después del flujo de cambio de
contraseña de `US-2.2.5`). Reutiliza `docente_token`/`estudiante_token`/`materia_id`/`banco_id`
ya obtenidos por el script.

Al ejecutarlo por primera vez se detectó un problema de datos: el nuevo bloque intentaba crear
una actividad con `cantidad_preguntas=3` pero en ese punto del script el banco solo tenía las 2
preguntas que el propio bloque nuevo acababa de cargar — el flujo de banco original (que carga
una 3ª pregunta de opción múltiple) corre *después*, más abajo en el script. Corregido bajando
`cantidad_preguntas` a 2, autocontenido respecto del resto del flujo.

También se extendió `cleanup()` (trap `EXIT`) para borrar del event store (`events`) los
streams `ActividadEvaluativaPeriodoAbierto`/`Evaluacion` creados por la corrida, correlacionando
por `materia_id` — verificado con una consulta directa a Postgres tras la corrida (0 filas
residuales).

Corrida completa, todos los pasos en verde:

```
== Flujo de Actividad Evaluativa, período abierto (Incremento 3, Iteración 1) ==
== POST /preguntas/verdadero-falso (banco propio de este flujo) == OK (2 preguntas activas)
== POST /actividades (docente crea una actividad de período abierto, US-3.1.2) == OK (id=d85fc615-855d-43f2-afa3-f15dcacfe768, vigente por 7 días)
== POST /evaluaciones (estudiante inicia su evaluación, US-3.1.3, RF-12) == OK (id=ea68bca3-dfbf-5197-b597-7c113b3e8bcf, 2 preguntas asignadas)
== POST /evaluaciones de nuevo (reconexión — idempotente, INV-AE-05/06) == OK (misma Evaluacion, mismo set)
== POST /evaluaciones sobre una actividad con fecha_apertura futura (esperado 422, FueraDePeriodo) == OK (422)
== POST /evaluaciones con rol docente (esperado 403, RBAC) == OK (403)
[... continúa con el resto del flujo de Identidad/Banco de Preguntas, sin cambios ...]

SMOKE TEST OK — server bajado y datos de prueba limpiados.
```

Verificación post-corrida (sin residuos):
```sql
SELECT count(*) FROM events WHERE aggregate_type IN ('ActividadEvaluativaPeriodoAbierto','Evaluacion'); -- 0
SELECT count(*) FROM materia WHERE nombre LIKE 'smoketest-%'; -- 0
```

---

## Revisión manual de Víctor — guión

Sin frontend todavía (`US-3.4.*` es Iteración 4) — no hay pantalla que recorrer en navegador.
Se armó un guión dedicado, pensado para que Víctor lo corra y juzgue los resultados a ojo (no
solo códigos HTTP):

```bash
tests/uat/inc3/guion_manual_iteracion1.sh
```

Siembra Administrador + Docente + Estudiante (vía invitación real, con fake SMTP), levanta el
backend si no hay uno corriendo, y recorre los 6 pasos del `design.md` imprimiendo cada
request/respuesta junto con qué revisar puntualmente en cada uno (ej. "los `pregunta_id` de
`preguntas_asignadas` corresponden a las preguntas cargadas", "¿el mensaje de error le queda
claro a un Estudiante?"). Al final deja el backend corriendo (si lo arrancó él) y las
credenciales/ids a mano para seguir explorando libremente en Swagger UI (`/docs`) — no limpia
nada automáticamente.

**Verificado con una corrida propia de esta sesión antes de entregarlo**: los 3 endpoints
responden como se espera (creación con 3 preguntas asignadas, idempotencia exacta en la
reconexión — mismo `id`, mismo set y orden —, 422 en `FueraDePeriodo`, 403 por rol). Datos de
esa corrida ya limpiados (`tests/uat/inc3/limpiar_uat.sh`, 0 residuos verificados).

Hallazgos de Víctor a completar en `quality/reports/uat/inc3/hallazgos-revision-manual.md`.

---

## Criterio de aceptación — resultado

- Capa 1 (pytest): ✅ en verde, sin regresiones (447/447).
- Capa 2 (HTTP vía `smoke.sh` extendido): ✅ todos los códigos HTTP esperados, sin pérdida de
  datos, cleanup verificado.
- DesignReviewer (`src/` completo): ✅ 0 CRITICAL.
- Revisión de Víctor: ✅ validada — sin hallazgos (`quality/reports/uat/inc3/hallazgos-revision-manual.md`).

**Conclusión:** el alcance backend de la Iteración 1 del Incremento 3 (crear actividad +
iniciar evaluación con set fijo idempotente) queda verificado de punta a punta por Capa 1 +
Capa 2 + DesignReviewer + revisión manual de Víctor. **UAT aprobado.**
