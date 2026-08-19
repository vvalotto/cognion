# US-2.2.3: Administrador ve el detalle de una cuenta

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-2.2`
**Tipo**: `feat backend`
**Agregado principal afectado**: `Usuario`
**Bounded Context**: Identidad

---

## Descripcion (lenguaje de negocio)

Como **Administrador**,
quiero **ver el detalle completo de una cuenta puntual**
para **confirmar su estado antes de decidir si necesita un reseteo de contraseña o
desbloqueo (RF-03)**.

---

## Contexto del dominio

### Problema

El listado de `US-2.2.2` alcanza para encontrar una cuenta, pero no expone todo lo necesario
para decidir una acción sobre ella (p.ej. la comisión de un Estudiante, o la fecha de alta) —
se separa en una query propia, consistente con el patrón ya usado en Banco de Preguntas
(`US-2.1.7` listado vs. el detalle implícito en la edición de `US-2.1.5`).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Query | `ObtenerCuenta(usuario_id)` | Devuelve el detalle de un `Usuario`, incluyendo su perfil |

---

## Especificacion del comportamiento

### Precondicion

- Actor autenticado con JWT válido y claim `rol = administrador`.
- `Usuario` (`usuario_id`) existe.

### Postcondicion

- Devuelve: `id`, `nombre`, `email`, tipo de perfil (rol derivado), `bloqueada`,
  `creado_en`, y `comision_id` cuando el perfil es `Estudiante` (`null` para
  Docente/Administrador).

### Invariantes

| ID | Invariante |
|----|------------|
| — | Sin invariantes de dominio propias — consulta de solo lectura. |

---

## Criterios de aceptacion

```gherkin
Feature: Detalle de una cuenta (US-2.2.3)

  Scenario: Detalle de un Estudiante
    Given un Usuario con perfil Estudiante asignado a una Comisión
    When un Administrador ejecuta ObtenerCuenta(usuario_id)
    Then el sistema devuelve sus datos incluyendo comision_id

  Scenario: Detalle de un Docente
    Given un Usuario con perfil Docente
    When un Administrador ejecuta ObtenerCuenta(usuario_id)
    Then el sistema devuelve sus datos con comision_id en null

  Scenario: Cuenta inexistente
    Given ningún Usuario tiene el id provisto
    When un Administrador ejecuta ObtenerCuenta(usuario_id)
    Then el sistema rechaza con UsuarioNoExiste
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — se implementa con la arquitectura existente.

**Capa(s) afectadas:**
- [x] Entities — nuevo error `UsuarioNoExiste`
- [x] Use Cases — `ObtenerCuentaUseCase`
- [x] Interface Adapters — nuevo endpoint en `CuentasController` (`US-2.2.2`)
- [x] Frameworks — endpoint FastAPI `GET /usuarios/{id}` (rol `administrador`)
- [ ] Frontend — cubierto por `US-2.2.7`

---

## Fuente de verdad UX

No aplica a esta spec (backend puro) — la pantalla correspondiente (`#cuenta-detalle`) se
especifica en `US-2.2.7`
(`docs/design/ux/wireframes-cuentas-administracion.md` §2.2).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/entities/errors.py` | Agregar `UsuarioNoExiste` |
| `src/identidad/use_cases/obtener_cuenta.py` | Orquesta la consulta, resuelve `comision_id` del perfil Estudiante |
| `src/identidad/interface_adapters/controllers/cuentas_controller.py` | Endpoint de detalle, reutiliza el controller de `US-2.2.2` |
| `src/identidad/frameworks/api/cuentas_router.py` | `GET /usuarios/{id}` |

---

## Referencias

- Relacionada con: `US-2.2.2` (listado que precede a esta consulta), `US-2.2.4` (acción
  disponible desde este detalle), `US-2.2.7` (frontend)
- Modelo de dominio: `docs/design/domain/BC-identidad-modelo.md` §4 (`Usuario`, `Estudiante`)
- Candidatas: `docs/plans/inc2/inc2-candidatas.md` §Iteración 2 — Backend

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
