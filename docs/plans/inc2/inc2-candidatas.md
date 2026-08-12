# Incremento 2 — Banco de Preguntas — US candidatas

> Estado documental: **Iteración 0 — Modelado cerrada (2026-07-31).** US-2.0.1 (modelo de
> dominio, Issue #38) y US-2.0.2 (wireframes de carga/filtrado, Issue #39) aprobadas por
> Víctor. Esta tabla ya puede usarse como base para elaborar las US-IEDD formales de la
> Iteración 1 (WORKFLOW-DESARROLLO.md §3, paso 1) — revisarla contra el modelo y los
> wireframes aprobados antes de crear los Issues y specs, por si algo se ajustó respecto de lo
> anticipado acá.
>
> Fuente: `docs/rf/PLAN_v1.md` §Incremento 2, `docs/rf/RF_v1.md` (RF-03, RF-04, RF-05, RF-06),
> `docs/design/domain/BC-banco-preguntas-modelo.md`,
> `docs/design/ux/wireframes-banco-preguntas.md`.

---

## Iteración 0 — Modelado

Dos US-IEDD **tipo `Modelado`** (WORKFLOW-DESARROLLO.md §1, §2) — DoD = artefacto aprobado
explícitamente por Víctor en el comentario que cierra el Issue.

| US | Tipo | Descripción | Postcondición (DoD) | Path del artefacto |
|---|---|---|---|---|
| **US-2.0.1** | Modelado | Event storming BC Banco de Preguntas: aggregates (`Materia`, `Banco`, `PreguntaPlantillaOpcionMultiple`, `PreguntaPlantillaVerdaderoFalso`), eventos de dominio (`MateriaCreada`, `BancoCreado`, `PreguntaCargada`, `PreguntaEditada`, `PreguntaEliminada`), comandos, invariantes (INV-BP-00 a INV-BP-04) | Víctor aprueba el modelo en el comentario de cierre del Issue | `docs/design/domain/BC-banco-preguntas-modelo.md` |
| **US-2.0.2** | Modelado | Wireframes de carga (Opción Múltiple / Verdadero-Falso, diferenciados) y filtrado del banco (por unidad temática, tema, dificultad, importancia) | Víctor aprueba los wireframes/prototipo en el comentario de cierre del Issue | `docs/design/ux/wireframes-banco-preguntas.md` + prototipo en `docs/design/ux/prototipos/` |

~~US-2.0.1~~ Cerrada 2026-07-31, Issue #38. ~~US-2.0.2~~ Cerrada 2026-07-31, Issue #39.

Al cerrar la Iteración 0: actualizar `docs/traceability/matrix.md` §4 — los escenarios RNF
que este incremento aborda pasan de *Planificado* a *Especificado* (WORKFLOW-DESARROLLO.md
§3, paso 0e).

---

## Iteración 1 — RF-04, RF-05, RF-06: carga, tipos, metadatos y filtrado

Formato compacto (mismo precedente usado en `inc1-candidatas.md`, Iteración 1 de Identidad).
Todas del BC Banco de Preguntas salvo **US-2.1.2**, que toca BC Identidad (refactor de
`Comisión.materia`).

### Backend

| US | Descripción | Comando | Evento(s) | Actor | Invariantes clave | Precondición → Postcondición |
|---|---|---|---|---|---|---|
| **US-2.1.1** | Docente da de alta una materia; se crea su banco vacío en el mismo flujo | `CrearMateria(nombre)`, `CrearBanco(materia_id)` | `MateriaCreada`, `BancoCreado` | Docente | `nombre` único (INV-BP-00); un `Banco` por `Materia` (INV-BP-01) | Docente autenticado, nombre no usado → `Materia` y `Banco` persistidos |
| **US-2.1.2** *(técnica, BC Identidad)* | `Comisión.materia` deja de ser `string` libre y referencia la `Materia` de BC Banco de Preguntas por puerto (`entities/ports/`) — sin imports directos entre BCs | — (refactor, sin comando de dominio nuevo) | — | — | `Comisión` existente conserva su `materia_id` tras la migración; ninguna comisión queda con referencia inválida | `Materia` ya existe con al menos las 2 materias conocidas (depende de US-2.1.1) → `Comisión.materia_id` referencia `Materia` por puerto, tests de Identidad siguen en verde |
| **US-2.1.3** | Docente carga una pregunta de opción múltiple en un banco | `CargarPreguntaOpcionMultiple(banco_id, texto, opciones, unidad, tema, dificultad, importancia)` | `PreguntaCargada` | Docente | Mínimo 2 opciones (INV-BP-03); exactamente una `es_correcta` (INV-BP-02) | `Banco` existe → `PreguntaPlantillaOpcionMultiple` persistida, `activa = true` |
| **US-2.1.4** | Docente carga una pregunta verdadero/falso en un banco | `CargarPreguntaVerdaderoFalso(banco_id, texto, respuesta_correcta, unidad, tema, dificultad, importancia)` | `PreguntaCargada` | Docente | — | `Banco` existe → `PreguntaPlantillaVerdaderoFalso` persistida, `activa = true` |
| **US-2.1.5** | Docente edita una pregunta existente (según su tipo concreto) | `EditarPregunta(pregunta_id, ...)` | `PreguntaEditada` | Docente | Mismas invariantes de INV-BP-02/03 si es Opción Múltiple; no se puede cambiar el tipo de la pregunta | Pregunta existe y `activa = true` → campos actualizados |
| **US-2.1.6** | Docente elimina (baja lógica) una pregunta | `EliminarPregunta(pregunta_id)` | `PreguntaEliminada` | Docente | Baja lógica, no física (INV-BP-04) — preserva historial de sesiones pasadas | Pregunta existe y `activa = true` → `activa = false`, no vuelve a aparecer en `FiltrarBanco` |
| **US-2.1.7** | Docente filtra el banco de una materia por cualquier combinación de metadatos | `FiltrarBanco(materia_id, unidad?, tema?, dificultad?, importancia?)` (query) | — | Docente | Solo devuelve preguntas `activa = true` | `Banco` existe → lista de preguntas que matchean todos los filtros provistos |

**Orden de implementación:** US-2.1.1 primero (crea `Materia`/`Banco`, precondición de todo lo
demás). US-2.1.2 puede ir en paralelo o justo después — depende de que exista al menos una
`Materia`, no del resto de la iteración. US-2.1.3/2.1.4 antes que 2.1.5/2.1.6 (no se puede
editar/eliminar lo que no existe). US-2.1.7 al final, sobre datos ya cargados.

### Frontend

> Mismo criterio adoptado en Identidad (`docs/plans/PLAN-CM.md` §7, decisión 2026-07-24): la
> Baseline no cierra backend-only. El wireframe completo ya está aprobado
> (`docs/design/ux/wireframes-banco-preguntas.md`, US-2.0.2/Issue #39), así que el frontend se
> planifica dentro de esta misma Iteración 1 en vez de diferirlo a una Iteración 2 separada,
> como sí hizo falta en Identidad (ahí la necesidad de un frontend explícito surgió recién
> después del backend).

| US | Descripción | Pantallas (`wireframes-banco-preguntas.md`) | Backend consumido | Depende de |
|---|---|---|---|---|
| **US-2.1.8** | Infraestructura de frontend específica del BC: rutas de banco de preguntas, cliente API de este dominio (reutiliza el cliente HTTP con JWT de US-1.1.6) | Sin pantalla propia — soporte técnico | — | US-2.1.1 a US-2.1.7 |
| **US-2.1.9** | Docente ve el listado de materias y da de alta una nueva | §2.1 `#materias`, §2.2 `#nueva-materia` | `POST /materias` (US-2.1.1) | US-2.1.8 |
| **US-2.1.10** | Docente ve y filtra el banco de preguntas de una materia | §2.3 `#banco` | `GET /bancos/{id}/preguntas?filtros` (US-2.1.7) | US-2.1.8 |
| **US-2.1.11** | Docente carga una pregunta (elige tipo, completa el formulario correspondiente) | §2.4 `#nueva-pregunta-tipo`, §2.5 `#nueva-pregunta-om`, §2.6 `#nueva-pregunta-vf` | `POST /preguntas/opcion-multiple`, `POST /preguntas/verdadero-falso` (US-2.1.3, US-2.1.4) | US-2.1.10 |
| **US-2.1.12** | Docente edita una pregunta existente | §2.7 `#editar-pregunta` | `PUT /preguntas/{id}` (US-2.1.5) | US-2.1.10 |
| **US-2.1.13** | Docente elimina (baja lógica) una pregunta, con confirmación previa | §2.8 `#eliminar-pregunta` | `DELETE /preguntas/{id}` (US-2.1.6) | US-2.1.10 |

**Orden de implementación:** US-2.1.8 primero (bloquea al resto). US-2.1.9 antes que
US-2.1.10 (necesita al menos una materia con banco para tener algo que listar/filtrar).
US-2.1.11 antes que 2.1.12/2.1.13 (no se edita/elimina lo que no existe).

---

## Iteración 2 — RF-03: gestión de cuentas por administrador

BC Identidad, no Banco de Preguntas — agrupada en este incremento por el plan original
(`PLAN_v1.md`). El dominio ya está parcialmente modelado como "Diferidos" en
`docs/design/domain/BC-identidad-modelo.md` §3 y §9 (`ResetearPassword`, `CambiarPassword`,
`CuentaBloqueada`/RF-19) — probablemente **no** necesita una nueva US de event storming, pero
sí una **US-Modelado de wireframes** nueva (listado/gestión de cuentas, reset de contraseña),
ya que `wireframes-identidad.md` §4 la deja explícitamente fuera de alcance. No se detalla
todavía — se retoma al cerrar esta Iteración 1, siguiendo el mismo ciclo (WORKFLOW-DESARROLLO.md
§3, paso 0).

---

## DoD del Incremento (hito, `PLAN_v1.md`)

> El docente arma y mantiene el banco de preguntas completo, filtrable por
> materia/unidad/tema/dificultad/importancia. El administrador resuelve problemas de cuentas
> sin depender del docente.

Se verifica de punta a punta en UAT (Capa 1 pytest + Capa 2 HTTP) al cierre del incremento,
según `PROCEDIMIENTO-UAT.md` — no basta con que cada US individual pase sus propios tests.

*(RF-07, migración desde PDF, pospuesta al Incremento 7 — no bloquea el cierre de este
incremento.)*

---

## Próximos pasos

1. ~~Ejecutar Iteración 0 — Modelado (event storming + wireframes) y obtener aprobación
   explícita de Víctor.~~ Cerrada 2026-07-31 (US-2.0.1, Issue #38; US-2.0.2, Issue #39).
2. Revisar esta tabla de candidatas contigo antes de crear Issues/specs.
3. Crear GitHub Issues (Milestone `Incremento 2 — Banco de Preguntas`, labels `us-iedd`,
   `incremento-2`) y `docs/specs/inc2/US-2.1.K.md` por cada US aprobada de la Iteración 1
   (backend US-2.1.1 a 2.1.7, frontend US-2.1.8 a 2.1.13).
4. Actualizar `docs/traceability/matrix.md`: RF-04, RF-05, RF-06 pasan de *Planificado* a
   *Especificado*, completando la columna US-IEDD.
5. Implementar Iteración 1 (backend primero, frontend después, mismo orden que Identidad).
6. Al cerrar la Iteración 1: modelar la Iteración 2 (RF-03) — wireframes de gestión de
   cuentas, y confirmar si el event storming ya existente en `BC-identidad-modelo.md` alcanza
   o necesita revisión.
