# US-ADJ-41: Autoregistro de Docente (endpoint público)

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 5-ADJ — Identidad Autoservicio y Analytics del Docente`,
Iteración 3
**Tipo**: `feature` (backend nuevo, endpoint público)
**Bounded Context**: Identidad
**Origen**: `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 3. Modelo aprobado:
`docs/design/domain/BC-identidad-modelo.md` §13.2/13.4 (`US-ADJ-32`). Primera de la
Iteración — `US-ADJ-42` (Estudiante) y `US-ADJ-43` (pantalla) siguen a esta.

---

## Fuente de verdad UX

`docs/design/ux/wireframes-identidad-autoservicio.md` §5.1 ("Elegir perfil") y §5.2
("Autoregistro — Docente"). Prototipo navegable:
`docs/design/ux/prototipos/identidad-autoservicio.html` (`#autoregistro-perfil`,
`#autoregistro-docente`). Sin pantalla propia todavía — esta US es backend puro
(`US-ADJ-43` construye las pantallas).

---

## Descripcion (lenguaje de negocio)

Como **un Docente que todavía no tiene cuenta en el sistema**,
quiero **crear mi propia cuenta sin depender de que un Administrador me dé de alta**
para **empezar a usar la plataforma sin fricción**.

---

## Contexto del dominio

### Problema

Hoy la única forma de que un Docente tenga cuenta es que el Administrador lo cree
(`US-1.1.9`/`CrearUsuarioUseCase`, requiere autenticación con rol `administrador`). No hay
autoservicio — mismo gap de producto que motivó la recuperación de contraseña
(`US-ADJ-38`/`39`/`40`).

### Alcance del fix

**Backend nuevo**, BC Identidad:

1. Evento nuevo `UsuarioAutoregistrado` (`entities/eventos.py`) — mismo shape que
   `UsuarioCreado` (`usuario_id`, `email`, `tipo_perfil`), pero distinto tipo: el modelo de
   dominio (`BC-identidad-modelo.md` §13.2) especifica un comando y evento propios para
   distinguir el autoservicio (sin autenticar) del alta administrativa (`CrearUsuario`,
   autenticada, rol `administrador`).
2. Comando `AutoregistrarDocente(nombre, email, password)` → `AutoregistrarDocenteUseCase`:
   valida que el email no esté en uso (`EmailYaRegistrado`), valida `password` contra
   `Usuario.validar_password_nueva()` (INV-ID-11 ampliada), crea el `Usuario` con perfil
   `Docente` vía `Usuario.crear(..., TipoPerfil.DOCENTE)` — **activo de inmediato**
   (`bloqueada=False`, sin estado pendiente, INV-ID-16) — y lo persiste.
3. Endpoint nuevo `POST /identidad/autoregistro/docente` (público, sin `Depends` de
   autenticación) — body `{nombre, email, password}`, responde `201 Created` con los datos
   del usuario creado.
4. Reutiliza en su totalidad los puertos existentes (`UsuarioRepositoryPort`,
   `PasswordHasherPort`) — no hay puertos nuevos, mismo criterio que `RegistrarEstudiante`
   reutiliza `PasswordHasherPort`.

**Fuera de alcance de esta US:**
- Perfil Estudiante (requiere `comision_id`, selector Materia→Comisión) — `US-ADJ-42`.
- Cualquier pantalla — `US-ADJ-43`.
- Verificación de email o aprobación del Administrador — decisión de producto ya tomada
  (`BC-identidad-modelo.md` §13.4, INV-ID-16: activo de inmediato, sin verificación).

---

## Especificacion del comportamiento

### Precondicion

- No existe ningún mecanismo de autoservicio de alta de cuenta — el único camino para un
  Docente es que un Administrador lo cree (`CrearUsuario`, autenticado).

### Postcondicion

- Un `POST /identidad/autoregistro/docente` con un email no usado crea un `Usuario` con
  perfil `Docente`, activo de inmediato, y responde `201 Created`.
- El mismo endpoint con un email ya registrado responde `409 Conflict`, sin crear nada.
- El mismo endpoint con una contraseña que no cumple INV-ID-11 responde `422`, sin crear
  nada.
- La cuenta creada puede loguearse inmediatamente con `POST /identidad/login` — mismo
  comportamiento que cualquier otra cuenta `Docente` ya existente.

### Invariantes

- **INV-ID-11 (ampliada):** la contraseña debe cumplir mínimo 12 caracteres + mayúscula +
  número + símbolo — igual que el resto de los comandos que fijan contraseña.
- **INV-ID-15:** el autoregistro no admite perfil `Administrador` — este endpoint es
  exclusivo de `Docente` (el de `Estudiante` es un endpoint hermano, `US-ADJ-42`).
- **INV-ID-16:** la cuenta creada queda activa de inmediato (`bloqueada=False`), sin
  aprobación ni verificación de email.

---

## Criterios de aceptacion

```gherkin
Feature: Autoregistro de Docente (US-ADJ-41)

  Scenario: Autoregistro exitoso con datos válidos
    Given ningún Usuario tiene el email "docente.nuevo@fiuner.edu.ar"
    When se hace POST /identidad/autoregistro/docente con nombre, ese email y una
      contraseña que cumple INV-ID-11
    Then la respuesta es 201 Created con los datos del Usuario creado
    And el Usuario tiene perfil Docente y queda activo de inmediato

  Scenario: Rechazo por email ya registrado
    Given un Usuario ya existe con el email "docente@fiuner.edu.ar"
    When se hace POST /identidad/autoregistro/docente con ese mismo email
    Then la respuesta es 409 Conflict
    And no se crea ningún Usuario nuevo

  Scenario: Rechazo por contraseña insegura
    Given ningún Usuario tiene el email "docente.nuevo@fiuner.edu.ar"
    When se hace POST /identidad/autoregistro/docente con una contraseña de menos de 12
      caracteres
    Then la respuesta es 422 Unprocessable Content
    And no se crea ningún Usuario nuevo

  Scenario: La cuenta autoregistrada puede loguearse de inmediato
    Given un Docente se autoregistró exitosamente
    When hace POST /identidad/login con ese email y esa contraseña
    Then la respuesta es 200 OK con un JWT válido
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — reutiliza el mismo patrón de alta de usuario ya existente
  (`Usuario.crear()`/`UsuarioRepositoryPort`/`PasswordHasherPort`), solo cambia el actor (sin
  autenticar) y el evento emitido. Ninguna dependencia nueva entre BCs.

**Capa(s) afectadas:**
- [x] Entities — evento `UsuarioAutoregistrado`
- [x] Use Cases — `AutoregistrarDocenteUseCase`
- [x] Interface Adapters — controller/endpoint nuevo
- [x] Frameworks — router público, composition root

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/entities/eventos.py` | Evento nuevo `UsuarioAutoregistrado` |
| `src/identidad/use_cases/autoregistrar_docente.py` | Use case nuevo |
| `src/identidad/interface_adapters/controllers/autoregistro_controller.py` | Controller nuevo |
| `src/identidad/frameworks/api/autoregistro_router.py` | Endpoint `POST /identidad/autoregistro/docente` |
| `src/identidad/frameworks/api/schemas.py` | `AutoregistrarDocenteRequest`/`AutoregistroResponse` |
| `src/identidad/frameworks/dependencies.py` | Composition root: cablear el nuevo use case/controller |
| `src/app.py` | Registrar el router nuevo |

---

## Referencias

- Incremento: 5-ADJ
- `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 3
- `docs/design/domain/BC-identidad-modelo.md` §13.2, §13.4
- `docs/design/ux/wireframes-identidad-autoservicio.md` §5.1, §5.2
- Issue: [#347](https://github.com/vvalotto/cognion/issues/347)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
