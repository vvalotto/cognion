# US-ADJ-54: Esperas asincrónicas correctas en los tests del frontend

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 6 — ajuste inmediato tras US-6.3.7`
**Tipo**: `test` (sin código de producción)
**Agregado principal afectado**: ninguno
**Bounded Context**: ninguno — transversal (tests de frontend de todos los BC)
**Origen**: Fase 7 de `US-6.3.7` (2026-09-24). Decisión de Víctor: resolverlo como US-ADJ inmediatamente después
de `US-ADJ-53`, antes de `US-6.3.8`.

---

## Descripcion (lenguaje de negocio)

Como **responsable del proceso de calidad**,
quiero **que los tests del frontend esperen el dato que verifican y no solo el elemento que lo muestra**
para **que no fallen al azar según la velocidad de la máquina, ni en local ni en CI**.

---

## Contexto del dominio

### Problema

Hay tests que esperan a que **aparezca un elemento** y verifican **enseguida** un valor que llega **después**, con
un pedido HTTP propio. Casos confirmados en la Fase 7 de `US-6.3.7`:

- `frontend/src/pages/cuentas/EditarCuenta.test.tsx:51` — el formulario se dibuja vacío y se completa al llegar la
  cuenta; `expect(await screen.findByLabelText("Nombre completo")).toHaveValue("Ana Docente")` encuentra el campo
  al instante (vacío) y verifica una sola vez.
- `frontend/src/pages/actividad-evaluativa/MateriasActividades.test.tsx` ("muestra cantidad de comisiones y
  actividades por estado") — espera la fila de la materia, pero los conteos llegan en otro pedido.
- `frontend/src/pages/banco-preguntas/EditarMateria.test.tsx` ("precarga el nombre actual de la materia") — mismo
  síntoma, a confirmar en el barrido.

Casi siempre ganan la carrera; bajo carga la pierden. Es un defecto del test, no del componente.

### Patrón correcto

```ts
const campo = await screen.findByLabelText("Nombre completo")
await waitFor(() => expect(campo).toHaveValue("Ana Docente"))
```

(o `findByDisplayValue` / `findByText` sobre el dato mismo, cuando se lea mejor).

---

## Especificacion del comportamiento

### Precondicion

- `US-ADJ-53` mergeada (para medir con la suite estable, sin confundir saturación con carrera).

### Postcondicion

- **Barrido** de todo `frontend/src/**/*.test.tsx` buscando el patrón "espera el elemento, verifica un valor
  asincrónico sin reintento" (`findBy*(...)` seguido de `toHaveValue`/`toHaveTextContent`/conteos que dependen de
  otro pedido). El reporte lista cada caso encontrado y cómo se corrigió, o por qué se descartó.
- Tests corregidos con el patrón de arriba. **Sin cambios en componentes**.

---

## Criterios de aceptacion

```gherkin
Feature: Esperas asincrónicas correctas en tests (US-ADJ-54)

  Scenario: Los casos confirmados esperan el dato
    Given los tests de EditarCuenta, MateriasActividades y EditarMateria
    When se revisa cómo verifican los valores que llegan después del primer render
    Then esperan el dato con reintento, no solo el elemento

  Scenario: Barrido documentado
    Given todos los tests del frontend
    When se busca el patrón de espera incompleta
    Then el reporte lista cada caso encontrado con su corrección o su descarte

  Scenario: Sin fallos aleatorios en corridas repetidas
    Given la suite completa
    When se corre "npm run test" 3 veces seguidas y "npm run test:coverage" 3 veces seguidas
    Then las 6 corridas pasan completas

  Scenario: Sin cambios de comportamiento
    Given los componentes de los tests corregidos
    When se compara el diff
    Then solo cambian archivos de test
```

---

## Impacto arquitectonico

- [x] No. Solo tests del frontend.

---

## Fuera de alcance

- Mostrar "Cargando…" en `EditarCuenta` mientras llega la cuenta (decisión de UX, no la causa del fallo).
- `cleanup` automático global en `src/test/setup.ts` (hoy cada archivo lo llama a mano porque `globals` no está
  activo): se evalúa aparte si el barrido muestra que hace falta.

---

## Referencias

- `docs/reports/inc6/US-6.3.7-report.md` §Métricas de Calidad.
- Depende de: `US-ADJ-53`.
