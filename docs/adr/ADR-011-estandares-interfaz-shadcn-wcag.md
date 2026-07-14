# ADR-011 — shadcn/ui + Tailwind y WCAG A como estándares de interfaz (vs. librería de componentes propia o cerrada)

**Estado:** Aceptado
**Fecha:** 2026-07-08

---

## Contexto

El escenario de calidad de Usabilidad en `RNF_v1.md` exige una interfaz responsive funcional en
cualquier dispositivo/browser vigente, y legibilidad completa cuando se proyecta en el aula
durante una sesión en vivo. El equipo es unipersonal, sin diseñador dedicado.

## Opciones Consideradas

- **Librería de componentes propia desde cero** — descartada: el esfuerzo de construir y
  mantener un sistema de componentes no se justifica para un equipo unipersonal.
- **Material UI / Chakra UI** (u otra librería con componentes empaquetados) — descartada:
  imponen un lenguaje visual propio, más difícil de personalizar para el criterio de
  legibilidad en proyección que exige el escenario de Usabilidad.
- **shadcn/ui sobre Tailwind CSS** — componentes copiados al proyecto (no una dependencia
  opaca), basados en Radix UI. Elegida.

## Decisión

shadcn/ui (preset nova) como librería de componentes base, sobre Tailwind CSS, cumpliendo como
mínimo WCAG nivel A.

## Justificación

shadcn/ui entrega componentes accesibles por defecto (basados en Radix UI primitives) que se
copian al proyecto en `frontend/src/components/` en vez de instalarse como dependencia opaca de
`node_modules` — esto permite ajustar el criterio de legibilidad en proyección (tamaño de
fuente, contraste) directamente sobre el código del componente, sin pelear contra los límites de
una librería cerrada. WCAG nivel A es el mínimo razonable para un contexto académico sin
usuarios con necesidades de accesibilidad reportadas hasta el momento.

## Impacto en Configuración

- `frontend/package.json` — Tailwind CSS v4 y shadcn/ui ya instalados (ver commit `cef8abb`).
- `frontend/components.json` — configuración de shadcn/ui, preset `nova`.
- `docs/design/ux/` — los prototipos deben validar legibilidad en proyección antes de
  aprobarse; el criterio específico (tamaño mínimo de fuente, contraste) sigue siendo un ítem
  abierto — ver RNF-USA-2 en `docs/traceability/matrix.md`.

## Consecuencias

- ✅ Componentes accesibles por defecto (Radix UI)
- ✅ Totalmente personalizables — viven como código propio, no como dependencia opaca
- ⚠️ WCAG A es un mínimo — no cubre el nivel AA
- ⚠️ El criterio específico de legibilidad en proyección de aula sigue siendo un ítem abierto
  hasta la etapa de diseño UX (ver `CLAUDE.md`, ítems abiertos)
