# US-8.7.1: Carga de datos iniciales (materias y preguntas) desde archivos JSON o Markdown

**Estado**: `Implementada`
**Iteracion / Sprint**: `INC-8.7`
**Tipo**: `tooling operativo` (comando de línea de comandos en `src/banco_preguntas/frameworks/cli/`)
**Bounded Context**: Banco de Preguntas
**Issue**: #564

---

## Descripcion (lenguaje de negocio)

Como **docente que instala Cognión en su equipo**,
quiero **cargar mis materias y mis preguntas desde mis archivos (JSON o Markdown) con un solo comando**,
para **que la versión de producción nazca con mi contenido sin cargarlo pregunta por pregunta desde la pantalla**.

---

## Contexto

La versión `v0.9.0` corre en la Mac de Víctor, sin nube (`ADR-021` y `ADR-024` en revisión). Las preguntas son material de cátedra y
**no se versionan en el repositorio**: Víctor genera los archivos y el comando los lee desde una carpeta que él elige (por ejemplo
`~/CognionDatos/`). Hoy la carga masiva se hizo con un script fuera de git (`tests/uat/datos-reales/cargar_preguntas.py`) que habla
por HTTP con un JWT; esta US lo reemplaza por un comando soportado que usa los casos de uso del Banco de Preguntas, para que se
valide con las mismas invariantes de dominio (INV-BP-02, INV-BP-03). Los cuestionarios de Gestión de Proyectos ya existen como 17
archivos Markdown con 20 preguntas de opción múltiple cada uno (340 en total, formato regular verificado el 2026-10-24) en
`tests/uat/datos-reales/` (fuera de git); el comando debe poder leerlos tal cual, sin convertirlos a mano. No carga estudiantes, comisiones ni contraseñas: el
Administrador sigue naciendo en `scripts/local/levantar.sh`.

## Especificacion del comportamiento

**Comando:**
`python -m src.banco_preguntas.frameworks.cli.cargar_datos_iniciales <ruta> [--materia NOMBRE] [--simular]`
- `<ruta>` es un archivo `.json` o `.md`, o una carpeta; si es carpeta, procesa todos los `*.json` y los `*.md` cuyo nombre termina en
  ` - Cuestionario.md`, en orden alfabético (los demás `.md`, como bitácoras, se ignoran).
- `--materia` es obligatorio para los `.md` (no traen la materia) y se ignora en los `.json`, que la declaran adentro.
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

**Formato Markdown de cuestionario** (un archivo = un tema; solo opción múltiple):
```markdown
# Cuestionario — Riesgos

**Unidad temática:** 09 – Incertidumbre

**Pregunta 1.** ¿Cómo se define un riesgo según el material?

a) Un problema que ya ocurrió y afecta al proyecto.
b) Un error en la planificación.
c) Un cambio aprobado en la línea base.
d) Un acontecimiento o condición incierta que…

✅ **Respuesta correcta: d)** — Justificación (se ignora). *(Nivel: Fácil)*

---
```
- Las preguntas se separan por `---`; el enunciado es el texto después de `**Pregunta N.**`; las opciones son las líneas `a) …`
  hasta `d) …` (entre 2 y 6); la correcta sale de `Respuesta correcta: x)`.
- `unidad_tematica` = valor de `**Unidad temática:**` de la cabecera, tal cual.
- `tema` = nombre del archivo sin ` - Cuestionario.md` (por ejemplo `Riesgos - Cuestionario.md` → `Riesgos`).
- `dificultad` desde `Nivel`: `Fácil` → `bajo`, `Medio` → `medio`, `Difícil` → `alto`.
- `importancia` se **deriva de la dificultad** con la misma escala (`bajo`, `medio`, `alto`); se puede ajustar luego desde la pantalla.
- Un `Nivel` distinto de los tres, una letra correcta que no existe entre las opciones o una pregunta sin `Nivel` es un error de formato.

**Reglas:**
- Si la materia no existe, la crea con su banco (`CrearMateriaUseCase`); si existe, la reutiliza.
- Cada pregunta se carga con `CargarPreguntaOpcionMultipleUseCase` o `CargarPreguntaVerdaderoFalsoUseCase`, de modo que se aplican las
  invariantes del dominio.
- **Idempotente:** una pregunta cuyo `texto` ya existe y está activa en el banco de esa materia se omite. Volver a ejecutar el
  comando no duplica nada.
- **Todo o nada por archivo:** se valida el archivo completo antes de escribir (si la base falla durante la escritura, volver a ejecutar es seguro: el comando es idempotente). Un error en cualquier pregunta (formato, opciones
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
4. Carpeta con dos archivos, uno con error → el otro se carga completo y el código de salida es distinto de cero.
5. `--simular` → informa lo que cargaría y la base queda idéntica.
6. Materia ya existente (creada desde la pantalla) → se reutiliza y se le agregan las preguntas nuevas.
7. JSON inválido o ruta inexistente → mensaje claro, sin traza, salida distinta de cero.
8. Cuestionario `.md` con `--materia "Gestión de Proyectos"` → se cargan sus 20 preguntas con unidad, tema, dificultad e importancia derivados según las reglas de arriba.
9. Carpeta con los 17 cuestionarios → 340 preguntas cargadas en una única materia; una segunda ejecución las omite todas.
10. `.md` sin `--materia` → error claro antes de leer nada.
11. Cuestionario `.md` con `Nivel` desconocido o respuesta correcta inexistente → ese archivo no carga nada y se indica la pregunta.

## Fuera de alcance

Carga de estudiantes, comisiones, docentes o actividades; importación desde `.docx` o PDF (RF-07); preguntas de verdadero/falso en Markdown; edición o baja de preguntas
existentes; exportar el banco a JSON.

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.
