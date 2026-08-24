# Plan de Implementación: US-ADJ-01 - Alinear visualmente Banco de Preguntas con el prototipo

**Patrón:** React 19 + TypeScript + Vite (frontend puro, sin capas Clean Architecture)
**Producto:** cognion-frontend
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-22
**Tiempo real (tracker):** 55 min (todas las fases, 0 a 8)

Fuente de verdad UX: `docs/design/ux/prototipos/banco-preguntas-carga-filtrado.html` (colores,
radii, spacing ya definidos ahí — se traducen a Tailwind, no se inventan valores nuevos).

## Componentes a Implementar

### 1. Primitivas nuevas en `components/ui/`

- [x] `frontend/src/components/ui/card.tsx`
  - `Card`: contenedor `rounded-lg border border-border bg-card shadow-sm` (equivalente a
    `--radius: 10px` + `--shadow` del prototipo)
  - `CardContent`: wrapper de padding interno (`p-5`/`p-6` según pantalla)
  - Sigue el mismo patrón shadcn de `button.tsx` (función + `cn()`, sin lógica de negocio)
- [x] `frontend/src/components/ui/badge.tsx`
  - `Badge` con `cva`: variantes `tipo-om` (azul), `tipo-vf` (violeta), `nivel-alto` (rojo),
    `nivel-medio` (ámbar), `nivel-bajo` (verde) — colores Tailwind ad hoc (`red-50/800`,
    `amber-50/800`, `green-50/800`, `blue-50/800`, `violet-50/800`), sin nuevos tokens CSS en
    `index.css` (no lo amerita, mismo criterio que el resto de `components/ui/`)
- [x] `frontend/src/components/ui/button.tsx` (extender, no romper lo existente)
  - Agregar variante `destructive-solid`: `bg-destructive text-white hover:bg-destructive/90`
  - **No tocar** la variante `destructive` existente (soft, `bg-destructive/10`) — la usan
    `ResetearPassword.tsx` y otras pantallas de Identidad ya aprobadas; cambiarla sería
    ensanchar el alcance fuera de Banco de Preguntas
- [x] `frontend/src/components/Breadcrumb.tsx`
  - Componente liviano propio (no shadcn): recibe `items: { label: string; to?: string }[]`,
    renderiza segmentos separados por "›", el último sin link y en `font-medium` (clase
    `.breadcrumb .current` del prototipo)

### 2. Pantallas — aplicar Card/Badge/Breadcrumb sin cambiar comportamiento

- [x] `frontend/src/pages/Materias.tsx`
  - Breadcrumb "Banco de preguntas › Materias"
  - Grid de `Card` por materia (ícono, nombre, "N preguntas activas") en vez de `<button>` plano
  - Card "+ Nueva materia" con borde punteado, "+" centrado (mantiene semántica de botón)
- [x] `frontend/src/pages/NuevaMateria.tsx`
  - Breadcrumb "Banco de preguntas › Materias › Nueva materia"
  - Formulario envuelto en `Card`
- [x] `frontend/src/pages/Banco.tsx`
  - Breadcrumb "Banco de preguntas › Materias › {nombre materia}"
  - Filtros envueltos en `Card`; tabla envuelta en `Card`
  - Columna Tipo con `Badge` (`tipo-om`/`tipo-vf`); columnas Dificultad/Importancia con
    `Badge` (`nivel-alto`/`nivel-medio`/`nivel-bajo`)
  - Botón "Eliminar" de cada fila: variante `destructive-solid` (hoy outline)
- [x] `frontend/src/pages/NuevaPreguntaTipo.tsx`
  - Breadcrumb "Banco de preguntas › {materia} › Nueva pregunta"
  - Cards de selección de tipo con el estilo `tipo-card` (borde 2px, centrado, ícono grande)
- [x] `frontend/src/pages/NuevaPreguntaOpcionMultiple.tsx`
  - Breadcrumb, formulario en `Card`; sin cambios en la lógica de opciones dinámicas
    (resaltado de la opción correcta ya existe, verificar que siga con el mismo criterio
    visual del prototipo — borde+fondo `success`)
- [x] `frontend/src/pages/NuevaPreguntaVerdaderoFalso.tsx`
  - Breadcrumb, formulario en `Card`; choice V/F con estilo de toggle (ya implementado,
    verificar contra prototipo)
- [x] `frontend/src/pages/EditarPregunta.tsx`
  - Mismo tratamiento que las pantallas de carga, según el tipo concreto de la pregunta
- [x] `frontend/src/pages/EliminarPregunta.tsx`
  - Botón "Sí, eliminar" con variante `destructive-solid`
  - Alert con estilo `warning` (ámbar) en vez de `destructive` (rojo) — el prototipo usa
    `.alert.warning` para este caso, no `.alert.destructive`

### 3. Ajuste de tests existentes

- [x] Revisar `Materias.test.tsx`, `NuevaMateria.test.tsx`, `Banco.test.tsx`,
  `NuevaPreguntaTipo.test.tsx`, `NuevaPreguntaOpcionMultiple.test.tsx`,
  `NuevaPreguntaVerdaderoFalso.test.tsx`, `EditarPregunta.test.tsx`, `EliminarPregunta.test.tsx`
  — ajustar únicamente los selectors que dependan de la jerarquía DOM que cambia (queries por
  texto/rol no deberían romperse si el copy no cambia)

**Estado:** 12/12 tareas completadas
