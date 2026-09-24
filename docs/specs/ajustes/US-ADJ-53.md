# US-ADJ-53: Corrida de la suite frontend con cobertura estable, sin flags manuales

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 6 — ajuste inmediato tras US-6.3.7`
**Tipo**: `config` (tooling de tests, sin código de producción)
**Agregado principal afectado**: ninguno
**Bounded Context**: ninguno — transversal (frontend, herramienta de tests)
**Origen**: Fase 7 de `US-6.3.7` (2026-09-24). Decisión de Víctor: resolverlo como US-ADJ inmediatamente después
de cerrar `US-6.3.7`, antes de `US-6.3.8`.

---

## Descripcion (lenguaje de negocio)

Como **responsable del proceso de calidad**,
quiero **que la suite completa del frontend con cobertura corra estable con un solo comando documentado**
para **que un fallo en la Fase 7 signifique un problema real y no una máquina saturada**.

---

## Contexto del dominio

### Problema

`npx vitest run --coverage` sobre la suite completa (99 archivos, 639 tests) satura la máquina local: en la Fase 7
de `US-6.3.7` se midió **load average 116 con 8 núcleos**. Vitest lanza por defecto un worker por núcleo y la
instrumentación v8 multiplica el costo; los tests con timeout por defecto (5 s) o con `findBy*`/`waitFor` (1 s)
expiran de forma aleatoria — tests distintos en cada corrida, todos pasan aislados.

Desde `US-6.3.4` la Fase 7 lo esquiva pasando `--testTimeout=20000` (y en `US-6.3.7`, `30000`) a mano. El flag no
está en ninguna configuración ni documentado fuera de los `quality.json` de cada US.

El CI (`.github/workflows/ci.yml`) corre `npm run test` **sin** cobertura: este problema afecta sobre todo las
corridas locales de la Fase 7 y de cierre de baseline.

### Relación con `US-ADJ-54`

Son complementarias, no la misma cosa: esta US quita la saturación; `US-ADJ-54` corrige los tests cuya espera
asincrónica es incorrecta y que pueden fallar aun sin saturación (también en CI).

---

## Especificacion del comportamiento

### Precondicion

- `US-6.3.7` mergeada.

### Postcondicion

- Script `npm run test:coverage` en `frontend/package.json`.
- Configuración de la corrida con cobertura en `frontend/vite.config.ts` (no flags sueltos): límite de workers y
  timeout de test acordes, **solo donde hace falta** — los valores concretos se fijan en la Fase 2 midiendo
  (duración total y load average) con 2 o 3 configuraciones, no a ojo.
- `npm run test` (lo que corre el CI) conserva su comportamiento o mejora; no se alarga el CI sin justificarlo.
- La Fase 7 del perfil de frontend usa `npm run test:coverage` (actualizar la referencia en el skill
  `implement-us` o en la documentación donde figure el comando).

---

## Criterios de aceptacion

```gherkin
Feature: Suite frontend con cobertura estable (US-ADJ-53)

  Scenario: Un solo comando documentado
    Given el frontend con sus dependencias instaladas
    When se corre "npm run test:coverage"
    Then corre la suite completa con cobertura y aplica los umbrales de 80%, sin flags adicionales

  Scenario: Estable en corridas repetidas
    Given la máquina local sin otras cargas pesadas
    When se corre "npm run test:coverage" 3 veces seguidas
    Then las 3 corridas pasan completas

  Scenario: Sin saturar la máquina
    Given una corrida de "npm run test:coverage"
    When se mide el load average durante la corrida
    Then queda por debajo del valor medido hoy (116 con 8 núcleos), registrado en el reporte

  Scenario: El CI no empeora
    Given el workflow de CI
    When corre "npm run test"
    Then sigue pasando y su duración no crece sin justificación en el reporte
```

---

## Impacto arquitectonico

- [x] No. Solo configuración de tests del frontend.

**Capa(s) afectadas:** tooling (`frontend/vite.config.ts`, `frontend/package.json`, documentación del proceso).

---

## Fuera de alcance

- Corregir tests individuales con esperas mal armadas (`US-ADJ-54`).
- Agregar cobertura al CI.

---

## Referencias

- `docs/reports/inc6/US-6.3.7-report.md` §Métricas de Calidad; `quality/reports/inc6/US-6.3.4` a `US-6.3.7-quality.json`
  (notas del flag manual).
