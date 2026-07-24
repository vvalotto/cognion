# US-1.1.9: Administrador da de alta un Docente desde la UI

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-1.2`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (consume `POST /usuarios`, sin lógica de dominio propia en el frontend)
**Bounded Context**: Identidad

---

## Descripcion (lenguaje de negocio)

Como **Administrador** autenticado,
quiero **dar de alta una cuenta de Docente desde una pantalla web**
para **poder asignarla luego a una comisión y que ese Docente genere invitaciones** —
precondición operativa que `US-1.1.0` ya resuelve en backend.

---

## Contexto del dominio

### Problema

`POST /usuarios` con `perfil=docente` está implementado desde `US-1.1.0` y protegido por
`require_administrador` desde `US-1.1.5`, pero no hay ninguna pantalla que lo consuma. Es la
única forma de dar de alta un Docente — sin esta US, Víctor (único Administrador real del
proyecto) no puede operar esa parte desde la aplicación.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Endpoint consumido | `POST /usuarios` | Ya existe (`US-1.1.0`), protegido por `require_administrador` (`US-1.1.5`) — recibe `nombre`/`email`/`password`/`perfil`, devuelve el Usuario creado (201) o 409 (`EmailYaRegistrado`) |
| Ruta protegida | — | Usa el manejo de 401/403 de `US-1.1.6` — sin sesión de Administrador, no se llega a esta pantalla |

---

## Especificacion del comportamiento

### Precondicion

- `US-1.1.6` implementada (routing + manejo de sesión/401/403).
- `US-1.1.7` implementada (el Administrador necesita poder iniciar sesión para llegar a esta
  pantalla protegida).
- Sesión activa con rol `administrador`.

### Postcondicion

- Datos válidos → `POST /usuarios` con `perfil=docente` devuelve 201, se muestra
  `AltaDocenteExito.tsx` con la aclaración de que el Docente todavía no está asignado a
  ninguna comisión.
- Email ya registrado (409) → se muestra el error en el propio formulario
  (`EmailYaRegistrado`).
- Sin sesión, o sesión con rol distinto de `administrador` → no se llega al formulario: 401
  redirige a login, 403 muestra acceso denegado (comportamiento ya cubierto por `US-1.1.6`,
  esta US solo verifica que la ruta esté efectivamente protegida).

### Invariantes

| ID | Invariante |
|----|------------|
| — | El perfil está fijo en "Docente" — esta pantalla no ofrece elegir otro perfil (decisión explícita de Víctor en la aprobación del wireframe, §4: alta de Administrador queda fuera de alcance). |
| — | La pantalla no incluye asignación a comisión — es un comando separado (`AsignarDocenteAComision`), sin UI dedicada en esta iteración. |

---

## Criterios de aceptacion

```gherkin
Feature: Alta de Docente desde la UI (US-1.1.9)

  Scenario: Alta exitosa de un Docente
    Given un Administrador autenticado
    When completa el formulario de alta de Docente con datos válidos
    Then el sistema crea el Usuario con perfil Docente
    And muestra la pantalla de confirmación
    And aclara que el Docente todavía no está asignado a ninguna comisión

  Scenario: Alta rechazada por email duplicado
    Given un Administrador autenticado
    And un Usuario ya existe con el email que se va a usar
    When completa el formulario de alta de Docente con ese email
    Then el sistema muestra el error en el propio formulario

  Scenario: Acceso sin sesión
    Given ningún actor autenticado
    When intenta acceder a la pantalla de alta de Docente
    Then el sistema redirige a login

  Scenario: Acceso con rol insuficiente
    Given un Docente autenticado (no Administrador)
    When intenta acceder a la pantalla de alta de Docente
    Then el sistema muestra acceso denegado
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — consume un endpoint ya implementado y protegido (`ADR-007`), sin decisiones nuevas.

**Capa(s) afectadas:**
- [x] Frontend — `frontend/src/pages/AltaDocente.tsx`, `AltaDocenteExito.tsx`, ruta protegida
  en `frontend/src/router.tsx`
- [ ] Backend — sin cambios

---

## Fuente de verdad UX

`docs/design/ux/wireframes-identidad.md` §2.6 (`#alta-docente`), §2.7
(`#alta-docente-exito`), §3 (responsive, layout de una sola columna, header de aplicación).
Prototipo navegable: `docs/design/ux/prototipos/`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/pages/AltaDocente.tsx` | Formulario de alta — perfil fijo en Docente |
| `frontend/src/pages/AltaDocenteExito.tsx` | Confirmación con aclaración de comisión pendiente |
| `frontend/src/router.tsx` | Ruta protegida `/docentes/nuevo`, requiere rol `administrador` |

---

## Referencias

- Relacionada con: `US-1.1.0`, `US-1.1.5` (backend), `US-1.1.6`, `US-1.1.7` (infraestructura, precondición)
- Candidatas: `docs/plans/inc1/inc1-candidatas.md` §Iteración 2
- Issue: #26

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
