# US-ADJ-42: Autoregistro de Estudiante (endpoint público)

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 5-ADJ — Identidad Autoservicio y Analytics del Docente`,
Iteración 3
**Tipo**: `feature` (backend nuevo, endpoint público)
**Bounded Context**: Identidad
**Origen**: `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 3. Modelo aprobado:
`docs/design/domain/BC-identidad-modelo.md` §13.2/13.4 (`US-ADJ-32`). Depende de
`US-ADJ-41` (mismo patrón de endpoint, hermano por perfil). `US-ADJ-43` (pantalla) sigue a
esta.

---

## Fuente de verdad UX

`docs/design/ux/wireframes-identidad-autoservicio.md` §5.1 ("Elegir perfil") y §5.3
("Autoregistro — Estudiante"). Prototipo navegable:
`docs/design/ux/prototipos/identidad-autoservicio.html` (`#autoregistro-perfil`,
`#autoregistro-estudiante`). Sin pantalla propia todavía — esta US es backend puro
(`US-ADJ-43` construye las pantallas).

---

## Descripcion (lenguaje de negocio)

Como **un Estudiante que todavía no tiene cuenta en el sistema**,
quiero **crear mi propia cuenta eligiendo mi Comisión**
para **empezar a rendir evaluaciones sin depender de una invitación de mi Docente**.

---

## Contexto del dominio

### Problema

Hoy la única forma de que un Estudiante tenga cuenta es aceptar una invitación generada por
su Docente (`RegistrarEstudianteUseCase`, `US-1.1.8`) — funciona, pero depende de que el
Docente genere y comparta el link antes. No hay una vía de autoservicio directa, análoga a la
que `US-ADJ-41` agrega para Docente.

### Alcance del fix

**Backend nuevo**, BC Identidad:

1. Comando `AutoregistrarEstudiante(nombre, email, password, comision_id)` →
   `AutoregistrarEstudianteUseCase`: valida que el email no esté en uso
   (`EmailYaRegistrado`), valida que `comision_id` corresponda a una `Comisión` existente
   (`ComisionNoExiste`, INV-ID-14 — usa `ComisionRepositoryPort.obtener_por_id()`, ya
   existente), valida `password` contra `Usuario.validar_password_nueva()` (INV-ID-11
   ampliada), crea el `Usuario` con perfil `Estudiante` vía
   `Usuario.crear_estudiante(..., comision_id)` — activo de inmediato (INV-ID-16) — y lo
   persiste. Reutiliza el mismo evento `UsuarioAutoregistrado` de `US-ADJ-41` (mismo shape,
   no hay dato adicional que el evento deba transportar — `comision_id` no forma parte de su
   payload, igual que `UsuarioCreado` tampoco lo lleva para el alta administrativa).
2. Endpoint nuevo `POST /identidad/autoregistro/estudiante` (público, sin autenticar) — body
   `{nombre, email, password, comision_id}`, responde `201 Created`.
3. Reutiliza puertos existentes: `UsuarioRepositoryPort`, `PasswordHasherPort`,
   `ComisionRepositoryPort` (los tres ya inyectados en otros use cases del mismo BC) — sin
   puertos nuevos.
4. **No** reutiliza `AutoregistrarDocenteUseCase` — mismo criterio ya documentado en
   `BC-identidad-modelo.md` §13.2 ("dos comandos, no uno con `perfil` como parámetro"): cada
   perfil tiene su propia precondición de datos (`Estudiante` exige `comision_id`, `Docente`
   no admite ninguno).

**Fuera de alcance de esta US:**
- Perfil Docente — ya cubierto por `US-ADJ-41`.
- Cualquier pantalla, incluido el selector Materia→Comisión en cascada — `US-ADJ-43`. Esta US
  solo expone el endpoint; el cliente HTTP que arme el selector ya cuenta con
  `GET /materias` (`US-2.1.9`) y `GET /materias/{id}/comisiones` (`US-4.2.2`) para poblarlo.
- Verificación de email o aprobación del Administrador — decisión de producto ya tomada
  (INV-ID-16).

---

## Especificacion del comportamiento

### Precondicion

- `AutoregistrarDocente` ya existe (`US-ADJ-41`) — no hay endpoint de autoregistro para
  Estudiante todavía.
- Existe al menos una `Comisión` creada (`US-ADJ-24`) para poder autoregistrarse.

### Postcondicion

- Un `POST /identidad/autoregistro/estudiante` con un email no usado y un `comision_id`
  existente crea un `Usuario` con perfil `Estudiante` asignado a esa comisión, activo de
  inmediato, y responde `201 Created`.
- El mismo endpoint con un email ya registrado responde `409 Conflict`, sin crear nada.
- El mismo endpoint con un `comision_id` inexistente responde `422`, sin crear nada.
- El mismo endpoint con una contraseña que no cumple INV-ID-11 responde `422`, sin crear
  nada.
- La cuenta creada puede loguearse inmediatamente y ve su Comisión como cualquier otro
  Estudiante (`GET /estudiante/materias`, ya existente).

### Invariantes

- **INV-ID-11 (ampliada):** igual que `US-ADJ-41`.
- **INV-ID-14:** `comision_id` debe corresponder a una `Comisión` existente.
- **INV-ID-15:** el autoregistro no admite perfil `Administrador`.
- **INV-ID-16:** la cuenta creada queda activa de inmediato.

---

## Criterios de aceptacion

```gherkin
Feature: Autoregistro de Estudiante (US-ADJ-42)

  Scenario: Autoregistro exitoso con datos válidos
    Given una Comisión existente
    And ningún Usuario tiene el email "estudiante.nuevo@fiuner.edu.ar"
    When se hace POST /identidad/autoregistro/estudiante con nombre, ese email, una
      contraseña que cumple INV-ID-11 y el id de esa Comisión
    Then la respuesta es 201 Created con los datos del Usuario creado
    And el Usuario tiene perfil Estudiante, queda asignado a esa Comisión y activo de
      inmediato

  Scenario: Rechazo por email ya registrado
    Given un Usuario ya existe con el email "estudiante@fiuner.edu.ar"
    When se hace POST /identidad/autoregistro/estudiante con ese mismo email
    Then la respuesta es 409 Conflict
    And no se crea ningún Usuario nuevo

  Scenario: Rechazo por comisión inexistente
    Given ningún Usuario tiene el email "estudiante.nuevo@fiuner.edu.ar"
    When se hace POST /identidad/autoregistro/estudiante con un comision_id que no existe
    Then la respuesta es 422 Unprocessable Content
    And no se crea ningún Usuario nuevo

  Scenario: Rechazo por contraseña insegura
    Given una Comisión existente
    And ningún Usuario tiene el email "estudiante.nuevo@fiuner.edu.ar"
    When se hace POST /identidad/autoregistro/estudiante con una contraseña de menos de 12
      caracteres
    Then la respuesta es 422 Unprocessable Content
    And no se crea ningún Usuario nuevo
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — reutiliza `Usuario.crear_estudiante()`/`UsuarioRepositoryPort`/
  `PasswordHasherPort`/`ComisionRepositoryPort`, todos ya existentes. Ninguna dependencia
  nueva entre BCs.

**Capa(s) afectadas:**
- [x] Entities — ninguna nueva (reutiliza `UsuarioAutoregistrado` de `US-ADJ-41`)
- [x] Use Cases — `AutoregistrarEstudianteUseCase`
- [x] Interface Adapters — controller ampliado (o método nuevo en `AutoregistroController`)
- [x] Frameworks — endpoint nuevo en el router de `US-ADJ-41`, composition root

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/use_cases/autoregistrar_estudiante.py` | Use case nuevo |
| `src/identidad/interface_adapters/controllers/autoregistro_controller.py` | Método nuevo `autoregistrar_estudiante` |
| `src/identidad/frameworks/api/autoregistro_router.py` | Endpoint `POST /identidad/autoregistro/estudiante` |
| `src/identidad/frameworks/api/schemas.py` | `AutoregistrarEstudianteRequest` |
| `src/identidad/frameworks/dependencies.py` | Composition root: cablear el nuevo use case |

---

## Referencias

- Incremento: 5-ADJ
- `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 3
- `docs/design/domain/BC-identidad-modelo.md` §13.2, §13.4
- `docs/design/ux/wireframes-identidad-autoservicio.md` §5.1, §5.3
- Issue: [#348](https://github.com/vvalotto/cognion/issues/348)
- Depende de: `US-ADJ-41`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
