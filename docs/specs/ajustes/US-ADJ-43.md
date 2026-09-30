# US-ADJ-43: Pantallas de autoregistro con selección de perfil

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 5-ADJ — Identidad Autoservicio y Analytics del Docente`,
Iteración 3
**Tipo**: `feature` (frontend nuevo, consume backend existente)
**Bounded Context**: Identidad (frontend)
**Origen**: `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 3. Modelo aprobado:
`docs/design/domain/BC-identidad-modelo.md` §13.2/13.4. Depende de `US-ADJ-41` y `US-ADJ-42`
(los dos endpoints ya deben existir).

---

## Fuente de verdad UX

`docs/design/ux/wireframes-identidad-autoservicio.md` §5 completo ("Pantallas —
Autoregistro con selección de perfil": §5.1 elegir perfil, §5.2 Docente, §5.3 Estudiante,
§5.4 éxito) y §7 (responsive). Prototipo navegable:
`docs/design/ux/prototipos/identidad-autoservicio.html`
(`#autoregistro-perfil`/`#autoregistro-docente`/`#autoregistro-estudiante`/
`#autoregistro-exito`).

---

## Descripcion (lenguaje de negocio)

Como **un Docente o Estudiante sin cuenta**,
quiero **crear mi cuenta desde la pantalla de login, eligiendo mi perfil**
para **no depender de una invitación ni de un Administrador**.

---

## Contexto del dominio

### Problema

`US-ADJ-41`/`US-ADJ-42` ya exponen los endpoints de autoregistro, pero no hay ninguna
pantalla que los use — el único camino visible en la UI para tener cuenta sigue siendo la
invitación (`Registro.tsx`) o el alta por Administrador. Falta el punto de entrada y el flujo
completo de autoservicio en el frontend.

### Alcance del fix

**Frontend nuevo**, sin cambios de backend — consume `POST /identidad/autoregistro/docente`
(`US-ADJ-41`), `POST /identidad/autoregistro/estudiante` (`US-ADJ-42`), `GET /materias`
(`US-2.1.9`, ya consumido por `identidad-comisiones-api.ts`/similares) y
`GET /materias/{id}/comisiones` (`US-4.2.2`, ya consumido en
`DesempenoPorAlumno.tsx`/`DesempenoPorTema.tsx` vía `identidad-comisiones-api.ts`).

1. **Cliente API** (`frontend/src/lib/identidad-autoregistro-api.ts` o ampliación del
   cliente de auth existente): `autoregistrarDocente(nombre, email, password)` y
   `autoregistrarEstudiante(nombre, email, password, comisionId)`, mapeando errores 409/422
   a mensajes de UI (mismo patrón que `Registro.tsx` ya resuelve para `EmailYaRegistrado`).
2. **`AutoregistroPerfil.tsx`** (`#autoregistro-perfil`): dos tarjetas ("Soy Docente" / "Soy
   Estudiante"), sin tercera opción de Administrador (INV-ID-15). Link "¿Ya tenés cuenta?
   Iniciar sesión".
3. **`AutoregistroDocente.tsx`** (`#autoregistro-docente`): tag "Perfil: Docente"
   (informativo), campos Nombre/Email/Contraseña (`PasswordInput.tsx` de `US-ADJ-35`, con
   indicador de fortaleza de `US-ADJ-36`)/Confirmar contraseña, copy "Tu cuenta queda activa
   de inmediato", acción "Crear cuenta", link "‹ Elegir otro perfil".
4. **`AutoregistroEstudiante.tsx`** (`#autoregistro-estudiante`): tag "Perfil: Estudiante",
   selector Materia→Comisión en cascada **antes** de los datos personales (mismo orden que
   `wireframes-identidad-autoservicio.md` §5.3 especifica), luego
   Nombre/Email/Contraseña/Confirmar, acción "Crear cuenta", link "‹ Elegir otro perfil".
5. **`AutoregistroExito.tsx`** (`#autoregistro-exito`): pantalla única para ambos perfiles —
   "Cuenta creada. Tu cuenta ya está activa. Iniciá sesión para continuar.", sin login
   automático (mismo criterio que `RegistroExito.tsx`), acción "Iniciar sesión".
6. **Rutas nuevas en `router.tsx`** (públicas, sin `RequireRole`):
   `/autoregistro` → `AutoregistroPerfil`, `/autoregistro/docente` → `AutoregistroDocente`,
   `/autoregistro/estudiante` → `AutoregistroEstudiante`, `/autoregistro/exito` →
   `AutoregistroExito`.
7. **Link nuevo en `Login.tsx`**: "¿No tenés cuenta? Registrate" (footer, mismo patrón visual
   que el link "¿Olvidaste tu contraseña?" de `US-ADJ-38`), navega a `/autoregistro`.

**Fuera de alcance de esta US:**
- Cualquier cambio de backend — los dos endpoints ya existen.
- Verificación de email o aprobación — decisión de producto ya tomada, sin UI para eso.

---

## Especificacion del comportamiento

### Precondicion

- `POST /identidad/autoregistro/docente` y `POST /identidad/autoregistro/estudiante` existen
  y responden según `US-ADJ-41`/`US-ADJ-42`.
- No hay ninguna pantalla ni link que lleve a un flujo de autoregistro.

### Postcondicion

- Desde `/login`, un click en "¿No tenés cuenta? Registrate" lleva a `/autoregistro`.
- Elegir "Soy Docente" lleva a `/autoregistro/docente`; completar el formulario y enviarlo
  crea la cuenta y navega a `/autoregistro/exito`.
- Elegir "Soy Estudiante" lleva a `/autoregistro/estudiante`; el selector de Comisión se
  puebla en cascada desde Materia; completar el formulario y enviarlo crea la cuenta y
  navega a `/autoregistro/exito`.
- Un email ya registrado (409) o una contraseña insegura (422) se muestran como error en el
  propio formulario, sin navegar.
- Desde `/autoregistro/exito`, "Iniciar sesión" lleva a `/login`, donde la cuenta recién
  creada puede loguearse.

### Invariantes

- Ninguna nueva — el frontend no valida invariantes de dominio, solo refleja los errores que
  ya devuelve el backend (`US-ADJ-41`/`US-ADJ-42`).

---

## Criterios de aceptacion

```gherkin
Feature: Pantallas de autoregistro (US-ADJ-43)

  Scenario: Autoregistro exitoso como Docente
    Given estoy en /login
    When hago click en "¿No tenés cuenta? Registrate"
    And elijo "Soy Docente"
    And completo el formulario con datos válidos y lo envío
    Then veo la pantalla de éxito
    And puedo iniciar sesión con esas credenciales

  Scenario: Autoregistro exitoso como Estudiante
    Given estoy en /autoregistro
    When elijo "Soy Estudiante"
    And selecciono una Materia y luego una Comisión
    And completo el formulario con datos válidos y lo envío
    Then veo la pantalla de éxito
    And puedo iniciar sesión con esas credenciales

  Scenario: Rechazo por email ya registrado
    Given estoy en /autoregistro/docente
    When envío el formulario con un email ya registrado
    Then veo un mensaje de error en la propia pantalla
    And no navego a la pantalla de éxito

  Scenario: Volver a elegir perfil
    Given estoy en /autoregistro/docente
    When hago click en "‹ Elegir otro perfil"
    Then vuelvo a /autoregistro
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — frontend puro, mismo patrón de cliente API + pantalla + ruta pública ya usado en
  `US-ADJ-38`/`39`/`40` (recuperación de contraseña) y `US-1.1.8` (registro por invitación).

**Capa(s) afectadas:**
- [x] Frontend únicamente (`frontend/src/pages/identidad/`, `frontend/src/lib/`,
  `frontend/src/router.tsx`)

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/lib/identidad-autoregistro-api.ts` | Cliente API nuevo |
| `frontend/src/pages/identidad/AutoregistroPerfil.tsx` | Pantalla nueva |
| `frontend/src/pages/identidad/AutoregistroDocente.tsx` | Pantalla nueva |
| `frontend/src/pages/identidad/AutoregistroEstudiante.tsx` | Pantalla nueva |
| `frontend/src/pages/identidad/AutoregistroExito.tsx` | Pantalla nueva |
| `frontend/src/pages/identidad/Login.tsx` | Link nuevo "¿No tenés cuenta? Registrate" |
| `frontend/src/router.tsx` | 4 rutas nuevas, públicas |

---

## Referencias

- Incremento: 5-ADJ
- `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 3
- `docs/design/domain/BC-identidad-modelo.md` §13.2, §13.4
- `docs/design/ux/wireframes-identidad-autoservicio.md` §5, §7
- Issue: [#349](https://github.com/vvalotto/cognion/issues/349)
- Depende de: `US-ADJ-41`, `US-ADJ-42`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
