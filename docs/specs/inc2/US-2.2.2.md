# US-2.2.2: Administrador ve el listado de cuentas, filtra por rol/estado/búsqueda

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-2.2`
**Tipo**: `feat backend`
**Agregado principal afectado**: `Usuario`
**Bounded Context**: Identidad

---

## Descripcion (lenguaje de negocio)

Como **Administrador**,
quiero **ver el listado de todas las cuentas de usuarios, filtrable por rol, estado y
búsqueda por nombre/email**
para **encontrar rápido la cuenta que necesito gestionar cuando un docente o estudiante
reporta un problema (RF-03)**.

---

## Contexto del dominio

### Problema

RF-03 dice que "el administrador puede ver, modificar el estado y gestionar las cuentas sin
necesidad de intervención del docente" — hoy no existe ninguna forma de listar cuentas
existentes; `UsuarioRepositoryPort` solo tiene búsquedas puntuales por `id` o `email`
(pensadas para login/registro, no para un listado administrativo).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Query | `ListarCuentas(rol?, estado?, busqueda?)` | Devuelve `Usuario` que matchean todos los filtros provistos (AND) |

---

## Especificacion del comportamiento

### Precondicion

- Actor autenticado con JWT válido y claim `rol = administrador`.

### Postcondicion

- Devuelve la lista de cuentas (id, nombre, email, tipo de perfil, `bloqueada`) que matchean
  todos los filtros provistos.
- Sin filtros → devuelve todas las cuentas.
- `busqueda` matchea por coincidencia parcial (case-insensitive) contra `nombre` o `email`.
- `estado` acepta `activa` (`bloqueada = false`) o `bloqueada` (`bloqueada = true`).

### Invariantes

| ID | Invariante |
|----|------------|
| — | Sin invariantes de dominio propias — es una consulta de solo lectura, sin efectos sobre `Usuario`. |

---

## Criterios de aceptacion

```gherkin
Feature: Listado de cuentas con filtros (US-2.2.2)

  Scenario: Listado sin filtros
    Given existen cuentas de distintos roles y estados
    When un Administrador ejecuta ListarCuentas() sin filtros
    Then el sistema devuelve todas las cuentas

  Scenario: Filtro combinado por rol y estado
    Given existen Estudiantes activos y bloqueados, y Docentes activos
    When un Administrador ejecuta ListarCuentas(rol=estudiante, estado=bloqueada)
    Then el sistema devuelve solo los Estudiantes con bloqueada = true

  Scenario: Búsqueda por email parcial
    Given existe una cuenta con email "mgonzalez@fiuner.edu.ar"
    When un Administrador ejecuta ListarCuentas(busqueda="mgonzalez")
    Then esa cuenta aparece en el resultado
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — se implementa con la arquitectura existente.

**Capa(s) afectadas:**
- [x] Entities — sin cambios (consulta, no muta `Usuario`)
- [x] Use Cases — `ListarCuentasUseCase`
- [x] Interface Adapters — `CuentasController` nuevo, `UsuarioRepositoryPort.listar(...)`
- [x] Frameworks — endpoint FastAPI `GET /usuarios?rol=&estado=&busqueda=` (rol `administrador`)
- [ ] Frontend — cubierto por `US-2.2.6`

---

## Fuente de verdad UX

No aplica a esta spec (backend puro) — la pantalla correspondiente (`#cuentas`) se especifica
en `US-2.2.6` (`docs/design/ux/wireframes-cuentas-administracion.md` §2.1).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/entities/ports/usuario_repository_port.py` | Nuevo método `listar(rol, estado, busqueda) -> list[Usuario]` |
| `src/identidad/interface_adapters/gateways/usuario_repository.py` | Implementación SQL del filtro combinable |
| `src/identidad/use_cases/listar_cuentas.py` | Orquesta la consulta |
| `src/identidad/interface_adapters/controllers/cuentas_controller.py` | Controller nuevo, endpoint de listado |
| `src/identidad/frameworks/api/cuentas_router.py` | `GET /usuarios` |
| `src/identidad/frameworks/dependencies.py` | Wiring del nuevo controller/use case |

---

## Referencias

- Relacionada con: `US-2.2.1` (agrega `bloqueada`, campo que este listado filtra), `US-2.2.3`
  (detalle de una cuenta del listado), `US-2.2.6` (frontend)
- Modelo de dominio: `docs/design/domain/BC-identidad-modelo.md` §4 (`Usuario`)
- Candidatas: `docs/plans/inc2/inc2-candidatas.md` §Iteración 2 — Backend

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
