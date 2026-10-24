# US-8.7.1: Carga de datos iniciales (materias y preguntas) desde archivos JSON

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-8.7`
**Tipo**: `tooling operativo` (comando de línea de comandos en `src/banco_preguntas/frameworks/cli/`)
**Bounded Context**: Banco de Preguntas
**Issue**: (a crear)

---

## Descripcion (lenguaje de negocio)

Como **docente que instala Cognión en su equipo**,
quiero **cargar mis materias y mis preguntas desde archivos con un solo comando**,
para **que la versión de producción nazca con mi contenido sin cargarlo pregunta por pregunta desde la pantalla**.

---

## Contexto

La versión `v0.9.0` corre en la Mac de Víctor, sin nube (`ADR-021` y `ADR-024` en revisión). Las preguntas son material de cátedra y
**no se versionan en el repositorio**: Víctor genera los archivos y el comando los lee desde una carpeta que él elige (por ejemplo
`~/CognionDatos/`). Hoy la carga masiva se hizo con un script fuera de git (`tests/uat/datos-reales/cargar_preguntas.py`) que habla
por HTTP con un JWT; esta US lo reemplaza por un comando soportado que usa los casos de uso del Banco de Preguntas, para que se
valide con las mismas invariantes de dominio (INV-BP-02, INV-BP-03). No carga estudiantes, comisiones ni contraseñas: el
Administrador sigue naciendo en `scripts/local/levantar.sh`.

## Especificacion del comportamiento

**Comando:**
`python -m src.banco_preguntas.frameworks.cli.cargar_datos_iniciales <ruta> [--simular]`
- `<ruta>` es un archivo `.json` o una carpeta; si es carpeta, procesa todos los `*.json` en orden alfabético.
- Lee la base de `DATABASE_URL` del entorno (el de `.env.local`, igual que `bootstrap_administrador`).
- `--simular` valida todo y muestra qué haría, sin escribir nada.

**Formato de cada archivo** (una materia por archivo):
```json
{
  "materia": "Ingeniería de Software",
  "preguntas": [
    {
      "tipo": "opcion_multiple",
      "texto": "¿Qué es la arquitectura de software?",
      "unidad_tematica": "Arquitectura de Software",
      "tema": "Fundamentos",
      "dificultad": "medio",
      "importancia": "alto",
      "opciones": [
        {"texto": "…", "es_correcta": false},
        {"texto": "…", "es_correcta": true}
      ]
    },
    {
      "tipo": "verdadero_falso",
      "texto": "…",
      "unidad_tematica": "…",
      "tema": "…",
      "dificultad": "bajo",
      "importancia": "medio",
      "respuesta_correcta": true
    }
  ]
}
```
`dificultad` e `importancia` toman `bajo`, `medio` o `alto`. Los límites de longitud son los de la API (texto 2000, unidad y tema 200).

**Reglas:**
- Si la materia no existe, la crea con su banco (`CrearMateriaUseCase`); si existe, la reutiliza.
- Cada pregunta se carga con `CargarPreguntaOpcionMultipleUseCase` o `CargarPreguntaVerdaderoFalsoUseCase`, de modo que se aplican las
  invariantes del dominio.
- **Idempotente:** una pregunta cuyo `texto` ya existe y está activa en el banco de esa materia se omite. Volver a ejecutar el
  comando no duplica nada.
- **Todo o nada por archivo:** se valida el archivo completo antes de escribir. Un error en cualquier pregunta (formato, opciones
  sin exactamente una correcta, tipo desconocido) aborta ese archivo sin cargar nada de él y se informa la posición y el motivo.
- Un error en un archivo no impide procesar los demás; el código de salida es distinto de cero si algún archivo falló.
- Al terminar imprime un resumen por materia: preguntas cargadas, omitidas por duplicadas y con error.
- Sin trazas: ante un archivo ausente, un JSON inválido o una base inaccesible, un mensaje claro y salida distinta de cero.

**Documentación:** `docs/plans/DESPLIEGUE-LOCAL.md` incorpora el paso de carga después de `levantar.sh` y el formato de los archivos.
Se agrega un archivo de ejemplo mínimo en `docs/plans/ejemplos/datos-iniciales.ejemplo.json` (2 preguntas, no es contenido de cátedra).

## Escenarios (BDD)

1. Base sin la materia → el comando crea la materia, su banco y las preguntas del archivo, y el resumen coincide con el archivo.
2. Segunda ejecución con el mismo archivo → no se carga nada nuevo (todas omitidas por duplicadas) y la salida es 0.
3. Archivo con una pregunta de opción múltiple sin opción correcta → ese archivo no carga ninguna pregunta, se informa cuál y por qué.
4. Carpeta con dos materias, una con error → la otra se carga completa y el código de salida es distinto de cero.
5. `--simular` → informa lo que cargaría y la base queda idéntica.
6. Materia ya existente (creada desde la pantalla) → se reutiliza y se le agregan las preguntas nuevas.
7. JSON inválido o ruta inexistente → mensaje claro, sin traza, salida distinta de cero.

## Fuera de alcance

Carga de estudiantes, comisiones, docentes o actividades; importación desde `.docx` o PDF (RF-07); edición o baja de preguntas
existentes; exportar el banco a JSON.

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.
