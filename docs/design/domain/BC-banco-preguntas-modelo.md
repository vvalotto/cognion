# BC Banco de Preguntas — Modelo de Dominio (Event Storming)

> Estado documental: **borrador — pendiente de aprobación explícita de Víctor en el comentario
> de cierre del Issue de esta US-Modelado (Iteración 0, Incremento 2).**
> Va a ser usado como input de las specs US-IEDD de la Iteración 1
> (`docs/specs/inc2/US-2.1.x`).
>
> Fuente: `docs/rf/RF_v1.md` (RF-04, RF-05, RF-06), `docs/rf/ARQ_v1.md` (§ Bounded Contexts —
> lenguaje ubicuo `PreguntaPlantilla`, `TipoPregunta`, `UnidadTemática`, `Dificultad`,
> `Importancia`). Modelado en sesión con Víctor, 2026-07-31.

---

## 1. Actores

| Actor | Rol en el BC |
|---|---|
| Docente | Único actor. Crea materias, crea el banco de cada materia, carga/edita/elimina preguntas, filtra el banco |

Sin rol de Administrador en este BC — la gestión de cuentas (RF-03) es de BC Identidad,
Iteración 2 de este mismo incremento.

---

## 2. Línea de tiempo — Eventos de dominio

Orden narrativo, no técnico. 🟧 evento de dominio · 🟦 comando · 🟨 aggregate.

```
[Docente]
   |
🟦 CrearMateria(nombre)
   |
🟧 MateriaCreada
   |
🟦 CrearBanco(materia_id)
   |
🟧 BancoCreado
   |
🟦 CargarPreguntaOpcionMultiple(banco_id, texto, opciones, unidad, tema, dificultad, importancia)
🟦 CargarPreguntaVerdaderoFalso(banco_id, texto, respuesta_correcta, unidad, tema, dificultad, importancia)
   |
🟧 PreguntaCargada
   |
🟦 EditarPregunta(pregunta_id, ...)
   |
🟧 PreguntaEditada
   |
🟦 EliminarPregunta(pregunta_id)
   |
🟧 PreguntaEliminada          (baja lógica — activa = false)
   |
🟦 FiltrarBanco(materia_id, unidad?, tema?, dificultad?, importancia?)
   |
   (read model — sin evento de dominio, solo consulta sobre preguntas activas)
```

---

## 3. Comandos → Eventos

| Comando | Actor | Aggregate | Evento(s) | Excepciones |
|---|---|---|---|---|
| `CrearMateria(nombre)` | Docente | `Materia` (crea) | `MateriaCreada` | `MateriaYaExiste` (nombre duplicado) |
| `CrearBanco(materia_id)` | Docente | `Banco` (crea) — valida contra `Materia` existente | `BancoCreado` | `MateriaNoExiste`, `BancoYaExisteParaMateria` (INV-BP-01) |
| `CargarPreguntaOpcionMultiple(banco_id, texto, opciones, unidad, tema, dificultad, importancia)` | Docente | `PreguntaPlantillaOpcionMultiple` (crea) | `PreguntaCargada` | `BancoNoExiste`, `OpcionesInvalidas` (INV-BP-02) |
| `CargarPreguntaVerdaderoFalso(banco_id, texto, respuesta_correcta, unidad, tema, dificultad, importancia)` | Docente | `PreguntaPlantillaVerdaderoFalso` (crea) | `PreguntaCargada` | `BancoNoExiste` |
| `EditarPregunta(pregunta_id, ...)` | Docente | `PreguntaPlantilla` (edita, según su tipo concreto) | `PreguntaEditada` | `PreguntaNoExiste`, `PreguntaInactiva`, `OpcionesInvalidas` (si aplica al tipo) |
| `EliminarPregunta(pregunta_id)` | Docente | `PreguntaPlantilla` (baja lógica) | `PreguntaEliminada` | `PreguntaNoExiste`, `PreguntaYaEliminada` |

**Query — sin comando ni evento de dominio:**

| Query | Actor | Fuente | Resultado |
|---|---|---|---|
| `FiltrarBanco(materia_id, unidad?, tema?, dificultad?, importancia?)` | Docente | `PreguntaPlantilla` (read model, solo `activa = true`) | Lista de preguntas que matchean todos los filtros provistos |

---

## 4. Aggregates

### `Materia` (Aggregate Root — dueño: BC Banco de Preguntas)

| Atributo | Tipo | Notas |
|---|---|---|
| `id` | UUID | |
| `nombre` | string único | ej. "Ingeniería de Software", "Gestión de Proyectos" |

**Invariantes:**
- **INV-BP-00:** `nombre` único en todo el sistema.

**Alta:** comando de producto `CrearMateria`, actor Docente — no seed/fixture, a diferencia del
primer Administrador en BC Identidad (`BC-identidad-modelo.md` §9.4). Hoy se conocen dos
materias fijas, pero el alta queda como operación normal del producto.

**Nota de alcance — cruce con BC Identidad:** Resuelto en `US-2.1.2`. `Comisión` (BC Identidad,
`src/identidad/entities/comision.py`) tenía `materia: str` shippeado en BL-002 (Incremento 1);
ahora referencia esta `Materia` por `materia_id: UUID` a través de `MateriaPort`
(`src/identidad/entities/ports/materia_port.py`), implementado por `MateriaPortInProcess`
(`src/identidad/frameworks/adapters/`) — llamada directa in-process, mismo criterio que
`ADR-006` para Sesiones→Notificaciones. Ver `docs/architecture/20-context-map-integrations.md`
para la relación documentada.

### `Banco` (Aggregate Root)

| Atributo | Tipo | Notas |
|---|---|---|
| `id` | UUID | |
| `materia_id` | referencia a `Materia` | único — relación 1:1 con `Materia` |

**Invariantes:**
- **INV-BP-01:** a lo sumo un `Banco` por `Materia` (`CrearBanco` sobre una materia que ya
  tiene banco es `BancoYaExisteParaMateria`).

Sin colección propia de `PreguntaPlantilla` como estado del aggregate — evita cargar todas las
preguntas del banco para tocar una sola (ver `PreguntaPlantilla` abajo). `Banco` es, en la
práctica, poco más que el par `(id, materia_id)` que ancla las preguntas de esa materia; su
valor es dar identidad estable a "el banco de la materia X" para que `PreguntaPlantilla`
referencie algo con `id` propio en vez de referenciar `materia_id` directamente.

### `PreguntaPlantilla` (Aggregate Root — tipos diferenciados)

Dos tipos concretos, sin estructura uniforme forzada entre ambos (RF-05 exige poder incorporar
nuevos tipos a futuro — se resuelve agregando un nuevo tipo concreto, no generalizando la
estructura de datos existente).

#### `PreguntaPlantillaOpcionMultiple`

| Atributo | Tipo | Notas |
|---|---|---|
| `id` | UUID | |
| `banco_id` | referencia a `Banco` | |
| `texto` | string | |
| `opciones` | lista de `{texto, es_correcta}` | |
| `unidad_tematica` | string | metadato de clasificación (RF-06) |
| `tema` | string | metadato de clasificación (RF-06) |
| `dificultad` | `Alto \| Medio \| Bajo` | metadato de clasificación (RF-06) |
| `importancia` | `Alto \| Medio \| Bajo` | metadato de clasificación (RF-06) |
| `activa` | bool | `false` tras `EliminarPregunta` (baja lógica) |

**Invariantes:**
- **INV-BP-02:** exactamente una opción con `es_correcta = true`.
- **INV-BP-03:** mínimo 2 opciones.

#### `PreguntaPlantillaVerdaderoFalso`

| Atributo | Tipo | Notas |
|---|---|---|
| `id` | UUID | |
| `banco_id` | referencia a `Banco` | |
| `texto` | string | |
| `respuesta_correcta` | bool | reemplaza `opciones` — no hay lista, son dos valores fijos |
| `unidad_tematica` | string | metadato de clasificación (RF-06) |
| `tema` | string | metadato de clasificación (RF-06) |
| `dificultad` | `Alto \| Medio \| Bajo` | metadato de clasificación (RF-06) |
| `importancia` | `Alto \| Medio \| Bajo` | metadato de clasificación (RF-06) |
| `activa` | bool | `false` tras `EliminarPregunta` (baja lógica) |

**Eliminación — baja lógica (INV-BP-04):** `EliminarPregunta` pone `activa = false`, no borra
la fila. Una pregunta inactiva no aparece en `FiltrarBanco` ni queda disponible para nuevas
sesiones, pero se preserva para no romper el historial de sesiones pasadas que ya la usaron
(Incremento 3, BC Sesiones).

### Value Objects

- **`Dificultad`** — `Alto | Medio | Bajo` (RF-06).
- **`Importancia`** — `Alto | Medio | Bajo` (RF-06).

---

## 5. Hot spots — resueltos con Víctor (2026-07-31)

1. **¿Qué es "el Banco"?** Resuelto — `Banco` es un aggregate con lifecycle propio, 1:1 con
   `Materia`, creado explícitamente por `CrearBanco` antes de poder cargar preguntas (§4).
2. **¿Quién es dueño de `Materia`?** Resuelto — BC Banco de Preguntas. `Comisión` (BC
   Identidad) la referencia por puerto (§4, nota de alcance) — implementado en `US-2.1.2`.
3. **¿`PreguntaPlantilla` aggregate propio o Entity subordinada de `Banco`?** Resuelto —
   aggregate propio (`banco_id` como referencia), para no cargar todo el banco al tocar una
   sola pregunta.
4. **¿Eliminación física o lógica?** Resuelto — lógica (`activa = false`, INV-BP-04) — preserva
   historial de sesiones pasadas.
5. **¿Estructura uniforme entre tipos de pregunta?** Resuelto — tipos diferenciados
   (`PreguntaPlantillaOpcionMultiple` / `PreguntaPlantillaVerdaderoFalso`), sin forzar una
   forma de datos común.
6. **¿Estructura académica más amplia (Institución, Carrera)?** Resuelto — fuera de alcance.
   Ningún RF la pide; el proyecto tiene un docente único con materias conocidas y fijas.
   Diseñar para esa estructura ahora sería anticipar un requerimiento hipotético (anti-patrón
   marcado en `CLAUDE.md`) — se reevalúa si en el futuro aparece un RF real que lo exija.

---

## 6. Próximo paso

Modelo completo (sin hot spots, preguntas abiertas ni observaciones de diseño pendientes,
salvo el mecanismo concreto del puerto Identidad↔Banco de Preguntas, no bloqueante — ver §4) —
pasa a aprobación explícita de Víctor en el comentario de cierre del Issue de esta US-Modelado
(DoD tipo `Modelado`, `WORKFLOW-DESARROLLO.md` §2).
