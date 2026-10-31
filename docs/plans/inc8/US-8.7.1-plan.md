# Plan de Implementación: US-8.7.1 - Carga de datos iniciales (materias y preguntas) desde archivos JSON o Markdown

**Patrón:** clean-architecture-bc · **Producto:** cognion · **BC:** Banco de Preguntas

## Diseño
El dominio no cambia. Se reutilizan `CrearMateriaUseCase`, `CargarPreguntaOpcionMultipleUseCase` y `CargarPreguntaVerdaderoFalsoUseCase` con `docente_id=None` (omite la autorización por Comisión). El parseo de archivos es adaptación de formato; el comando es la capa de frameworks.

```
frameworks/cli/cargar_datos_iniciales.py      ← argparse, descubrimiento de archivos, salida, códigos
interface_adapters/importadores/               ← parseo JSON y Markdown → ArchivoDeDatos (o ArchivoInvalido)
use_cases/cargar_datos_iniciales.py            ← orquesta: materia/banco, validar todo, omitir duplicadas, persistir
```

**Todo o nada por archivo:** los repositorios hacen `commit` por llamada, así que no hay una transacción única. La garantía es la **validación previa completa** (formato y construcción de las entidades, que aplica INV-BP-02/03); si la base falla durante la escritura, volver a ejecutar es seguro por la idempotencia.

## Componentes a Implementar

### 1. Datos de entrada (use_cases)
- [ ] `src/banco_preguntas/use_cases/cargar_datos_iniciales.py`
  - Dataclasses `PreguntaACargar` (tipo, metadatos, opciones | respuesta_correcta), `ArchivoDeDatos` (materia, preguntas, origen) y `ResultadoCarga` (cargadas, omitidas, errores).
  - `CargarDatosInicialesUseCase.execute(archivo, simular=False)`: obtiene o crea la materia y su banco; construye todas las entidades (falla con la posición de la primera inválida); lee los textos de las activas con `PreguntaRepositoryPort.filtrar` sin paginar; omite repetidas; persiste el resto. Con `simular` no escribe (si la materia no existe, valida contra un `banco_id` provisorio).

### 2. Importadores (interface_adapters)
- [ ] `src/banco_preguntas/interface_adapters/importadores/errores.py` — `ArchivoInvalido(mensaje)`.
- [ ] `.../importadores/json_importador.py` — `leer_json(ruta) -> ArchivoDeDatos`; valida campos, tipos, `dificultad`/`importancia` en `bajo|medio|alto`, límites de longitud (texto 2000, unidad y tema 200).
- [ ] `.../importadores/markdown_importador.py` — `leer_cuestionario(ruta, materia) -> ArchivoDeDatos`: separa por `---`, extrae enunciado tras `**Pregunta N.**`, opciones `a)`..`f)` (2 a 6), `Respuesta correcta: x)`, `Nivel`; `unidad_tematica` de la cabecera, `tema` del nombre sin ` - Cuestionario.md`; dificultad `Fácil/Medio/Difícil → bajo/medio/alto`, importancia igual a la dificultad.

### 3. Comando (frameworks)
- [ ] `src/banco_preguntas/frameworks/cli/__init__.py` y `cargar_datos_iniciales.py`
  - `python -m src.banco_preguntas.frameworks.cli.cargar_datos_iniciales <ruta> [--materia NOMBRE] [--simular]`.
  - Descubre `*.json` y `* - Cuestionario.md` (carpeta, orden alfabético) o toma un archivo; `.md` exige `--materia` (error antes de leer).
  - Procesa archivo por archivo; un error no frena a los demás; resumen por archivo/materia; código 0 si todo bien, 1 si algún archivo falló o la entrada es inválida; mensajes sin traza (archivo ausente, JSON inválido, base inaccesible).
  - Cableado real con `SessionLocal` en `_main` (`# pragma: no cover`, igual que `bootstrap_administrador`).

## Integración
- [ ] Sin cambios en el dominio, en la API ni en `dependencies.py` de FastAPI.
- [ ] `docs/plans/DESPLIEGUE-LOCAL.md`: paso de carga después de `levantar.sh`, formato de archivos y ejemplo (Fase 8).
- [ ] `docs/plans/ejemplos/datos-iniciales.ejemplo.json` ya existe.

## Tests (se hacen en las Fases 4 a 6)
- Unitarios: importadores (válidos, formato inválido, mapeos) y caso de uso con repositorios en memoria (idempotencia, simular, todo o nada, materia existente).
- Integración: el comando contra una base **descartable** (`DATABASE_URL` inline; nunca la local).
- BDD: los 11 escenarios del `.feature` aprobado.

## Riesgos
- **CBO** del caso de uso (muchas dependencias): el pre-push lo mide y Fase 7 no. Se mantiene el caso de uso chico y la validación en funciones aparte; si llega al umbral, se separa la construcción de entidades.
- Las pruebas de integración y BDD **vacían la base**: correrlas solo con una base descartable inline, nunca con `cognion_local`.
- Un cuestionario real con un formato no previsto: se verifica de punta a punta con los 17 archivos reales en modo `--simular`.
