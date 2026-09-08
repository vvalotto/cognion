# Datos reales para la prueba manual E2E

Siembra la base de datos con contenido cercano a la realidad (dos materias, comisiones,
docentes y estudiantes, banco de preguntas con volumen real) para que Víctor haga una prueba
manual completa navegando la UI — no un smoke test automatizado ni parte de una UAT de
incremento.

## Contenido

- `*.docx` — cuestionarios de origen de dos materias (Gestión de Proyectos, Ingeniería de
  Software). **No versionados en git** (`.gitignore`) — son material de cátedra personal.
- `_extraido/parse_docx.py` — extrae las preguntas de los `.docx` a `preguntas.json`. Ya
  corrido una vez; volver a correrlo solo si cambia el material de origen.
- `preguntas.json` — 113 preguntas estructuradas (materia, unidad temática, tema, tipo,
  opciones/respuesta correcta, dificultad, importancia), versionado en git.
- `config.example.json` — plantilla de Docentes/Comisiones/Estudiantes a sembrar.
- `config.json` — copia de la plantilla con los datos reales completados. **No versionado**
  (nombres/emails reales de personas) — copiar desde el ejemplo:
  ```bash
  cp config.example.json config.json
  ```
  y completar los campos `"PENDIENTE"` en `docentes` antes de sembrar.
- `seed_datos_reales.py` — siembra todo vía la API real (no accede a la base directo, salvo
  el bootstrap del primer Administrador, `scripts/seed_admin.py`, `ADR-016`).

## Uso

```bash
# 1. Postgres local corriendo, backend levantado (ver .claude/skills/run-cognion/SKILL.md)
.venv/bin/uvicorn src.app:app --port 8000

# 2. Frontend levantado
cd frontend && npm run dev

# 3. Completar tests/uat/datos-reales/config.json con los Docentes reales

# 4. Sembrar (desde la raíz del repo)
.venv/bin/python tests/uat/datos-reales/seed_datos_reales.py
```

El script no es idempotente para Materias/Comisiones/Preguntas — correrlo dos veces sobre la
misma base duplica ese contenido (sí es tolerante a que el Administrador o un Docente ya
existan). Para repetir la siembra desde cero, limpiar antes las tablas de negocio (mismo
orden de borrado por FK que `.claude/skills/run-cognion/smoke.sh` — no hay script de limpieza
dedicado acá porque, a diferencia del smoke test, esta siembra está pensada para dejar datos
persistentes mientras dura la prueba manual, no para correr y limpiar en una sola invocación).

Al terminar, el script imprime las credenciales de Administrador, Docentes y Estudiantes para
loguearse y probar.
