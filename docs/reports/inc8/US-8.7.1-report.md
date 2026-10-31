# Reporte — US-8.7.1: Carga de datos iniciales (materias y preguntas) desde archivos JSON o Markdown

**Estado:** implementada en `feature/US-8.7.1-carga-datos-iniciales` (2026-10-24). PR pendiente.
**Issue:** #564 · **Spec:** `docs/specs/inc8/US-8.7.1.md` · **Iteración:** 7, versión local `v0.9.0`

## Qué se hizo
- `src/banco_preguntas/use_cases/cargar_datos_iniciales.py`: crea la materia y su banco si faltan, valida el archivo completo (INV-BP-02/03) antes de escribir, omite las preguntas ya cargadas o repetidas y persiste el resto reutilizando `CrearMateriaUseCase` y los dos casos de uso de carga con `docente_id=None`.
- `interface_adapters/importadores/`: lectores de JSON (opción múltiple y verdadero/falso) y de cuestionarios Markdown (unidad de la cabecera, tema del nombre del archivo, dificultad del `Nivel`, importancia derivada de la dificultad).
- `frameworks/cli/cargar_datos_iniciales.py`: `python -m ...cargar_datos_iniciales <ruta> [--materia NOMBRE] [--simular]`; procesa archivos o carpetas, un error no frena a los demás, sin trazas, salida 0 o 1.
- El dominio, la API y `dependencies.py` no cambiaron.

## Decisiones
- **Todo o nada por archivo = validación previa**, no transacción única: los repositorios hacen `commit` por llamada. Si la base falla a mitad de un archivo, volver a ejecutar es seguro por la idempotencia.
- Idempotencia por **texto exacto** de la pregunta activa en el banco: editar un texto y recargar agrega una pregunta nueva.
- Las preguntas no se versionan: Víctor las mantiene en una carpeta propia.

## Verificación con datos reales
Base descartable, con los 17 cuestionarios de Gestión de Proyectos: 340 preguntas, 17 temas, 10 unidades; 102 bajo/bajo, 170 medio/medio, 68 alto/alto; la segunda corrida no duplica. La carpeta `tests/uat/datos-reales/` mezcla otros `.json` que el comando marca como error: se recomienda una carpeta dedicada.

## Calidad
Suite completa 2088 pasaron, 0 fallos (unit + integración + BDD contra base descartable). 41 tests unitarios, 5 de integración con PostgreSQL real y 14 casos BDD (11 escenarios). Cobertura total 97,22 %; archivos nuevos 98-100 %. ruff, black, isort y mypy limpios; pylint 9,96/10; CC máx 9; CodeGuard completo sin advertencias reales (la primera corrida marcó complejidad 12, resuelta partiendo `ejecutar`); DesignReviewer 0 bloqueantes. Evidencia: `quality/reports/inc8/US-8.7.1-quality.json`.

## Pendiente
- Probar la carga sobre `cognion_local` real (solo se probó en base descartable) como parte de la UAT.
- Eliminar la base descartable `cognion_test_us871`.
- PR contra `develop` y cierre del Issue #564 tras el merge.
