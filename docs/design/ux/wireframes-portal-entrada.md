# Portal de Entrada — Wireframes (Incremento 4-ADJ)

> Estado documental: **borrador — pendiente de aprobación explícita de Víctor en el comentario
> de cierre del Issue [#262](https://github.com/vvalotto/cognion/issues/262) (US-ADJ-22,
> Iteración 0, Incremento 4-ADJ).**
> Alcance: portal de entrada (menú de navegación persistente + home por rol, `US-ADJ-27` a
> `30`) y pantallas de Comisiones (`US-ADJ-23` a `26`) — gate UX obligatorio para las 8 US de
> la Iteración 1, ninguna se implementa sin este documento aprobado.
>
> Fuente: `docs/design/domain/portal-entrada-modelo.md` (mapa de navegación, aprobado en
> `US-ADJ-21`), `docs/rf/RF_v1.md` (RF-01, mitad "Docente/Administrador" nunca implementada en
> UI), `docs/aprendizajes/HITO-9-PORTAL-DE-ENTRADA-SIN-DUENO-DE-PRODUCTO.md`.
>
> Prototipo: `docs/design/ux/prototipos/portal-entrada.html` — navegable, 7 pantallas.

---

## 1. Identidad visual

Misma paleta y tipografía que `wireframes-analytics.md` §1, `wireframes-actividad-evaluativa.md`
§1, `wireframes-banco-preguntas.md` §1 y `wireframes-cuentas-administracion.md` §1 (azul
institucional `#1D75B5`, verde de acento `#53AA74`, Roboto) — continuidad visual entre BCs e
iteraciones, sin redefinir tokens nuevos. Primitivas reutilizadas: `Card`, `Badge`,
`Breadcrumb`, tabla de datos (`identidad-cuentas-administracion.html`). Primitiva **nueva**:
`.app-nav` — barra de navegación persistente bajo el header de aplicación, con el ítem de la
sección actual resaltado; reemplaza el header actual de `AppLayout.tsx` (solo logo + badge de
rol, sin navegación).

---

## 2. Pantallas — Portal de entrada (menú + home)

### 2.1 Home Docente (`#home-docente`) — `US-ADJ-28`

**Actor:** Docente.
**Reemplaza:** `InicioPlaceholder` para rol `docente`.

| Elemento | Detalle |
|---|---|
| Contexto | Sin breadcrumb — es la raíz (`/`) |
| Saludo | "Hola, {nombre}" |
| `.app-nav` | Inicio (actual) · Banco de Preguntas · Actividades · Desempeño por alumno · Desempeño por tema |
| Cards de acceso | 4 cards: Banco de Preguntas, Actividades, Desempeño por alumno, Desempeño por tema — cada una con título + descripción de una línea, click navega a la ruta ya existente |
| Fuera de alcance | Contenido dinámico (contadores, notificaciones) — solo navegación, ver `portal-entrada-modelo.md` §5 |

### 2.2 Home Estudiante (`#home-estudiante`) — `US-ADJ-29`

**Actor:** Estudiante.
**Reemplaza:** `InicioPlaceholder` para rol `estudiante`.

| Elemento | Detalle |
|---|---|
| Contexto | Sin breadcrumb — es la raíz (`/`) |
| Saludo | "Hola, {nombre}" |
| `.app-nav` | Inicio (actual) · Mis Actividades · Mi Desempeño |
| Cards de acceso | 2 cards: Mis Actividades, Mi Desempeño |

### 2.3 Home Administrador (`#home-admin`) — `US-ADJ-30`

**Actor:** Administrador.
**Reemplaza:** salto directo a `/docentes/nuevo` (`RUTA_POST_LOGIN[administrador]` en
`Login.tsx`) — pasa a apuntar a `/` como los otros dos roles.

| Elemento | Detalle |
|---|---|
| Contexto | Sin breadcrumb — es la raíz (`/`) |
| `.app-nav` | Inicio (actual) · Comisiones · Docentes · Cuentas |
| Cards de acceso | 3 cards: Comisiones, Alta de Docente, Cuentas |

### 2.4 Menú de navegación persistente (`.app-nav`) — `US-ADJ-27`

No es una pantalla propia — es el componente que aparece en **todas** las pantallas
post-login (home incluido), integrado en `AppLayout.tsx` debajo del header actual.

| Elemento | Detalle |
|---|---|
| Condicionado por rol | `session.rol` decide qué ítems se muestran — mismo dato que ya usa el header para el badge |
| Ítem activo | El ítem de la sección actual queda resaltado (subrayado + color primario) — `.app-nav a.current` en el prototipo |
| Nomenclatura | "Banco de Preguntas" y "Actividades" (Docente) — sin la palabra "materias" en ninguno de los dos, resuelve la ambigüedad de `portal-entrada-modelo.md` §2 |
| Agrupamiento | Ítems sueltos, sin submenú — ver decisión en `portal-entrada-modelo.md` §3 |
| Fuera de alcance | Badges de notificación, buscador global — no hay read model para eso hoy |

---

## 3. Pantallas — Comisiones (cierra la UI de RF-01)

### 3.1 Listado de Comisiones por Materia (`#admin-comisiones`) — `US-ADJ-23`

**Actor:** Administrador.
**Consume:** `GET /materias` (`US-2.1.9`), `GET /materias/{id}/comisiones` +
`GET /comisiones/{id}/estudiantes` (ambos ampliados a rol `administrador`, ver
`portal-entrada-modelo.md` §2).

| Elemento | Detalle |
|---|---|
| Contexto | Breadcrumb "Comisiones › {materia}" |
| Selector | Materia (`GET /materias`) |
| Tabla | Horario, Docentes asignados (badge verde si hay al menos uno, badge ámbar "Sin docente asignado" si no), cantidad de Estudiantes inscriptos, acción "Ver detalle" |
| Acción "+ Nueva Comisión" | Navega a `#admin-comision-nueva` |
| Estado vacío | Si la materia no tiene ninguna Comisión: mensaje simple + botón "+ Nueva Comisión" destacado |

### 3.2 Nueva Comisión (`#admin-comision-nueva`) — `US-ADJ-24`

**Actor:** Administrador.
**Consume:** `POST /comisiones` (`materia_id`, `horario`) — ya acepta rol `administrador`,
sin cambios de backend.

| Elemento | Detalle |
|---|---|
| Contexto | Breadcrumb "Comisiones › Nueva Comisión" |
| Campo Materia | Preseleccionada si se llega desde el listado de una materia; select si se llega desde otro lado |
| Campo Horario | Texto libre (ej. "Lunes y Miércoles 18–20hs") — sin catálogo, mismo criterio que otros campos de texto libre del sistema (`unidad_tematica`/`tema` de Banco de Preguntas, `US-ADJ-02`) |
| Acción | "Crear Comisión" → success navega al detalle de la Comisión recién creada (`#admin-comision-detalle`) |
| Fuera de alcance | Asignar Docente en el mismo formulario — acción separada (`US-ADJ-25`), decisión ya tomada con Víctor |

### 3.3 Detalle de Comisión — vista Administrador (`#admin-comision-detalle`) — `US-ADJ-25`

**Actor:** Administrador.
**Consume:** `GET /usuarios?rol=docente` (`US-2.2.2`), `POST /comisiones/{id}/docentes` (ya
acepta rol `administrador`), `GET /comisiones/{id}/estudiantes` (ampliado a `administrador`).

| Elemento | Detalle |
|---|---|
| Contexto | Breadcrumb "Comisiones › {horario}" + botón "‹ Volver a Comisiones" |
| Alerta | Si la Comisión no tiene Docente asignado: alerta informativa — "Hasta que se asigne un Docente, esta Comisión no puede generar link de invitación para estudiantes" |
| Asignar Docente | Select con los usuarios de rol `docente` (`GET /usuarios?rol=docente`) + botón "Asignar" — visible siempre que se pueda agregar otro (el sistema no impide más de un Docente, aunque hoy solo exista uno) |
| Estudiantes inscriptos | Tabla (Nombre, Email) o estado vacío si la Comisión no tiene ninguno todavía |
| Fuera de alcance | Generar invitación — acción exclusiva del Docente (`#docente-comision-detalle`, `US-ADJ-26`), el Administrador no la genera |

### 3.4 Detalle de Comisión — vista Docente, generar invitación (`#docente-comision-detalle`) — `US-ADJ-26`

**Actor:** Docente (solo Comisiones donde está asignado).
**Consume:** `POST /comisiones/{id}/invitaciones` (`US-1.1.1`, ya acepta rol `docente`),
`GET /comisiones/{id}/estudiantes` (ya acepta rol `docente` desde `US-4.2.2`, sin cambios).

| Elemento | Detalle |
|---|---|
| Contexto | Breadcrumb "Actividades › Comisiones › {horario}" + botón "‹ Volver" |
| Acción principal | "Generar link de invitación" — al confirmar, muestra el link generado en un recuadro con botón "Copiar" |
| Link generado | Válido 7 días desde la generación, un solo uso por invitación (`ADR-012`) — texto de ayuda debajo del link |
| Generar de nuevo | El botón cambia a "Generar un link nuevo" tras la primera generación — cada click genera una invitación distinta, no reutiliza la anterior |
| Estudiantes inscriptos | Misma tabla que la vista Administrador — visibilidad de solo lectura |
| Cómo se llega | Desde "Actividades" en el `.app-nav`, o desde una lista de Comisiones del Docente a confirmar en la implementación (`US-ADJ-26`) — no es una ruta nueva del menú principal, es un nivel más profundo dentro de Actividades |

---

## 4. Fuera de alcance de este documento

- **Multi-inscripción de un Estudiante a más de una Comisión** — el dominio actual liga
  `Estudiante.comision_id` a una sola Comisión (limitación ya documentada en
  `docs/plans/inc4/inc4-candidatas.md`, Iteración 1). Este incremento no la resuelve.
- **Revocar o editar una invitación ya generada** — RF-01 no lo contempla; queda para cuando
  surja una necesidad concreta.
- **Notificación automática al Estudiante con el link** — eso es RF-14 (Incremento 5,
  Notificaciones), no este incremento. Hoy el Docente comparte el link manualmente (copiar y
  pegar).

---

*Creado: 2026-09-07*
