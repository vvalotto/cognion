# US-1.1.0: Administrador da de alta cuentas de usuario, crea una comisión y asigna docentes

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-1.1`
**Tipo**: `feat backend` + `feat frontend` (solo alta de Docente, ver alcance)
**Agregado principal afectado**: `Usuario`, `Comisión`
**Bounded Context**: Identidad

---

## Descripcion (lenguaje de negocio)

Como **Administrador**,
quiero **dar de alta cuentas de usuario (en particular Docentes), crear una Comisión y asignar
uno o más Docentes a ella**
para **contar con la precondición mínima que necesita todo lo demás del BC: sin un `Usuario`
con perfil `Docente` y sin una `Comisión` con al menos un Docente asignado, no existe forma de
generar una invitación (`US-1.1.1`) ni de probar el flujo de registro de punta a punta**.

No tiene RF propio — surgió como necesidad derivada del event storming
(`BC-identidad-modelo.md` §6 y §9). Se resuelve dentro del producto (el Administrador lo
ejecuta), no como seed/fixture — con la única excepción del primer Administrador (huevo y
gallina), que se crea por seed/fixture al desplegar el entorno.

---

## Contexto del dominio

### Problema

Antes de esta US no existe ningún mecanismo para crear un `Usuario` dentro del producto — el
primer Administrador es un dato de bootstrap, pero a partir de ahí toda alta adicional
(Docentes, otros Administradores, y la infraestructura de Comisiones que un Docente necesita
para generar invitaciones) debe poder ejecutarse sin intervención fuera de la aplicación.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Aggregate | `Usuario` | Identidad y credenciales comunes a los tres perfiles; guarda `perfil` como Entity subordinada |
| Entity subordinada | `Docente`, `Administrador`, `Estudiante` | Perfil concreto (`id = usuario_id`), creado atómicamente junto con `Usuario` |
| Aggregate | `Comisión` | Espacio de dictado de una materia: horario, `docentes_asignados` |
| Command | `CrearUsuario(nombre, email, password, perfil)` | Crea `Usuario` + perfil en la misma transacción |
| Command | `CrearComision(materia, horario, administrador_id)` | Crea una `Comisión` |
| Command | `AsignarDocenteAComision(comision_id, docente_id)` | Agrega un `Docente` a `docentes_asignados` |
| Domain Event | `UsuarioCreado`, `ComisionCreada`, `DocenteAsignado` | Señalan cada alta/asignación |
| Port | `PasswordHasherPort` | Hashing de contraseña (bcrypt, `ADR-014`) |

---

## Especificacion del comportamiento

### Precondicion

- Actor autenticado con JWT válido y claim `rol = administrador` (`US-1.1.4`, `US-1.1.5`).
- Para `AsignarDocenteAComision`: el `usuario_id` recibido corresponde a un `Usuario` existente
  con perfil `Docente`.

### Postcondicion

- `CrearUsuario`: `Usuario` + perfil (`Docente`, `Administrador` o `Estudiante`) persistidos en
  la misma transacción; `password_hash` con bcrypt, nunca la contraseña en texto plano; evento
  `UsuarioCreado`.
- `CrearComision`: `Comisión` persistida con `docentes_asignados` vacío; evento
  `ComisionCreada`.
- `AsignarDocenteAComision`: el `Docente` referenciado queda agregado a
  `Comisión.docentes_asignados`; evento `DocenteAsignado`.

### Invariantes

| ID | Invariante |
|----|------------|
| INV-ID-09 | Todo `Usuario` tiene exactamente un `perfil`, creado atómicamente en el mismo comando que crea el `Usuario` — no puede existir un `Usuario` sin perfil ni un perfil huérfano. |
| INV-ID-04 | `email` único en todo el sistema, sin distinción de perfil — `EmailYaRegistrado` si ya existe. |
| INV-ID-06 | `password_hash` se persiste siempre con bcrypt (`ADR-014`); nunca en texto plano ni expuesto en ninguna respuesta. |
| INV-ID-07 | Puede existir más de una `Comisión` para la misma materia — `CrearComision` no valida unicidad de `materia`. |
| — | Solo un `Usuario` con perfil `Docente` puede agregarse a `docentes_asignados` — `UsuarioNoEsDocente` si no. |

---

## Criterios de aceptacion

```gherkin
Feature: Alta de usuarios y comisiones por Administrador

  Scenario: Administrador crea un Docente
    Given un Administrador autenticado con JWT válido
    When ejecuta CrearUsuario(nombre, email, password, perfil=Docente)
    Then el sistema crea un Usuario con perfil Docente en la misma transacción
    And la contraseña se persiste hasheada con bcrypt
    And se emite el evento UsuarioCreado

  Scenario: Alta rechazada por email duplicado
    Given un Usuario ya existe con email "docente@fiuner.edu.ar"
    When un Administrador ejecuta CrearUsuario con ese mismo email
    Then el sistema rechaza la operación con EmailYaRegistrado
    And ningún Usuario nuevo se crea

  Scenario: Administrador crea una Comisión
    Given un Administrador autenticado
    When ejecuta CrearComision(materia="Ingeniería de Software", horario, administrador_id)
    Then el sistema persiste la Comisión con docentes_asignados vacío
    And se emite el evento ComisionCreada

  Scenario: Administrador asigna un Docente a una Comisión
    Given una Comisión existente y un Usuario con perfil Docente
    When el Administrador ejecuta AsignarDocenteAComision(comision_id, docente_id)
    Then el Docente queda agregado a Comisión.docentes_asignados
    And se emite el evento DocenteAsignado

  Scenario: Rechazo al asignar un Usuario que no es Docente
    Given un Usuario existente con perfil Estudiante
    When el Administrador ejecuta AsignarDocenteAComision(comision_id, ese usuario_id)
    Then el sistema rechaza la operación con UsuarioNoEsDocente
    And Comisión.docentes_asignados no cambia
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — se implementa con la arquitectura existente (`ADR-007`, `ADR-014`)

**Capa(s) afectadas:**
- [x] Entities — `Usuario`, `Docente`, `Administrador`, `Estudiante`, `Comisión`, eventos
- [x] Use Cases — `CrearUsuarioUseCase`, `CrearComisionUseCase`, `AsignarDocenteAComisionUseCase`
- [x] Interface Adapters — controllers/presenters, `UsuarioRepositoryPort`, `ComisionRepositoryPort`
- [x] Frameworks — endpoints FastAPI, modelos SQLAlchemy + migración Alembic
- [x] Frontend — solo la pantalla de alta de Docente (ver alcance frontend abajo)

---

## Alcance frontend

Solo se construye UI para **alta de Docente** (`CrearUsuario` con `perfil` fijo en `Docente`),
porque es la única parte de esta US con wireframe aprobado (`wireframes-identidad.md` §2.6,
§2.7). `CrearComision` y `AsignarDocenteAComision` se implementan **solo en backend** (endpoint
API) en esta iteración — no tienen wireframe aprobado y el gate de diseño UX
(`CLAUDE.md` §"Gate de diseño UX") no permite escribir `frontend/` sin artefacto aprobado. Se
puede operar por API directamente (Swagger/HTTP) hasta que una US futura agregue su UI.

## Fuente de verdad UX

- `docs/design/ux/wireframes-identidad.md` §2.6 (Admin — Alta de Docente) y §2.7 (Admin —
  Docente creado).
- Prototipo: `docs/design/ux/prototipos/identidad-registro-login.html` (`#alta-docente`,
  `#alta-docente-exito`).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/entities/usuario.py` | Aggregate `Usuario` + entities subordinadas `Docente`/`Administrador`/`Estudiante` |
| `src/identidad/entities/comision.py` | Aggregate `Comisión` |
| `src/identidad/entities/eventos.py` | `UsuarioCreado`, `ComisionCreada`, `DocenteAsignado` |
| `src/identidad/entities/ports/password_hasher_port.py` | Puerto de hashing bcrypt |
| `src/identidad/entities/ports/usuario_repository_port.py`, `comision_repository_port.py` | Puertos de persistencia |
| `src/identidad/use_cases/crear_usuario.py` | Orquesta alta de `Usuario` + perfil |
| `src/identidad/use_cases/crear_comision.py` | Orquesta alta de `Comisión` |
| `src/identidad/use_cases/asignar_docente_a_comision.py` | Orquesta asignación |
| `src/identidad/interface_adapters/controllers/usuarios_controller.py`, `comisiones_controller.py` | Validación de entrada, mapeo a use case |
| `src/identidad/interface_adapters/gateways/usuario_repository.py`, `comision_repository.py` | Implementación SQLAlchemy de los puertos |
| `src/identidad/frameworks/api/usuarios_router.py`, `comisiones_router.py` | Endpoints FastAPI (requieren rol `administrador`) |
| `src/identidad/frameworks/db/models.py` | Modelos SQLAlchemy `usuario`, `docente`, `administrador`, `estudiante`, `comision` |
| `src/identidad/frameworks/db/migrations/` | Migración Alembic de las tablas nuevas |
| `frontend/src/features/identidad/AltaDocente.tsx` | Pantalla `#alta-docente` |
| `frontend/src/features/identidad/AltaDocenteExito.tsx` | Pantalla `#alta-docente-exito` |

---

## Referencias

- Relacionada con: `US-1.1.1`, `US-1.1.4`, `US-1.1.5`, `ADR-014`
- Modelo de dominio: `docs/design/domain/BC-identidad-modelo.md` (§3, §4, §6, §9)
- Candidatas: `docs/plans/inc1/inc1-candidatas.md`

---

## Notas de implementacion

> Bootstrap del primer Administrador: se crea por seed/fixture (script o migración de Alembic)
> al desplegar el entorno, no por esta US — mismo criterio que un superusuario de Django
> (`BC-identidad-modelo.md` §9, punto 4). Documentar la decisión operativa como ADR corto al
> implementar esta US si todavía no existe.

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
