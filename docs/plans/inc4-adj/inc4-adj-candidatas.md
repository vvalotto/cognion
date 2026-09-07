# Incremento 4-ADJ — Portal de Entrada y Validación E2E — US candidatas

> Estado documental: **Especificadas, ninguna implementada todavía.**
> Incremento no planificado originalmente en `docs/rf/PLAN_v1.md` — inserción fuera de la
> secuencia numérica 0-7 (mismo criterio que `Incremento 3-ADJ`: no se renumeran los
> Incrementos 5-7 ya mapeados a RF; ver revisión 2026-09-07 en `PLAN_v1.md`). A diferencia de
> `Incremento 3-ADJ` (deuda de tooling/arquitectura, sin impacto de usuario final), este es
> deuda de **producto** — no hay wireframe ni RF que sea dueño de la navegación de entrada del
> sistema, ver `docs/aprendizajes/HITO-9-PORTAL-DE-ENTRADA-SIN-DUENO-DE-PRODUCTO.md`.
>
> Origen: pregunta directa de Víctor tras el cierre de `BL-006` ("¿a dónde va cada usuario una
> vez que se loguea?"), que reveló que Docente, Estudiante y Administrador caen en
> `InicioPlaceholder` (`frontend/src/pages/_placeholders.tsx`, sin resolver desde `US-1.1.7`,
> Incremento 1) — sin ningún menú de navegación persistente en `AppLayout`, y sin ningún guion
> de UAT que alguna vez haya recorrido el camino real login → función, en las 4 rondas de UAT
> manual ya ejecutadas.
>
> **Ampliación de alcance 2026-09-07** (al revisar el mapa de navegación con Víctor): no existe
> ninguna pantalla para crear una Comisión ni para asignar un Docente a ella — el backend
> existe desde `US-1.1.1` (Incremento 1), pero la UI quedó explícitamente diferida "sin fecha"
> en la Iteración 2 de ese incremento (`docs/traceability/matrix.md`, nota de `US-1.1.9`) y
> nunca se retomó. Sin esto, el alta de un Estudiante real (`RF-01`) está rota de punta a punta
> en la UI — bloquea directamente la Validación E2E ya planeada en `US-4ADJ.2.1`. Se agrega al
> mismo incremento (no uno nuevo) porque cierra un prerrequisito de una iteración que ya
> estaba adentro. Detalle de las decisiones de diseño en
> `docs/design/domain/portal-entrada-modelo.md` §"Gap real detectado".
>
> La mayoría de estas US-IEDD no tiene RF asociado — mismo criterio que `US-1.1.0`/`US-2.1.2`
> (US técnicas/de producto sin fila propia en `docs/traceability/matrix.md`). Las de Comisiones
> e Invitación completan la UI de `RF-01` (ya "Validado" desde `BL-002`, vía UAT con datos
> sembrados por script) — tampoco mueven fila, cierran un gap de implementación bajo un RF ya
> cerrado, no un estado nuevo de la matriz.

---

## Por qué este incremento y no una US suelta

Se evaluó resolver el gap como un ajuste chico dentro del Incremento 5 (Notificaciones), que
es el siguiente en la secuencia de `PLAN_v1.md`. Se descartó: `PLAN_v1.md` describe ese
incremento como *"corto y deliberadamente aislado"* — valida la integración
`Actividad Evaluativa → Notificaciones` (`ADR-006`) con el menor acoplamiento posible.
Meterle diseño de UX + una pantalla nueva por rol + una UAT E2E consolidada le cambia la
naturaleza (de incremento técnico chico a incremento de UX+QA) y diluye esa aislación
deliberada — mismo criterio que ya se aplicó para separar `Incremento 3-ADJ` en vez de
mezclarlo con `Incremento 4`.

Se secuencia **antes** de Notificaciones (no después) porque es el que efectivamente entrega
un MVP demostrable — con Notificaciones el ciclo de la actividad de período abierto se
completa, pero sin portal de entrada nadie externo a esta sesión puede recorrer el sistema sin
conocer las URLs de memoria.

---

## Iteración 0 — Modelado (liviano)

Dos US-IEDD **tipo `Modelado`** (`WORKFLOW-DESARROLLO.md` §1, §2) — DoD = artefacto aprobado
explícitamente por Víctor en el comentario que cierra el Issue. Mismo patrón que
`US-4.0.1`/`US-4.0.2` (Incremento 4): primero el modelo, después el wireframe que lo visualiza
— acá no hay BC ni aggregate nuevo, así que el "modelo" es de **arquitectura de información**
(qué accesos existen, cómo se agrupan, con qué prioridad), no de dominio.

| US | Tipo | Descripción | Postcondición (DoD) | Path del artefacto |
|---|---|---|---|---|
| **US-4ADJ.0.1** | Modelado | Mapa de navegación por rol: qué accesos aparecen en el menú persistente y en cada home (Docente: Materias/Banco de Preguntas, Actividades, Analytics por alumno/por tema; Estudiante: Mis Materias/Actividades, Mi Desempeño; Administrador: Alta de Docente, Gestión de Cuentas), agrupamiento, prioridad/orden y nomenclatura — sin diseño visual todavía | Víctor aprueba el mapa de navegación en el comentario de cierre del Issue | `docs/design/domain/portal-entrada-modelo.md` |
| **US-4ADJ.0.2** | Modelado | Wireframes del portal de entrada sobre el mapa de `US-4ADJ.0.1`: home de Docente, home de Estudiante, home de Administrador, y menú de navegación persistente (visible en toda pantalla post-login vía `AppLayout`, no solo en el home) — condicionado por rol | Víctor aprueba wireframes/prototipo en el comentario de cierre del Issue | `docs/design/ux/wireframes-portal-entrada.md` + prototipo en `docs/design/ux/prototipos/` |

**Nota para el diseño:** hoy, dentro de un mismo rol, tampoco hay navegación cruzada entre
áreas top-level — p. ej. el Docente en `/materias` (Banco de Preguntas) no tiene forma de
llegar a `/actividad-evaluativa/materias` (Actividad Evaluativa) sin escribir la URL. El menú
persistente resuelve esto para todas las pantallas, no solo para el home.

**Orden:** `US-4ADJ.0.1` antes que `US-4ADJ.0.2` — el wireframe visualiza el mapa de
navegación ya aprobado, mismo orden que `US-4.0.1`→`US-4.0.2` en Incremento 4.

---

## Iteración 1 — Implementación

Dos grupos: **1a** cierra el gap real de alta de Estudiante (toca `src/`, ver más abajo) y es
prerrequisito de la Validación E2E (Iteración 2); **1b** es el portal de entrada en sí (menú +
homes), frontend puro sobre rutas ya protegidas por `RequireRole` (`US-1.1.9`).

### 1a — Alta de Estudiante y gestión de Comisiones (Administrador/Docente)

| US | Descripción | Consume | Backend | Actor |
|---|---|---|---|---|
| **US-4ADJ.1.1** | Administrador ve el listado de Comisiones de una Materia (horario, Docentes asignados, cantidad de Estudiantes inscriptos) | `GET /materias/{id}/comisiones`, `GET /comisiones/{id}/estudiantes` | **Amplía el guard de rol** de ambos endpoints — hoy `require_docente` únicamente (`US-4.2.2`), agregar `administrador` | Administrador |
| **US-4ADJ.1.2** | Administrador crea una Comisión (elige Materia + horario) | `POST /comisiones` (ya acepta rol `administrador`) | Sin cambios | Administrador |
| **US-4ADJ.1.3** | Administrador asigna un Docente a una Comisión (selecciona de la lista de usuarios rol `docente`) | `GET /usuarios?rol=docente` (`US-2.2.2`), `POST /comisiones/{id}/docentes` (ya acepta rol `administrador`) | Sin cambios | Administrador |
| **US-4ADJ.1.4** | Docente genera el link de invitación de una Comisión donde está asignado | `POST /comisiones/{id}/invitaciones` (ya acepta rol `docente`, `US-1.1.1`) | Sin cambios | Docente |

**Orden:** `US-4ADJ.1.1` primero (amplía el guard de rol, ambas pantallas de Administrador lo
necesitan) → `US-4ADJ.1.2` → `US-4ADJ.1.3` (una Comisión sin Docente asignado no sirve para
generar invitación) → `US-4ADJ.1.4` en cualquier momento después de que exista al menos una
Comisión con Docente asignado.

### 1b — Portal de entrada (menú + homes)

Todas las US consumen rutas ya protegidas por `RequireRole` — frontend puro, sin backend
nuevo.

| US | Descripción | Reemplaza / consume | Actor |
|---|---|---|---|
| **US-4ADJ.1.5** | Menú de navegación persistente en `AppLayout` — enlaces condicionados por rol (`session.rol`), visible en toda pantalla post-login | `AppLayout.tsx` (hoy sin navegación, solo header con logo/badge) | Docente, Estudiante, Administrador |
| **US-4ADJ.1.6** | Home del Docente — accesos directos a Banco de Preguntas, Actividades, Analytics | Reemplaza `InicioPlaceholder` para rol `docente` | Docente |
| **US-4ADJ.1.7** | Home del Estudiante — accesos directos a Mis Actividades, Mi Desempeño | Reemplaza `InicioPlaceholder` para rol `estudiante` | Estudiante |
| **US-4ADJ.1.8** | Home del Administrador — accesos directos a Comisiones, Alta de Docente, Gestión de Cuentas | `RUTA_POST_LOGIN[administrador]` pasa de `/docentes/nuevo` directo a `/` (home real, mismo patrón que Docente/Estudiante) | Administrador |

**Orden:** `US-4ADJ.1.5` primero (el menú depende del wireframe de navegación, pero ninguna de
las 3 US de home depende de las otras 2 — pueden ir en paralelo después). Las 3 homes sí
dependen de `US-4ADJ.1.5` si el wireframe integra menú + contenido de home en una sola
pantalla (a confirmar en el wireframe de la Iteración 0). `1b` no depende de `1a` para
implementarse (son pantallas distintas), pero la Validación E2E de la Iteración 2 sí necesita
`1a` completa.

---

## Iteración 2 — Validación E2E del MVP

Una única US-IEDD **tipo `UAT`/verificación** (no genera código de producción) — DoD = guion
ejecutado sin hallazgos 🔴 Bloqueantes, confirmado por Víctor.

| US | Tipo | Descripción | Postcondición (DoD) |
|---|---|---|---|
| **US-4ADJ.2.1** | UAT/Verificación | Guion E2E consolidado que atraviesa los 4 BC en una sola corrida, **arrancando desde un login real y navegando por clic** (no URLs tipeadas, mismo gap señalado en `HITO-9` L-9.2), **incluida el alta real del Estudiante por UI** (mismo gap cerrado en la Iteración 1a — hasta ahora toda UAT sembraba la Comisión/invitación por script): Administrador crea una Comisión y asigna un Docente → Docente genera el link de invitación → Estudiante se registra con ese link; Docente crea materia → carga preguntas (opción múltiple y V/F) → crea actividad de período abierto; Estudiante inicia sesión → rinde la evaluación (con pausa/reanudación) → finaliza y ve su revisión → ve su propio desempeño (Analytics); Docente ve el desempeño de ese alumno y la tasa de error por tema | Guion ejecutado en navegador real (Claude Browser o Chrome), sin hallazgos 🔴 Bloqueantes, evidencia guardada en `quality/reports/uat/inc4-adj/`, confirmado por Víctor |

Este guion es, en los hechos, la primera UAT del proyecto que ejercita el **camino completo**
del MVP (crear contenido → rendir → revisar → analizar) en una sola corrida — hasta ahora cada
incremento validó su propio flujo de forma aislada (`quality/reports/uat/inc1/` a `inc4/`).

---

## DoD del Incremento

Un Administrador puede dar de alta un Estudiante real de punta a punta desde la UI (Comisión →
Docente asignado → invitación → registro); cualquier Docente, Estudiante o Administrador
autenticado puede navegar, por clic, desde el login hasta cualquier función de su rol, sin
conocer ninguna URL de memoria; y existe al menos un guion de prueba que valida el flujo
completo del MVP (alta de Estudiante → crear contenido → rendir → revisar → analizar) en una
sola corrida, arrancando desde el login real.

---

## Próximos pasos

1. ~~Revisar esta propuesta de candidatas con Víctor.~~ Hecho — 2026-09-07, incluida la
   ampliación de alcance de Comisiones/Invitación.
2. ~~Crear Milestone GitHub `Incremento 4-ADJ — Portal de Entrada y Validación E2E` + Issues
   para `US-4ADJ.0.1` y `US-4ADJ.0.2`.~~ Hecho — Milestone
   [#12](https://github.com/vvalotto/cognion/milestone/12), Issues
   [#261](https://github.com/vvalotto/cognion/issues/261) (`US-4ADJ.0.1`) y
   [#262](https://github.com/vvalotto/cognion/issues/262) (`US-4ADJ.0.2`).
3. Ejecutar el mapa de navegación (`US-4ADJ.0.1`, ya redactado en
   `docs/design/domain/portal-entrada-modelo.md`, incluida la ampliación de Comisiones) y los
   wireframes (`US-4ADJ.0.2`), cada uno con aprobación explícita de Víctor.
4. Crear Issues y `docs/specs/inc4-adj/US-4ADJ.1.K.md` de la Iteración 1 (1a: `1.1` a `1.4`;
   1b: `1.5` a `1.8`).
5. Implementar Iteración 1a (`US-4ADJ.1.1` → `1.2` → `1.3` → `1.4`, orden secuencial) y
   luego/en paralelo Iteración 1b (`US-4ADJ.1.5` primero, `1.6`/`1.7`/`1.8` en cualquier orden
   entre sí).
6. Crear Issue y spec de `US-4ADJ.2.1`, ejecutar la UAT E2E consolidada (requiere 1a y 1b
   completas).
7. Cerrar baseline (`BL-007`) siguiendo `WORKFLOW-DESARROLLO.md` §7.
