# BC Banco de Preguntas — Wireframes: Carga y Filtrado

> Estado documental: **vigente — aprobado por Víctor en sesión de trabajo, 2026-07-31 (pendiente
> de formalizar cierre de Issue — ver §5).**
> Usado como input de las specs US-IEDD de la Iteración 1 (`docs/specs/inc2/US-2.1.x`).
>
> Fuente: `docs/rf/RF_v1.md` (RF-04, RF-05, RF-06), `docs/design/domain/BC-banco-preguntas-modelo.md`
> (comandos `CrearMateria`, `CrearBanco`, `CargarPreguntaOpcionMultiple`,
> `CargarPreguntaVerdaderoFalso`, `EditarPregunta`, `EliminarPregunta`, query `FiltrarBanco`).
>
> Prototipo: `docs/design/ux/prototipos/banco-preguntas-carga-filtrado.html` — navegable,
> 8 pantallas.

---

## 1. Identidad visual

Misma paleta y tipografía que `docs/design/ux/wireframes-identidad.md` §1 (azul institucional
`#1D75B5`, verde de acento `#53AA74`, tipografía Roboto) — continuidad visual entre BCs, sin
redefinir marca. Se agrega un tono de advertencia (`#B5791D` sobre fondo `#FDF5E8`) para
mensajes informativos de riesgo medio (ej. confirmación de eliminación), distinto del rojo
destructivo ya usado en Identidad.

---

## 2. Pantallas

### 2.1 Materias (`#materias`)

**Actor:** Docente autenticado.
**Query implícita:** listado de `Materia` con su `Banco` asociado.

| Elemento | Detalle |
|---|---|
| Contenido | Grilla de tarjetas, una por materia (nombre + cantidad de preguntas activas) |
| Acción | Cada tarjeta navega al banco de esa materia (`#banco`) |
| Acción secundaria | Tarjeta "Nueva materia" (borde punteado) navega a `#nueva-materia` |

### 2.2 Nueva materia (`#nueva-materia`)

**Comando:** `CrearMateria(nombre)`, seguido internamente de `CrearBanco(materia_id)` (1:1,
automático — sin pantalla propia para crear el banco, no hay decisión que tomar en ese paso).

| Elemento | Detalle |
|---|---|
| Campos | Nombre de la materia |
| Validación | Nombre único (INV-BP-00) — mensaje de error si ya existe, no modelado como pantalla propia (mismo criterio de simplicidad que errores de registro en Identidad) |
| Acción primaria | "Crear materia" — vuelve al listado de materias |
| Acción secundaria | "Cancelar" |

### 2.3 Banco — listado y filtro (`#banco`)

**Query:** `FiltrarBanco(materia_id, unidad?, tema?, dificultad?, importancia?)`.

| Elemento | Detalle |
|---|---|
| Contexto | Breadcrumb con la materia seleccionada; contador de preguntas activas |
| Filtros | Unidad temática, tema, dificultad, importancia — todos combinables, todos opcionales (`Todas`/`Todos` por defecto) |
| Tabla | Columnas: texto de la pregunta (truncado), tipo (tag), unidad/tema, dificultad (tag por color), importancia (tag por color), acciones |
| Acciones por fila | "Editar" (`#editar-pregunta`), "Eliminar" (`#eliminar-pregunta`) |
| Acción primaria | "+ Nueva pregunta" → `#nueva-pregunta-tipo` |
| Solo preguntas activas | Preguntas dadas de baja (INV-BP-04) no aparecen en esta tabla |

### 2.4 Nueva pregunta — elegir tipo (`#nueva-pregunta-tipo`)

**Decisión previa a `CargarPreguntaOpcionMultiple`/`CargarPreguntaVerdaderoFalso`** — tipos
diferenciados (§4 de `BC-banco-preguntas-modelo.md`), sin formulario único.

| Elemento | Detalle |
|---|---|
| Contenido | Dos tarjetas seleccionables: "Opción múltiple" y "Verdadero/Falso" |
| Aclaración | El tipo no se puede cambiar después de creada la pregunta — dicho explícitamente en el subtítulo |

### 2.5 Nueva pregunta — Opción múltiple (`#nueva-pregunta-om`)

**Comando:** `CargarPreguntaOpcionMultiple(banco_id, texto, opciones, unidad, tema, dificultad, importancia)`.

| Elemento | Detalle |
|---|---|
| Campos | Texto (textarea), lista de opciones (texto + radio "es correcta"), botón "+ Agregar opción", unidad temática (select), tema (texto libre), dificultad (select Alto/Medio/Bajo), importancia (select Alto/Medio/Bajo) |
| Validación de opciones | Mínimo 2 opciones, exactamente una marcada como correcta (INV-BP-02, INV-BP-03) — validación de cliente antes de enviar, la regla de negocio la aplica el backend |
| Cada opción | Puede quitarse individualmente (✕), salvo que baje de 2 |
| Acción primaria | "Guardar pregunta" — vuelve al banco filtrado |
| Acción secundaria | "Cancelar" |

### 2.6 Nueva pregunta — Verdadero/Falso (`#nueva-pregunta-vf`)

**Comando:** `CargarPreguntaVerdaderoFalso(banco_id, texto, respuesta_correcta, unidad, tema, dificultad, importancia)`.

| Elemento | Detalle |
|---|---|
| Campos | Texto (textarea), selector Verdadero/Falso (dos botones tipo radio, mutuamente excluyentes), mismos metadatos que 2.5 |
| Sin | Lista de opciones — reemplazada por el selector fijo de dos valores (`respuesta_correcta: bool`) |
| Acción primaria | "Guardar pregunta" — vuelve al banco filtrado |

### 2.7 Editar pregunta (`#editar-pregunta`)

**Comando:** `EditarPregunta(pregunta_id, ...)`.

| Elemento | Detalle |
|---|---|
| Formulario | Mismo formulario que la carga (2.5 u 2.6), según el tipo concreto de la pregunta editada, prellenado con sus valores actuales |
| Sin | Selector de tipo — el tipo no se puede cambiar una vez creada la pregunta (mismo criterio que 2.4) |
| Acción primaria | "Guardar cambios" |

### 2.8 Eliminar pregunta — confirmación (`#eliminar-pregunta`)

**Comando:** `EliminarPregunta(pregunta_id)` — baja lógica (INV-BP-04).

| Elemento | Detalle |
|---|---|
| Mensaje | Aclara explícitamente que es baja lógica: la pregunta deja de estar disponible para el banco y nuevas sesiones, pero las sesiones pasadas que ya la usaron no se ven afectadas |
| Contexto | Muestra el texto de la pregunta a eliminar, para confirmar que es la correcta antes de actuar |
| Acción primaria | "Sí, eliminar" (destructivo) |
| Acción secundaria | "Cancelar" |

---

## 3. Responsive

RNF Usabilidad, escenario 1 (PC, tablet, smartphone; browsers vigentes). La grilla de materias
y la tabla de preguntas usan layout fluido (`grid-template-columns: repeat(auto-fill/auto-fit,
minmax(...))`); por debajo de 560px la tabla del banco scrollea horizontalmente en vez de
comprimir columnas (prioriza legibilidad del texto de la pregunta sobre compactar la tabla). Los
formularios de carga/edición usan una columna en mobile (los pares unidad/tema y
dificultad/importancia pasan de 2 columnas a 1).

No aplica el escenario 2 de RNF Usabilidad (legibilidad en proyección de aula) — es específico
de las pantallas de sesión en vivo (Incremento 6), no de estas pantallas de gestión del banco.

---

## 4. Fuera de alcance de este wireframe

- Uso de las preguntas en sesiones (selección aleatoria, presentación al estudiante) —
  Incremento 3, BC Sesiones.
- Gestión de cuentas por Administrador (RF-03) — Iteración 2 de este mismo incremento, BC
  Identidad.
- Importación desde PDF (RF-07) — pospuesto al Incremento 7.
- Pantalla dedicada para el error de nombre de materia duplicado — se resuelve como validación
  inline en `#nueva-materia`, sin pantalla propia (mismo criterio de simplicidad que otros
  errores de formulario en Identidad).
- Un tercer tipo de pregunta — el modelo lo permite (RF-05), pero no hay wireframe hasta que
  exista un RF concreto que lo pida.

---

## 5. Próximo paso

Prototipo y spec completos, validados por Víctor en sesión de trabajo (2026-07-31) — falta
formalizar la creación y cierre del Issue tipo `Modelado` correspondiente en GitHub (mismo
patrón que `US-1.0.2`, Issue #4) para que quede como fuente de verdad de gestión, junto con el
Issue de `docs/design/domain/BC-banco-preguntas-modelo.md` (equivalente a `US-1.0.1`, Issue #2).
