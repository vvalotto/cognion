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

## Revisión manual de Víctor — instrucciones

Sin frontend todavía (`US-3.4.*` es Iteración 4) — no hay pantalla que recorrer en navegador.
La revisión humana de esta iteración es vía HTTP directo, con dos opciones:

**Opción A — reproducir el smoke test tal cual:**
```bash
.claude/skills/run-cognion/smoke.sh
```
Levanta y baja el server solo, siembra y limpia sus propios datos — no deja nada corriendo.

**Opción B — exploración interactiva vía Swagger UI (`/docs`):**
```bash
# Terminal 1 — levantar el backend
.venv/bin/uvicorn src.app:app --reload

# Terminal 2 — sembrar el primer Administrador (ADR-016)
ADMIN_NOMBRE="Victor" ADMIN_EMAIL="victor@fiuner.edu.ar" ADMIN_PASSWORD="TuPassword123!" \
  .venv/bin/python scripts/seed_admin.py
```
Abrir `http://localhost:8000/docs`, loguearse (`POST /identidad/login`) con ese Administrador,
pegar el `access_token` en el botón "Authorize" (arriba a la derecha), y desde ahí:
1. `POST /usuarios` — crear un Docente
2. Loguear como Docente, `POST /materias`, `POST /preguntas/verdadero-falso` (2-3 preguntas)
3. `POST /actividades` (`fecha_apertura` en el pasado, `fecha_cierre` en el futuro,
   `cantidad_preguntas` ≤ preguntas activas)
4. Crear un Estudiante (invitación + registro, o directamente en la comisión si ya existe) y
   loguear como Estudiante
5. `POST /evaluaciones` con el `actividad_id` — confirmar que devuelve un set de preguntas del
   tamaño pedido, y que repetir la misma llamada devuelve el mismo `id`/set

**Pendiente:** Víctor revisa contra este entorno cuando lo levante — no hay un server dejado
corriendo por esta sesión al momento de escribir este documento.

---

## Criterio de aceptación — resultado

- Capa 1 (pytest): ✅ en verde, sin regresiones (447/447).
- Capa 2 (HTTP vía `smoke.sh` extendido): ✅ todos los códigos HTTP esperados, sin pérdida de
  datos, cleanup verificado.
- DesignReviewer (`src/` completo): ✅ 0 CRITICAL.
- Revisión de Víctor: **pendiente** — instrucciones arriba.

**Conclusión preliminar:** el alcance backend de la Iteración 1 del Incremento 3 (crear
actividad + iniciar evaluación con set fijo idempotente) queda verificado de punta a punta por
Capa 1 + Capa 2 + DesignReviewer. Falta la confirmación humana de Víctor para cerrar
definitivamente esta verificación.
