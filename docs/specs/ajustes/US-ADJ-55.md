# US-ADJ-55: Espera máxima de Testing Library acorde a la suite completa

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 6 — ajuste inmediato tras US-6.3.8`
**Tipo**: `config` (tooling de tests, sin código de producción)
**Agregado principal afectado**: ninguno
**Bounded Context**: ninguno — transversal (frontend, herramienta de tests)
**Origen**: Fase 7 de `US-6.3.8` (2026-09-24). Decisión de Víctor: US-ADJ inmediata después de mergear `US-6.3.8`,
antes de `US-6.3.9`.

---

## Descripcion (lenguaje de negocio)

Como **responsable del proceso de calidad**,
quiero **que las esperas de los tests (`findBy*`, `waitFor`) tengan margen suficiente para la suite completa**
para **que un test bien escrito no falle al azar solo porque la suite entera corre en paralelo**.

---

## Contexto del dominio

### Problema

En la Fase 7 de `US-6.3.8`, `npm run test:coverage` falló 1 de 671 tests:
`AutoregistroEstudiante.test.tsx` — "puebla el selector de Materia al montar". El test **espera bien el dato**
(`findByRole("option", …)`), pero se agotó la espera máxima de Testing Library: `asyncUtilTimeout`, **1 s por
defecto**. Tardó 1,76 s con la carga que genera la propia suite (load ~35, partiendo de 5 en reposo). Aislado pasa 5/5;
la corrida siguiente de la suite completa pasó 671/671.

No lo cubrieron las dos US-ADJ anteriores:

- `US-ADJ-53` subió `testTimeout` (límite de cada test, 20 s), no la espera interna de `findBy*`/`waitFor`.
- `US-ADJ-54` corrigió tests que **no** esperaban el dato; este sí lo espera.

---

## Especificacion del comportamiento

### Precondicion

- `US-6.3.8` mergeada.

### Postcondicion

- `asyncUtilTimeout` configurado una sola vez en `frontend/src/test/setup.ts` (`configure({ asyncUtilTimeout })` de
  `@testing-library/react`), con un comentario que remite a esta US. **Sin tocar tests individuales.**
- Valor fijado con datos: medir cuánto tardan hoy las esperas más lentas de la suite completa y dejar margen, sin
  inflarlo de más (un valor alto solo retrasa el aviso de un test realmente roto).
- La sección "Frontend" de `phase-7-quality-gates.md` (`US-ADJ-53`) menciona el ajuste.

---

## Criterios de aceptacion

```gherkin
Feature: Espera máxima de Testing Library acorde a la suite (US-ADJ-55)

  Scenario: Configuración única
    Given el setup de tests del frontend
    When se revisa cómo se configura la espera de findBy y waitFor
    Then está fijada una sola vez en src/test/setup.ts, con el motivo documentado

  Scenario: Valor fijado con datos
    Given la suite completa con cobertura
    When se miden las esperas más lentas
    Then el valor elegido deja margen sobre lo medido y el reporte registra la medición

  Scenario: Estable en corridas repetidas
    Given la máquina en reposo
    When se corre "npm run test:coverage" 3 veces seguidas y "npm run test" 3 veces seguidas
    Then las 6 corridas pasan completas

  Scenario: Sin cambios de comportamiento
    Given el diff de la US
    When se revisan los archivos modificados
    Then no cambia ningún componente ni ningún test individual
```

---

## Impacto arquitectonico

- [x] No. Solo configuración de tests del frontend.

---

## Fuera de alcance

- Reescribir tests para que corran más rápido.
- Cambios de CI.

---

## Referencias

- `docs/reports/inc6/US-6.3.8-report.md` §Métricas de Calidad; `quality/reports/inc6/US-6.3.8-quality.json`.
- Relacionadas: `US-ADJ-53` (timeout por test), `US-ADJ-54` (esperas incompletas).
