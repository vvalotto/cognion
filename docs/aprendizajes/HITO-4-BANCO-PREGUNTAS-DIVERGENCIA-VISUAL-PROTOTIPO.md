# HITO-4 — Las pantallas de Banco de Preguntas no respetan visualmente el prototipo aprobado

> Estado documental: evidencia
> Registra un hallazgo de aprendizaje del ensayo IEDD en Cognion.
> No reemplaza a las fuentes vigentes (ADRs, arquitectura, specs).

| Campo | Valor |
|-------|-------|
| **Documento** | HITO-4 — hallazgo de UX en UAT de cierre de la Iteración 1, Incremento 2 |
| **Fecha** | 2026-08-17 |
| **Incremento / contexto** | Incremento 2 (Banco de Preguntas), UAT manual en navegador real de cierre de la Iteración 1 (`US-2.1.1` a `US-2.1.13`) |
| **Relacionado** | `docs/design/ux/prototipos/banco-preguntas-carga-filtrado.html`, `docs/design/ux/wireframes-banco-preguntas.md`, `US-2.1.8` a `US-2.1.13`, `quality/reports/uat/inc2/evidencia.md` |

---

## Contexto

Cerrada funcionalmente la Iteración 1 del Incremento 2 (Capa 1 y Capa 2 del UAT en verde,
recorrido funcional previo sin errores), Víctor hizo su propia pasada manual en navegador real
sobre las pantallas de Banco de Preguntas (Materias, Nueva materia, Banco/filtrado, Nueva
pregunta, Editar, Eliminar). Detectó que el resultado visual no coincide con el prototipo
aprobado que sirvió de fuente de verdad UX para esas mismas US.

---

## Hallazgo / Análisis

Comparando `docs/design/ux/prototipos/banco-preguntas-carga-filtrado.html` contra el código
real (`frontend/src/pages/Materias.tsx`, `Banco.tsx`, `NuevaMateria.tsx` y afines), la
divergencia es sistemática, no un detalle suelto en una pantalla:

- **Sin breadcrumb** (`Banco de preguntas › Materias › [pantalla]`) en ninguna pantalla real,
  salvo un rastro mínimo de un nivel en `NuevaMateria.tsx`.
- **Sin tarjetas con sombra** (`.form-card`, `.materia-card`, `.table-wrap` del prototipo) —
  el código real usa bordes planos sin `box-shadow`, sin el padding generoso del prototipo.
- **Cards de Materia sin ícono** ni el hover que resalta el borde en azul primario; la card
  "Nueva materia" no reproduce el estilo punteado con "+" centrado.
- **Filtros sin card contenedora** — sueltos en un `flex`, sin la tarjeta blanca con sombra
  del prototipo.
- **Tabla sin tags de color** — el prototipo colorea Tipo (azul/violeta) y
  Dificultad/Importancia (rojo/ámbar/verde) con pills redondeados; el código real los muestra
  como texto plano sin distinción visual.
- **Botón "Eliminar" no es sólido** — el prototipo lo pinta con fondo rojo relleno; el real es
  outline con texto rojo.
- **Sin `page-subtitle`** — ninguna pantalla real reproduce la línea explicativa que acompaña
  cada título en el prototipo.

**Causa raíz:** `frontend/src/components/ui/` solo tiene `button.tsx`, `input.tsx` y
`label.tsx` (shadcn) — los mismos tres que ya alcanzaban para las pantallas de Identidad
(`US-1.1.6`+), que sí respetan su prototipo porque lo hacen con ese patrón consistente. El
prototipo de Banco de Preguntas introduce primitivas nuevas (card con sombra, tabla envuelta,
tags de color, breadcrumb) que nunca se agregaron a `components/ui/` — cada pantalla de
`US-2.1.9` a `US-2.1.13` se escribió con Tailwind ad hoc en vez de extender el mismo patrón
de componentes compartidos.

El gate de diseño UX de `CLAUDE.md` ("Ninguna línea de `frontend/` sin artefacto aprobado en
`docs/design/ux/`") se cumplió a nivel procedimental — todas las specs de estas US listan el
prototipo en su campo "Fuente de verdad UX" — pero el gate no incluye una verificación visual
explícita del resultado contra el prototipo antes de mergear. El código puede satisfacer los
criterios de aceptación funcionales (Gherkin) y los tests (Vitest, que no verifican estilos
computados) y aun así divergir visualmente sin que nada lo detecte hasta que un humano lo mira
en el navegador.

---

## Aprendizaje(s)

- **L-4.1:** Referenciar el prototipo en la spec no garantiza fidelidad visual — el gate de
  diseño UX necesita un paso de verificación visual explícito (comparación lado a lado o
  checklist de elementos del prototipo) antes de cerrar una US de frontend, no solo la cita
  del artefacto de origen.
- **L-4.2:** Cuando un prototipo introduce primitivas de diseño nuevas (card con sombra, tags
  de color, breadcrumb, tabla envuelta), la primera US que las necesita debe extender
  `frontend/src/components/ui/` con el componente shadcn correspondiente en vez de
  reimplementar con Tailwind ad hoc — es el mismo patrón que ya funcionó para
  Button/Input/Label en Identidad, y su ausencia es la causa raíz de esta divergencia.
- **L-4.3:** Vitest con React Testing Library no detecta este tipo de gap — verifica
  comportamiento y contenido, no fidelidad visual contra un diseño de referencia. El UAT
  manual en navegador real (`feedback_uat_navegador_real`) sigue siendo, otra vez, el único
  paso del proceso que lo detecta.

---

## Relación con la hipótesis del ensayo

Confirma con mayor solidez §5.5 de `docs/iedd/04-Hipotesis_Ensayo_IA_Ingenieria_Human_In_The_Loop.md`
("Se confirmó, con mayor solidez, la necesidad estructural del human-in-the-loop"): el código
generado cumplió especificación funcional y suite de tests automatizada de punta a punta (270
backend, 103 frontend, todos en verde) y aun así se alejó sistemáticamente de un artefacto de
diseño ya aprobado — un gap que solo la revisión visual humana detectó, igual que el gap de
CORS/cascada CSS de `US-1.1.9` (`feedback_uat_navegador_real`). El patrón se repite: la
automatización certifica *comportamiento*, no *fidelidad al diseño*.

---

## Resumen de Aprendizajes

| ID | Aprendizaje | Impacto |
|----|-------------|---------|
| L-4.1 | El gate de diseño UX necesita verificación visual explícita, no solo cita del prototipo en la spec | Proceso |
| L-4.2 | Primitivas de diseño nuevas del prototipo deben materializarse como componente compartido (`components/ui/`) en la primera US que las usa | Arquitectura / Workflow |
| L-4.3 | Vitest/RTL no detecta divergencia visual — el UAT en navegador real sigue siendo insustituible para esto | Quality |

---

*Creado: 2026-08-17*
