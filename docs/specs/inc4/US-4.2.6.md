# US-4.2.6: Docente ve "Desempeño por tema"

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-4.2`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (BC sin aggregate propio, `BC-analytics-modelo.md` §2)
**Bounded Context**: Analytics

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **ver qué unidades/temas de una materia concentran más errores, para toda la materia o
una comisión puntual**
para **decidir dónde reforzar la enseñanza (RF-17)**.

---

## Contexto del dominio

### Problema

`US-4.2.4` ya expone `GET /analytics/materias/{materia_id}/tasa-error-por-tema?comision_id=`.
Falta la pantalla que lo consume — cierra completa la Iteración 2 del Incremento 4.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Cliente API (nuevo) | función tipada para `GET /analytics/materias/{materia_id}/tasa-error-por-tema` | Sobre `apiFetch`/`ApiError` existentes, reutiliza `listarComisionesPorMateria` de `US-4.2.5` |
| Pantalla (nueva) | `DesempenoPorTema.tsx` | Selector Materia (siempre) → Comisión (opcional, default "Toda la materia"), listado de `.tema-row` |
| Ruta (nueva) | `/analytics/desempeno-por-tema` (o path equivalente, a confirmar en el plan) | Protegida con `RequireRole rol="docente"` |

---

## Especificacion del comportamiento

### Precondicion

- `US-4.2.2` y `US-4.2.4` implementadas.
- Docente autenticado.

### Postcondicion

- Al entrar a la pantalla: selector de Materia poblado (`listarMateria()`, `US-2.1.9`), selector
  de Comisión en "Toda la materia" por defecto → dispara `GET .../tasa-error-por-tema` sin
  `comision_id`.
- Elegir Materia → pobla el selector de Comisión (`GET /materias/{materia_id}/comisiones`,
  `US-4.2.2`) y reconsulta con "Toda la materia".
- Elegir una Comisión puntual → reconsulta con `comision_id`.
- Resultado: una fila por `(unidad_tematica, tema)`, ordenada por tasa de error descendente —
  unidad (rótulo pequeño) + tema, barra de progreso coloreada, % de tasa de error, cantidad de
  respuestas/incorrectas. Color: ≥ 50% rojo, 20–49% ámbar, < 20% verde
  (`wireframes-analytics.md` §3.1, umbrales de referencia).
- Materia (o comisión elegida) sin ninguna `Evaluacion` finalizada → mensaje de estado vacío,
  sin listado.

### Invariantes

| ID | Invariante |
|----|------------|
| — | Los umbrales de color (50%/20%) son de UI, no de dominio — viven en el componente de presentación, no en ningún cálculo del backend. |
| — | Cambiar de Materia reinicia la Comisión a "Toda la materia" (no conserva una comisión de la materia anterior, que ya no aplica). |

---

## Criterios de aceptacion

```gherkin
Feature: Docente ve "Desempeño por tema" (US-4.2.6)

  Scenario: Materia completa por defecto
    Given un Docente entra a "Desempeño por tema" y elige una Materia con Evaluacion finalizadas
    When la pantalla carga
    Then ve el listado de temas ordenado por tasa de error descendente, agregado de toda la materia

  Scenario: Acotar a una comisión
    Given el Docente ya ve el listado de la materia completa
    When elige una Comisión puntual
    Then el listado se recalcula solo con las respuestas de esa comisión

  Scenario: Color por severidad
    Given un tema con tasa de error del 60%, otro del 30% y otro del 10%
    When se renderiza el listado
    Then el primero se ve en rojo, el segundo en ámbar y el tercero en verde

  Scenario: Materia sin evaluaciones finalizadas
    Given una Materia sin ninguna Evaluacion finalizada
    When el Docente la elige
    Then ve el mensaje de estado vacío, sin listado

  Scenario: Acceso sin rol Docente
    Given un Estudiante o Administrador autenticado
    When intenta acceder a la ruta de "Desempeño por tema"
    Then es redirigido por RequireRole, no ve la pantalla
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — frontend puro, reutiliza `apiFetch`/`RequireRole`/`listarComisionesPorMateria`
  (`US-4.2.5`).

**Capa(s) afectadas:**
- [ ] Entities / Use Cases / Interface Adapters / Frameworks (backend) — sin cambios
- [x] Frontend — cliente API (1 función nueva), pantalla `DesempenoPorTema.tsx`, primitiva
  `.tema-row` (barra de progreso coloreada), ruta nueva en `router.tsx` protegida con
  `RequireRole rol="docente"`

---

## Fuente de verdad UX

`docs/design/ux/wireframes-analytics.md` §3.1 (`#doc-desempeno-tema`) y §4 (hot spot 3: la fila
de tema no navega a ningún detalle adicional — RF-17 pide agregados, no el detalle pregunta por
pregunta). Umbrales de color pendientes de confirmar con datos reales (§4, "pendiente de
definir"): usar 50%/20% del prototipo como default, ajustable sin romper contrato de API.
Prototipo: `docs/design/ux/prototipos/analytics-portal-desempeno.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/lib/analytics-api.ts` | Agrega `obtenerTasaErrorPorTema(materiaId, comisionId?)` |
| `frontend/src/pages/analytics/DesempenoPorTema.tsx` | Nueva pantalla |
| `frontend/src/components/` | Primitiva `.tema-row` (o componente `TemaRow`) reutilizable |
| `frontend/src/router.tsx` | Ruta nueva, `RequireRole rol="docente"` |
| Tests Vitest correspondientes | Cambio de materia/comisión, color por severidad, estado vacío |

---

## Referencias

- Depende de: `US-4.2.4` (#243)
- Candidatas: `docs/plans/inc4/inc4-candidatas.md` §Iteración 2
- Issue: #245

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
