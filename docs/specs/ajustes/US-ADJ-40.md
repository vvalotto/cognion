# US-ADJ-40: Pantallas de recuperación de contraseña

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 5-ADJ — Identidad Autoservicio y Analytics del Docente`,
Iteración 2
**Tipo**: `feature` (frontend, consume backend nuevo)
**Bounded Context**: Identidad (frontend)
**Origen**: `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 2. Depende de `US-ADJ-38`
y `US-ADJ-39` (endpoints ya deben existir).

---

## Fuente de verdad UX

`docs/design/ux/wireframes-identidad-autoservicio.md` §3.1 (link "¿Olvidaste tu contraseña?"
en Login), §4 completo (las 5 pantallas de recuperación), §2 (toggle mostrar/ocultar +
indicador de fortaleza, ya implementado como `PasswordInput`, `US-ADJ-35`/`36`). Prototipo
navegable: `docs/design/ux/prototipos/identidad-autoservicio.html` (`#recuperar-solicitar`,
`#recuperar-solicitado`, `#recuperar-nueva`, `#recuperar-token-invalido`, `#recuperar-exito`).

---

## Descripcion (lenguaje de negocio)

Como **cualquier persona que olvidó su contraseña**,
quiero **pedir un link de recuperación desde la pantalla de login y usarlo para definir una
contraseña nueva**
para **recuperar el acceso a mi cuenta sin depender de un Administrador**.

---

## Contexto del dominio

### Problema

`US-ADJ-38`/`39` dejan los endpoints funcionando, pero sin ninguna pantalla que los consuma —
sin esta US, la recuperación de contraseña solo es accesible por HTTP directo (Swagger/curl).

### Alcance del fix

**Frontend puro**, consume los endpoints ya existentes:

1. `Login.tsx`: agrega el link "¿Olvidaste tu contraseña?" (§3.1) que navega a
   `/recuperar-password`.
2. Pantalla nueva `RecuperarPasswordSolicitar.tsx` (ruta `/recuperar-password`, pública, sin
   `RequireRole`): campo Email, botón "Enviar link de recuperación", llama
   `POST /identidad/recuperar-password/solicitar`. Al responder (siempre `202`, éxito o no),
   navega a la pantalla de confirmación §4.2 con el mensaje genérico — **nunca** distingue en
   la UI si el email existía o no (mismo criterio del backend, INV-ID-17).
3. Pantalla nueva `RecuperarPasswordSolicitado.tsx`: mensaje genérico + aclaración de vigencia
   (1 hora) + link "Volver a iniciar sesión".
4. Pantalla nueva `RecuperarPasswordNueva.tsx` (ruta `/recuperar-password/:token`, pública): dos
   campos `PasswordInput` (contraseña nueva con indicador de fortaleza, confirmar contraseña),
   validación de cliente de las 4 reglas de INV-ID-11 + coincidencia entre ambos campos, botón
   "Guardar nueva contraseña", llama `POST /identidad/recuperar-password/confirmar`.
   - Éxito → navega a §4.5 (`RecuperarPasswordExito.tsx`).
   - Error `TokenRecuperacionVencido`/`TokenRecuperacionInvalido`/`TokenRecuperacionYaUsado`
     (cualquiera de los tres, sin distinguir en la UI, mismo criterio del wireframe) → navega a
     §4.4 (`RecuperarPasswordTokenInvalido.tsx`), con link "Pedir un nuevo link" que vuelve a
     `/recuperar-password`.
   - Error de política de contraseña (`PasswordDemasiadoCorta`/
     `PasswordSinComplejidadSuficiente`) → error inline en el formulario, sin navegar (mismo
     patrón que `CambiarPassword.tsx`).
5. Pantalla nueva `RecuperarPasswordExito.tsx`: confirmación + botón "Iniciar sesión" que
   navega a `/login`.
6. Cliente API: agrega `solicitarRecuperacionPassword(email)` y
   `confirmarNuevaPassword(token, passwordNueva)` al cliente ya existente de Identidad
   (mismo patrón que el resto de `identidad-api.ts`/equivalente, sin manejo de sesión — estos
   endpoints son públicos, no requieren JWT).

**Fuera de alcance de esta US:**
- Los endpoints de backend — ya existen desde `US-ADJ-38`/`39`.
- Cualquier cambio a `Login.tsx` más allá del link nuevo.

---

## Especificacion del comportamiento

### Precondicion

- `POST /identidad/recuperar-password/solicitar` y `POST /identidad/recuperar-password/confirmar`
  existen y funcionan (verificado por HTTP directo desde `US-ADJ-38`/`39`).
- No existe ninguna pantalla de recuperación de contraseña.
- `Login.tsx` no tiene ningún link hacia recuperación.

### Postcondicion

- Desde `/login`, un clic en "¿Olvidaste tu contraseña?" lleva a `/recuperar-password`.
- Completar el formulario de solicitud con cualquier email (exista o no la cuenta) navega
  siempre a la misma pantalla de confirmación genérica.
- El link del email (`/recuperar-password/:token`) lleva al formulario de nueva contraseña.
- Un token vencido/inválido/ya usado muestra la pantalla de error correspondiente, sin
  formulario de contraseña.
- Una contraseña nueva válida con un token vigente termina en la pantalla de éxito y permite
  loguear con la contraseña nueva.

### Invariantes

N/A — frontend puro, valida contra las reglas ya impuestas por el backend (INV-ID-11, INV-ID-13).

---

## Criterios de aceptacion

```gherkin
Feature: Pantallas de recuperación de contraseña (US-ADJ-40)

  Scenario: Navegar desde el login
    Given la pantalla de Login
    When se hace clic en "¿Olvidaste tu contraseña?"
    Then la pantalla actual es /recuperar-password

  Scenario: Solicitar recuperación con cualquier email
    Given la pantalla de solicitar recuperación
    When se ingresa un email cualquiera y se hace clic en "Enviar link de recuperación"
    Then la pantalla actual muestra el mensaje genérico de "si el email corresponde a una cuenta..."

  Scenario: Definir nueva contraseña con un token vigente
    Given un link de recuperación con un token vigente
    When se ingresa una contraseña nueva válida y su confirmación coincide
    And se hace clic en "Guardar nueva contraseña"
    Then la pantalla actual es la de éxito
    And un login posterior con la contraseña nueva es exitoso

  Scenario: Token vencido o inválido
    Given un link de recuperación con un token vencido, inválido, o ya usado
    When se abre ese link
    Then la pantalla muestra "Este link ya no es válido"
    And no se muestra ningún formulario de contraseña
    And hay un link "Pedir un nuevo link" que vuelve a /recuperar-password

  Scenario: Contraseña nueva que no cumple la política
    Given un link de recuperación con un token vigente
    When se ingresa una contraseña de menos de 12 caracteres
    Then se muestra un error inline en el formulario
    And la pantalla sigue siendo la de definir nueva contraseña
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] Sí
- [x] No — reutiliza `PasswordInput` (`US-ADJ-35`/`36`) y el patrón de cliente API ya
  existente, sin librerías nuevas.

**Capa(s) afectadas:**
- [x] Frontend — 4 pantallas nuevas, 1 link en `Login.tsx`, cliente API ampliado

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/pages/Login.tsx` | Agrega link "¿Olvidaste tu contraseña?" |
| `frontend/src/pages/RecuperarPasswordSolicitar.tsx` | Pantalla nueva |
| `frontend/src/pages/RecuperarPasswordSolicitado.tsx` | Pantalla nueva |
| `frontend/src/pages/RecuperarPasswordNueva.tsx` | Pantalla nueva |
| `frontend/src/pages/RecuperarPasswordTokenInvalido.tsx` | Pantalla nueva |
| `frontend/src/pages/RecuperarPasswordExito.tsx` | Pantalla nueva |
| `frontend/src/lib/identidad-api.ts` (o equivalente) | `solicitarRecuperacionPassword()`, `confirmarNuevaPassword()` |
| `frontend/src/router.tsx` | 3 rutas públicas nuevas (`/recuperar-password`, `/recuperar-password/:token`, y la de éxito si tiene ruta propia) |

---

## Referencias

- Incremento: 5-ADJ
- `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 2
- `docs/design/ux/wireframes-identidad-autoservicio.md` §3.1, §4
- Issue: [#341](https://github.com/vvalotto/cognion/issues/341)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
