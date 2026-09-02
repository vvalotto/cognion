# US-ADJ-16: Subir cobertura de branches del frontend (77.89% → 80%)

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 3-ADJ — Adecuación Técnica`
**Tipo**: `tests frontend` (agregar casos, sin cambio de comportamiento)
**Agregado principal afectado**: ninguno
**Bounded Context**: transversal — varias pantallas de los 3 BCs con frontend
**Origen**: retro de `BL-004` — detectado recién al correr `vitest run --coverage` de punta a
punta para la baseline; ninguna US individual lo mostró porque el gate de Fase 7 mide por
archivo tocado, no cobertura global del proyecto.

---

## Descripcion (lenguaje de negocio)

Como **responsable del proceso de calidad**,
quiero **que la cobertura de branches del frontend vuelva a estar por encima del umbral
configurado (80%)**
para **que el umbral de `vitest.config.ts` deje de ser una discrepancia silenciosa y vuelva a
significar lo que dice significar**.

---

## Contexto del dominio

### Problema

`vitest.config.ts` declara `coverage.thresholds.branches = 80`, pero correr la suite completa
con `--coverage` (cierre de `BL-004`) dio:

```
Statements   : 90.8% ( 1126/1240 )
Branches     : 77.89% ( 518/665 )
Functions    : 91.43% ( 395/432 )
Lines        : 93.14% ( 1046/1123 )
ERROR: Coverage for branches (77.89%) does not meet global threshold (80%)
```

Ningún PR individual lo detectó: el gate de Fase 7 de `/implement-us` corre cobertura solo
sobre los archivos tocados por esa US, no de forma global — una pantalla con branches sin
cubrir pasó su propio umbral por archivo mientras la suite completa, agregada, cae por debajo.

Los archivos con menor cobertura de branches identificados en la corrida de cierre de `BL-004`
(candidatos concretos, no una lista exhaustiva — priorizar los peores primero):

| Archivo | Branches | Líneas sin cubrir (aprox.) |
|---|---|---|
| `EvaluacionSuspendida.tsx` | 50% | 17-32 |
| `NuevaPreguntaTipo.tsx` | 50% | 46-47, 64-65 |
| `Actividades.tsx` | 58.82% | 43-44, 98, 118-121 |
| `Materias.tsx` | 58.33% | 43, 62 |
| `MisMaterias.tsx` | 60% | 61-62 |
| `NuevaActividad.tsx` | 60% | 13-35 |

### Alcance del fix

Agregar casos de test (branches de error, estados vacíos, ramas condicionales no ejercitadas)
en los archivos de la tabla — empezando por los de menor porcentaje. No es necesario llegar a
100% en cada uno; el objetivo es que la suite completa vuelva a superar el 80% global de
branches, no maximizar cada archivo individualmente. Si al terminar la tabla anterior no
alcanza, repetir el análisis (`vitest run --coverage`) para identificar el siguiente candidato.

---

## Especificacion del comportamiento

### Precondicion

- `npx vitest run --coverage --no-file-parallelism` falla el umbral global de branches (77.89%
  < 80%).

### Postcondicion

- `npx vitest run --coverage --no-file-parallelism` termina sin el error de umbral — branches
  ≥ 80% de forma global.
- Ningún test existente se modifica de forma que deje de verificar lo que verificaba — solo se
  agregan casos nuevos.

### Invariantes

Ninguna — no hay cambio de dominio ni de comportamiento de la aplicación.

---

## Criterios de aceptacion

```gherkin
Feature: Cobertura de branches del frontend por encima del umbral (US-ADJ-16)

  Scenario: La suite completa supera el umbral global
    Given tests nuevos agregados en los archivos de menor cobertura de branches
    When se corre npx vitest run --coverage --no-file-parallelism
    Then el resumen de cobertura reporta branches >= 80%
    And no aparece "ERROR: Coverage for branches ... does not meet global threshold"
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — solo agrega tests, sin cambiar comportamiento ni contrato de ningún componente.

**Capa(s) afectadas:**
- [x] Frontend — archivos `*.test.tsx` de las pantallas listadas (y las que se sumen si hace
      falta más cobertura)

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/pages/EvaluacionSuspendida.test.tsx` | Casos nuevos para branches sin cubrir |
| `frontend/src/pages/NuevaPreguntaTipo.test.tsx` | Casos nuevos para branches sin cubrir |
| `frontend/src/pages/Actividades.test.tsx` | Casos nuevos para branches sin cubrir |
| `frontend/src/pages/Materias.test.tsx` | Casos nuevos para branches sin cubrir |
| `frontend/src/pages/MisMaterias.test.tsx` | Casos nuevos para branches sin cubrir |
| `frontend/src/pages/NuevaActividad.test.tsx` | Casos nuevos para branches sin cubrir |

---

## Referencias

- Relacionada con: retro de `BL-004` (`.cm/baselines/BL-004-actividad-evaluativa.md`)
- Detectada durante: cierre de `BL-004`, corrida de `vitest run --coverage` de punta a punta

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
