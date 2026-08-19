# US-2.2.6: Administrador ve y filtra el listado de cuentas (UI)

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-2.2`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (consume `US-2.2.2`, sin lógica de dominio propia en el frontend)
**Bounded Context**: Identidad

---

## Descripcion (lenguaje de negocio)

Como **Administrador**,
quiero **ver el listado de cuentas desde la aplicación, con filtros por rol, estado y
búsqueda**
para **ubicar la cuenta que necesito gestionar sin depender de una consola o de la base de
datos**.

---

## Contexto del dominio

### Problema

`GET /usuarios?rol=&estado=&busqueda=` existe desde `US-2.2.2`, pero sin esta US no hay
ninguna pantalla que lo consuma. Es la puerta de entrada al resto de la Iteración 2 en el
frontend — de acá se navega al detalle de una cuenta (`US-2.2.7`).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Endpoint consumido | `GET /usuarios?rol=&estado=&busqueda=` | Ya existe (`US-2.2.2`) |

---

## Especificacion del comportamiento

### Precondicion

- Usuario autenticado con rol `administrador` (guard `RequireRole`, mismo patrón de
  `US-1.1.9`).

### Postcondicion

- Al entrar a la pantalla, se listan todas las cuentas (sin filtros aplicados).
- Cambiar cualquiera de los tres filtros (rol, estado, búsqueda) vuelve a consultar el
  backend con los filtros combinados y refresca la tabla.
- "Limpiar filtros" vuelve al listado sin filtros.
- Cada fila navega al detalle de esa cuenta (`US-2.2.7`).

### Invariantes

| ID | Invariante |
|----|------------|
| — | N/A — pantalla de solo lectura, sin invariantes de dominio propias. |

---

## Criterios de aceptacion

```gherkin
Feature: Listado de cuentas en la UI (US-2.2.6)

  Scenario: Filtrar por rol y estado
    Given un Administrador en el listado de cuentas
    When selecciona rol "Estudiante" y estado "Bloqueada"
    Then la tabla muestra solo Estudiantes con cuenta bloqueada

  Scenario: Navegar al detalle
    Given un Administrador en el listado de cuentas
    When hace clic en una fila
    Then el sistema navega al detalle de esa cuenta
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — consume un endpoint ya implementado.

**Capa(s) afectadas:**
- [x] Frontend — `frontend/src/lib/cuentas-api.ts` (cliente nuevo, reutiliza `apiFetch`/JWT
  de `US-1.1.6`), `frontend/src/pages/Cuentas.tsx`
- [ ] Backend — sin cambios

---

## Fuente de verdad UX

`docs/design/ux/wireframes-cuentas-administracion.md` §2.1 (`#cuentas`). Prototipo
navegable: `docs/design/ux/prototipos/identidad-cuentas-administracion.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/lib/cuentas-api.ts` | Cliente API tipado, `listarCuentas(filtros)`, mapea snake_case↔camelCase (mismo patrón que `banco-preguntas-api.ts`) |
| `frontend/src/pages/Cuentas.tsx` | Tabla + filtros de rol/estado/búsqueda |
| `frontend/src/router.tsx` | Ruta `/cuentas`, protegida con `RequireRole rol="administrador"` |

---

## Referencias

- Relacionada con: `US-2.2.2` (backend), `US-2.2.7` (navegación de salida hacia el detalle)
- Candidatas: `docs/plans/inc2/inc2-candidatas.md` §Iteración 2 — Frontend

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
