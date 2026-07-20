# US-1.1.3: Estudiante intenta registrarse con link vencido o inválido

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-1.1`
**Tipo**: `feat backend` + `feat frontend`
**Agregado principal afectado**: `Invitación`
**Bounded Context**: Identidad

---

## Descripcion (lenguaje de negocio)

Como **Estudiante** que intenta usar un link de invitación que ya no es válido,
quiero **recibir un rechazo explícito y comprensible**
para **entender que no puedo completar el registro y que debo pedirle al docente un nuevo
link, sin esperar una recuperación automática (`ADR-012`)**.

---

## Contexto del dominio

### Problema

`ADR-012` decidió explícitamente que no hay mecanismo de recuperación automática ante un link
vencido o inválido — ni reenvío ni extensión de vigencia. Esta US cubre el camino de rechazo
del mismo comando que `US-1.1.2`, con su propia postcondición y su propia pantalla.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Aggregate | `Invitación` | Se consulta; determina el motivo del rechazo |
| Command | `RegistrarEstudiante(token, datos_usuario)` | Mismo comando que `US-1.1.2`, camino de rechazo |
| — | `RegistroRechazado` | **No** es un evento de dominio persistido — excepción de aplicación (`BC-identidad-modelo.md` §5, hot spot 2) |

---

## Especificacion del comportamiento

### Precondicion

- Se recibe un `token` que no corresponde a ninguna `Invitación` existente, **o**
- Corresponde a una `Invitación` con `expira_en` ya pasado, **o**
- Corresponde a una `Invitación` con `usada_en` no null.

### Postcondicion

- El sistema responde con un error explícito (4xx) — `InvitacionInvalida`, `InvitacionVencida`
  o `InvitacionYaUsada` según el caso.
- Ningún `Usuario` se crea.
- No se persiste ningún evento de dominio — el rechazo es una excepción de aplicación, no un
  evento del Event Store (`BC-identidad-modelo.md` §5, hot spot 2).

### Invariantes

| ID | Invariante |
|----|------------|
| INV-ID-03 | Una invitación es válida para aceptar solo si `ahora < expira_en` y `usada_en is null` — fuera de esa ventana, rechazo sin recuperación automática (`ADR-012`). |
| INV-ID-01 | Una invitación con `usada_en` no null no puede volver a aceptarse (uso único). |
| — | Sin mecanismo de reenvío o extensión automática de una invitación rechazada — el Docente debe generar una invitación nueva (`ADR-012`, `US-1.1.1`). |

---

## Criterios de aceptacion

```gherkin
Feature: Rechazo de registro con invitación no válida

  Scenario: Token inexistente
    Given un token que no corresponde a ninguna Invitación
    When el Estudiante ejecuta RegistrarEstudiante(token, datos_usuario)
    Then el sistema rechaza la operación con InvitacionInvalida
    And ningún Usuario se crea

  Scenario: Invitación vencida
    Given una Invitación cuyo expira_en ya pasó
    When el Estudiante ejecuta RegistrarEstudiante con ese token
    Then el sistema rechaza la operación con InvitacionVencida
    And ningún Usuario se crea

  Scenario: Invitación ya usada
    Given una Invitación con usada_en distinto de null
    When el Estudiante ejecuta RegistrarEstudiante con ese token
    Then el sistema rechaza la operación con InvitacionYaUsada
    And ningún Usuario se crea

  Scenario: La UI no distingue el motivo del rechazo
    Given cualquiera de los tres rechazos anteriores
    When se muestra el mensaje al Estudiante
    Then el mensaje es el mismo para los tres casos ("Este link ya no es válido")
    And no se muestra el formulario de registro
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — decisión ya tomada en `ADR-012`

**Capa(s) afectadas:**
- [x] Entities — validación de `Invitación` (comparte código con `US-1.1.2`)
- [x] Use Cases — mismo `RegistrarEstudianteUseCase` de `US-1.1.2`, camino de excepción
- [x] Interface Adapters — mapeo de excepciones a respuesta HTTP 4xx
- [x] Frameworks — mismo endpoint FastAPI de `US-1.1.2`
- [x] Frontend — pantalla de error

---

## Fuente de verdad UX

- `docs/design/ux/wireframes-identidad.md` §2.4 (Registro — link vencido/inválido).
- Prototipo: `docs/design/ux/prototipos/identidad-registro-login.html` (`#registro-error`).
- Nota explícita del wireframe: no se distingue en la UI entre vencido/inválido/usado — mismo
  mensaje para los tres casos (decisión de simplicidad; el backend sí distingue las tres
  excepciones para logging/debug).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/entities/invitacion.py` | Lógica de validación de vigencia (compartida con `US-1.1.2`) |
| `src/identidad/entities/excepciones.py` | `InvitacionInvalida`, `InvitacionVencida`, `InvitacionYaUsada` |
| `src/identidad/use_cases/registrar_estudiante.py` | Camino de rechazo del mismo use case de `US-1.1.2` |
| `src/identidad/interface_adapters/controllers/registro_controller.py` | Mapeo de excepciones a 4xx (mismo controller de `US-1.1.2`) |
| `frontend/src/features/identidad/RegistroError.tsx` | Pantalla `#registro-error` |

---

## Referencias

- Relacionada con: `US-1.1.1`, `US-1.1.2`, `ADR-012`
- Modelo de dominio: `docs/design/domain/BC-identidad-modelo.md` (§3, §4 `Invitación`, §5 hot spot 2)
- Candidatas: `docs/plans/inc1/inc1-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
