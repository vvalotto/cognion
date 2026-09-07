# Portal de Entrada — Mapa de Navegación por Rol

> Estado documental: **borrador — pendiente de aprobación explícita de Víctor en el comentario
> de cierre del Issue [#261](https://github.com/vvalotto/cognion/issues/261) (US-4ADJ.0.1,
> Iteración 0, Incremento 4-ADJ).**
> No es un modelo de dominio — Portal de Entrada no es un BC, no tiene aggregate ni evento
> propio. Es un mapa de **arquitectura de información**: qué accesos existen hoy por rol, cómo
> se agrupan, con qué prioridad y con qué nombre — insumo para el wireframe visual de
> `US-4ADJ.0.2`.
> Origen: `docs/aprendizajes/HITO-9-PORTAL-DE-ENTRADA-SIN-DUENO-DE-PRODUCTO.md`.
> Todos los accesos listados abajo son rutas **ya existentes**, protegidas por `RequireRole` —
> este documento no propone ningún endpoint ni pantalla de contenido nuevos, solo cómo
> llegar a ellos.

---

## 1. Problema que resuelve

Hoy, tras el login, los tres roles caen en `InicioPlaceholder`
(`frontend/src/pages/_placeholders.tsx`) — un callejón sin salida. Además, `AppLayout.tsx` no
tiene ningún menú de navegación: ni siquiera dentro de un mismo rol hay forma de moverse entre
áreas top-level sin escribir la URL de memoria (ej.: el Docente en `/materias`, viendo el Banco
de Preguntas, no tiene ningún enlace hacia `/actividad-evaluativa/materias`).

Este documento resuelve dos cosas a la vez:
1. **Menú de navegación persistente** — visible en toda pantalla post-login (no solo en el
   home), permite moverse entre áreas sin volver atrás.
2. **Home por rol** — reemplaza `InicioPlaceholder`, punto de aterrizaje tras el login con
   acceso directo a las áreas de ese rol.

---

## 2. Inventario de accesos existentes, por rol

Relevado directamente de `frontend/src/router.tsx` (rutas ya protegidas por `RequireRole`,
`US-1.1.9`) — ningún acceso nuevo, solo los que ya tienen pantalla funcionando.

### Docente

| Área (BC) | Ruta de entrada | Título de pantalla actual |
|---|---|---|
| Banco de Preguntas | `/materias` | "Materias" |
| Actividad Evaluativa | `/actividad-evaluativa/materias` | "Mis materias" |
| Analytics — por alumno | `/analytics/desempeno-por-alumno` | "Desempeño por alumno" |
| Analytics — por tema | `/analytics/desempeno-por-tema` | "Desempeño por tema" |

### Estudiante

| Área (BC) | Ruta de entrada | Título de pantalla actual |
|---|---|---|
| Actividad Evaluativa | `/mis-actividades/materias` | "Mis materias" |
| Analytics — propio | `/analytics/mi-desempeno` | "Mi desempeño" |

### Administrador

| Área (BC) | Ruta de entrada | Título de pantalla actual |
|---|---|---|
| Identidad — alta de cuenta | `/docentes/nuevo` | "Crear cuenta de Docente" |
| Identidad — gestión de cuentas | `/cuentas` | "Cuentas" |

**Gap real detectado al revisar este mapa con Víctor (2026-09-07):** no existe ninguna
pantalla para crear una Comisión ni para asignar un Docente a ella — el backend existe desde
`US-1.1.1` (Incremento 1), pero la UI quedó explícitamente diferida "sin fecha" en la
Iteración 2 de ese incremento (`docs/traceability/matrix.md`, nota de `US-1.1.9`) y nunca se
retomó. Sin esto, **el alta de un Estudiante real está rota de punta a punta en la UI** —
`Registro.tsx` asume que ya existe un link de invitación, pero nadie puede generarlo sin una
Comisión creada y sin un Docente asignado a ella primero. Decisiones tomadas con Víctor:

- Materia (Banco de Preguntas) y Comisión (Identidad) **siguen siendo conceptos separados**
  — una Materia puede tener varias Comisiones/horarios.
- Asignar un Docente a una Comisión **tiene pantalla propia** (acción separada de crear la
  Comisión), aunque el sistema sea de un solo Docente hoy.
- La Comisión la crea el **Administrador** (coincide con el backend actual —
  `Comisión.administrador_id`, `require_administrador` en `POST /comisiones`).

Esto agrega un área nueva al mapa — no es solo navegación, es cerrar un gap real de `RF-01`:

| Área (BC) | Ruta de entrada (nueva) | Acción |
|---|---|---|
| Identidad — Comisiones | `/comisiones` (a confirmar en wireframe) | Administrador: ver Comisiones de una Materia, crear una nueva, asignar Docente, ver Estudiantes inscriptos |
| Identidad — Invitación | dentro del detalle de una Comisión | Docente: generar el link de invitación de una Comisión donde está asignado |

**Consecuencia técnica:** `GET /materias/{id}/comisiones` y `GET /comisiones/{id}/estudiantes`
hoy exigen rol `docente` (`require_docente`, construidos para el selector de Analytics en
`US-4.2.2`) — el Administrador necesita acceso también. Esto **toca `src/`** (ampliar el
guard de rol a `administrador` además de `docente`), no es frontend puro como se asumió al
abrir este incremento.

**Hallazgo de nomenclatura (a resolver en `US-4ADJ.0.2` o antes):** tanto `/materias`
(Docente, Banco de Preguntas) como `/actividad-evaluativa/materias` (Docente, Actividad
Evaluativa) usan la palabra "materias" en su título de pantalla ("Materias" / "Mis materias")
para conceptos distintos — la primera es el banco de preguntas de una materia, la segunda es
el listado de actividades de una materia. En un menú persistente con las dos visibles a la vez
para el mismo rol, esa ambigüedad es real y hay que resolverla con nombres de menú distintos
(ver §4).

---

## 3. Menú de navegación persistente

Un único componente en `AppLayout.tsx`, condicionado por `session.rol` — mismo dato que ya usa
el header actual para el badge de rol. Reemplaza el header actual (logo + badge) por
logo + badge + los ítems de este menú.

| Rol | Ítems del menú (orden) |
|---|---|
| **Docente** | 1. Banco de Preguntas (`/materias`) — 2. Actividades (`/actividad-evaluativa/materias`) — 3. Desempeño por alumno (`/analytics/desempeno-por-alumno`) — 4. Desempeño por tema (`/analytics/desempeno-por-tema`) |
| **Estudiante** | 1. Mis Actividades (`/mis-actividades/materias`) — 2. Mi Desempeño (`/analytics/mi-desempeno`) |
| **Administrador** | 1. Comisiones (`/comisiones`) — 2. Docentes (`/docentes/nuevo`) — 3. Cuentas (`/cuentas`) |
| **Docente (adicional)** | La generación del link de invitación vive dentro del detalle de una Comisión, no como ítem de menú propio — el Docente llega ahí desde "Actividades" o desde una vista de sus Comisiones a confirmar en el wireframe (`US-4ADJ.0.2`) |

**Criterio de orden:** para Docente, orden de "creación de contenido → ejecución → análisis"
(Banco → Actividades → Analytics), mismo orden causal que el flujo real de uso (primero se
carga el banco, después se crean actividades sobre él, al final se analiza el resultado). Para
Estudiante, orden de uso (primero rinde, después consulta desempeño). Para Administrador,
orden causal del ciclo de alta (Comisiones → Docentes → Cuentas): antes de poder invitar
estudiantes hace falta una Comisión con un Docente asignado; alta de Docente y gestión de
Cuentas son tareas de mantenimiento recurrente, después de ese paso inicial.

**Decisión abierta para Víctor:** ¿"Banco de Preguntas" y "Actividades" van sueltos en el menú
(como arriba) o agrupados bajo un único ítem "Materias" con submenú? El wireframe de
`US-4ADJ.0.2` puede explorar ambas — este mapa no fuerza una sola opción.

---

## 4. Contenido de cada Home

Reemplaza `InicioPlaceholder` para cada rol. Mismos accesos que el menú persistente, pero como
tarjetas/accesos directos con una descripción de una línea — el home es la primera pantalla
que ve el usuario, así que puede permitirse más contexto que un ítem de menú.

### Home Docente (`/`)

| Tarjeta | Ruta | Descripción de una línea |
|---|---|---|
| Banco de Preguntas | `/materias` | Cargar, editar y filtrar preguntas por materia |
| Actividades | `/actividad-evaluativa/materias` | Crear y administrar actividades de evaluación |
| Desempeño por alumno | `/analytics/desempeno-por-alumno` | Consultar el desempeño de un estudiante elegido |
| Desempeño por tema | `/analytics/desempeno-por-tema` | Tasa de error por unidad/tema de una materia |

### Home Estudiante (`/`)

| Tarjeta | Ruta | Descripción de una línea |
|---|---|---|
| Mis Actividades | `/mis-actividades/materias` | Ver y rendir las actividades disponibles |
| Mi Desempeño | `/analytics/mi-desempeno` | Ver el resultado acumulado de mis evaluaciones |

### Home Administrador (`/`)

| Tarjeta | Ruta | Descripción de una línea |
|---|---|---|
| Comisiones | `/comisiones` | Crear comisiones, asignar docentes y ver estudiantes inscriptos |
| Alta de Docente | `/docentes/nuevo` | Crear una cuenta nueva de Docente |
| Cuentas | `/cuentas` | Ver, filtrar, resetear y desbloquear cuentas existentes |

**Nota:** hoy `RUTA_POST_LOGIN[administrador]` en `Login.tsx` salta directo a `/docentes/nuevo`
sin pasar por un home — `US-4ADJ.1.4` lo cambia a `/` (home real), igual que Docente y
Estudiante, para que el Administrador también tenga un punto de partida navegable en vez de
aterrizar siempre en la misma tarea.

---

## 5. Fuera de alcance de este mapa

- **Contenido nuevo** — este documento no agrega ninguna función; todas las rutas ya existen.
- **Diseño visual** (colores, tipografía, layout de las tarjetas/menú) — corresponde al
  wireframe de `US-4ADJ.0.2`, no a este mapa.
- **Notificaciones o badges** en el menú (ej. "3 actividades por corregir") — no hay ningún
  read model para eso todavía; queda fuera hasta que exista una necesidad concreta.

---

*Creado: 2026-09-07*
