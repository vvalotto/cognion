# US-ADJ-01: Alinear visualmente las pantallas de Banco de Preguntas con el prototipo aprobado

**Estado**: `Especificada`
**Iteracion / Sprint**: `SP-ADJ` (sin incremento asignado todavía — ver `HITO-4`)
**Tipo**: `refactor frontend`
**Agregado principal afectado**: — (sin cambios de dominio, solo presentación)
**Bounded Context**: Banco de Preguntas (frontend)

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **que las pantallas de Banco de Preguntas se vean como el prototipo que Víctor ya
aprobó** (cards con sombra, tags de color por tipo/dificultad/importancia, breadcrumb, botón
de eliminar sólido)
para **tener la misma calidad visual e institucional que ya tienen las pantallas de
Identidad, y poder distinguir de un vistazo la dificultad/importancia de cada pregunta**.

---

## Contexto del dominio

### Problema

Detectado en el UAT manual de cierre de la Iteración 1 (`HITO-4`,
`quality/reports/uat/inc2/evidencia.md`): las pantallas `Materias.tsx`, `Banco.tsx`,
`NuevaMateria.tsx`, `NuevaPreguntaTipo.tsx`, `NuevaPreguntaOpcionMultiple.tsx`,
`NuevaPreguntaVerdaderoFalso.tsx`, `EditarPregunta.tsx` y `EliminarPregunta.tsx` cumplen los
criterios de aceptación funcionales de `US-2.1.9` a `US-2.1.13` y pasan su suite de tests,
pero no reproducen el lenguaje visual de
`docs/design/ux/prototipos/banco-preguntas-carga-filtrado.html`: falta breadcrumb, tarjetas
con sombra, tags de color, subtítulo de página y el botón "Eliminar" sólido.

Causa raíz (`HITO-4`): `frontend/src/components/ui/` nunca se extendió más allá de
`button.tsx`/`input.tsx`/`label.tsx` (los mismos tres que alcanzaban para Identidad) — las
primitivas nuevas que el prototipo de Banco de Preguntas introduce (card, tabla envuelta,
badge/tag, breadcrumb) no tienen un componente compartido y cada pantalla las reimplementó (o
directamente las omitió) con Tailwind ad hoc.

### Modelo involucrado

Sin cambios de dominio — US puramente de presentación (frontend). No hay Aggregate, Value
Object, Domain Event, Port ni Command afectados.

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Componente nuevo | `Card` (shadcn) | Contenedor con sombra + borde + radius para formularios, cards de materia y tabla |
| Componente nuevo | `Badge` (shadcn, o equivalente propio) | Tag de color para Tipo / Dificultad / Importancia |
| Componente nuevo | `Breadcrumb` (propio, liviano) | Ruta de navegación en cabecera de cada pantalla |

---

## Especificacion del comportamiento

### Precondicion

- `US-2.1.9` a `US-2.1.13` implementadas y mergeadas (esta US no agrega comportamiento nuevo,
  solo re-viste pantallas existentes).
- Prototipo `docs/design/ux/prototipos/banco-preguntas-carga-filtrado.html` sigue siendo la
  fuente de verdad UX — sin cambios de diseño respecto a lo ya aprobado.

### Postcondicion

- Cada pantalla listada en "Artefactos a modificar" reproduce, verificado visualmente
  (screenshot en navegador real contra el prototipo, no solo revisión de código):
  - Breadcrumb con la ruta correspondiente.
  - Tarjetas con sombra (`Card`) para formularios, cards de materia y tabla del banco.
  - Tags de color por Tipo (azul opción múltiple / violeta V-F) y por
    Dificultad/Importancia (rojo alto / ámbar medio / verde bajo).
  - `page-subtitle` bajo cada título.
  - Botón "Eliminar" con fondo sólido destructivo (no outline).
- Ningún criterio de aceptación funcional de `US-2.1.9` a `US-2.1.13` cambia — mismos
  endpoints, mismas validaciones, mismas rutas. Es un refactor de presentación puro.
- Suite de tests existente (Vitest + RTL) sigue en verde; se ajustan los tests que dependían
  de estructura DOM que cambia (p. ej. selectors por texto/rol siguen siendo válidos si no se
  cambia el copy, pero puede haber que ajustar queries si cambia la jerarquía de elementos).

### Invariantes

| ID | Invariante |
|----|------------|
| — | Sin invariantes de dominio — US de presentación pura. |

---

## Criterios de aceptacion

```gherkin
Feature: Alineación visual del Banco de Preguntas con el prototipo aprobado (US-ADJ-01)

  Scenario: Listado de materias con el estilo del prototipo
    Given un Docente autenticado en "Materias"
    When la pantalla carga
    Then cada materia se muestra en una tarjeta con sombra e ícono
    And la tarjeta "+ Nueva materia" se muestra punteada con el "+" centrado
    And el breadcrumb muestra "Banco de preguntas › Materias"

  Scenario: Banco de preguntas con tags de color
    Given un Docente autenticado viendo el banco de una materia
    When la tabla de preguntas carga
    Then el Tipo de cada pregunta se muestra con un tag de color (azul opción múltiple, violeta V/F)
    And la Dificultad y la Importancia se muestran con tags de color (rojo alto, ámbar medio, verde bajo)
    And el botón "Eliminar" de cada fila tiene fondo sólido destructivo

  Scenario: Sin regresión funcional
    Given la suite de tests existente de Banco de Preguntas
    When se ejecuta después de este ajuste
    Then todos los tests siguen pasando sin cambios en los criterios de aceptación de US-2.1.9 a US-2.1.13
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] Sí — agrega primitivas nuevas a `components/ui/` (`Card`, `Badge`, `Breadcrumb`), pero
  sigue el patrón ya establecido por `button.tsx`/`input.tsx`/`label.tsx` (shadcn) — no
  amerita un ADR nuevo, es la aplicación consistente de una decisión ya tomada.
- [x] No — sin cambios de capas `entities`/`use_cases`/`interface_adapters`/`frameworks` del
  backend ni de contratos de API.

**Capa(s) afectadas:**
- [x] Frontend — `components/ui/` (componentes nuevos) + las 8 pantallas de Banco de Preguntas
- [ ] Backend — sin cambios

---

## Fuente de verdad UX

`docs/design/ux/prototipos/banco-preguntas-carga-filtrado.html` (ya aprobado, sin cambios de
diseño en esta US) y `docs/design/ux/wireframes-banco-preguntas.md`. Verificación de cierre:
comparación visual en navegador real contra el prototipo, no solo lectura de código —
mismo criterio que `HITO-4` recomienda incorporar al gate de diseño UX.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/components/ui/card.tsx` | Nuevo — componente `Card` (shadcn) |
| `frontend/src/components/ui/badge.tsx` | Nuevo — componente `Badge`/tag de color |
| `frontend/src/components/Breadcrumb.tsx` | Nuevo — breadcrumb liviano propio (o `components/ui/breadcrumb.tsx` si se adopta el de shadcn) |
| `frontend/src/pages/Materias.tsx` | Cards con sombra, ícono, breadcrumb, subtítulo |
| `frontend/src/pages/NuevaMateria.tsx` | `Card` envolviendo el formulario, breadcrumb, hint de nombre único |
| `frontend/src/pages/Banco.tsx` | Filtros en `Card`, tabla envuelta en `Card`, tags de color, breadcrumb |
| `frontend/src/pages/NuevaPreguntaTipo.tsx` | Cards de selección de tipo con el estilo `tipo-card` del prototipo |
| `frontend/src/pages/NuevaPreguntaOpcionMultiple.tsx` | `Card` de formulario, filas de opción con resaltado de la correcta |
| `frontend/src/pages/NuevaPreguntaVerdaderoFalso.tsx` | `Card` de formulario, choice V/F con el estilo de toggle del prototipo |
| `frontend/src/pages/EditarPregunta.tsx` | Mismo ajuste que las pantallas de carga, según tipo |
| `frontend/src/pages/EliminarPregunta.tsx` | Botón "Sí, eliminar" con fondo sólido, alert con el estilo `warning` del prototipo |

---

## Referencias

- Relacionada con: `US-2.1.9` a `US-2.1.13` (US que esta US re-viste, sin tocar su
  comportamiento), `HITO-4` (hallazgo que origina esta US)
- Candidatas: sin incremento asignado — se decide después de completar el UAT de cierre de la
  Iteración 1 (`quality/reports/uat/inc2/evidencia.md`)

---

*Basado en el template de `docs/specs/inc2/US-2.1.13.md` — adaptado a capas
`entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`). US de ajuste (`SP-ADJ`,
`docs/plans/PLAN-CM.md` §12) — sin Issue de GitHub ni branch hasta que se decida el
incremento de implementación.*
