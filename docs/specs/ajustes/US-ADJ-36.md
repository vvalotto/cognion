# US-ADJ-36: Contraseña segura — política ampliada

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 5-ADJ — Identidad Autoservicio y Analytics del Docente`,
Iteración 1
**Tipo**: `feature` (invariante de dominio ampliada + UI de apoyo, backend + frontend)
**Agregado principal afectado**: `Usuario` (`INV-ID-11` ampliada, sin aggregate ni comando
nuevo)
**Bounded Context**: Identidad
**Origen**: `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 1. Hallazgo 2 de
`hallazgos-cognion.md` ("Contraseña segura"). Depende de `US-ADJ-35` para el componente
`PasswordInput` (el indicador de fortaleza se agrega como ampliación de ese componente) — se
implementa después.

---

## Fuente de verdad UX

`docs/design/ux/wireframes-identidad-autoservicio.md` §2 ("Componente transversal — Mostrar/
ocultar contraseña e indicador de fortaleza"). Prototipo navegable:
`docs/design/ux/prototipos/identidad-autoservicio.html` (`#recuperar-nueva`,
`#autoregistro-docente`, `#autoregistro-estudiante` muestran el indicador en sus 3 estados).

---

## Descripcion (lenguaje de negocio)

Como **Administrador del sistema** (representando el interés de seguridad de todas las
cuentas),
quiero **exigir contraseñas más largas y con mezcla de tipos de caracteres**
para **reducir el riesgo de cuentas comprometidas por fuerza bruta o ataques de diccionario**.

---

## Contexto del dominio

### Problema

`Usuario.validar_password_nueva` (`src/identidad/entities/usuario.py:95-102`) hoy solo exige
`_LARGO_MINIMO_PASSWORD = 8` caracteres, sin ningún chequeo de complejidad — decisión original
de `RF-19` (2026-07-17), ya insuficiente según el hallazgo de Víctor.

**Gap real detectado en Fase 0, más grave que la política en sí:** de los 4 comandos que
`BC-identidad-modelo.md` (antes de esta ampliación) documentaba como cubiertos por INV-ID-11,
solo 2 la aplican de verdad. `CambiarPassword` (`use_cases/cambiar_password.py:60`) y
`ResetearPassword` (`use_cases/resetear_password.py:37`) sí llaman
`Usuario.validar_password_nueva(...)`. `CrearUsuario` (`use_cases/crear_usuario.py`) y
`RegistrarEstudiante` (`use_cases/registrar_estudiante.py`) **nunca la llaman** — hashean la
contraseña directamente (`self._hasher.hash(password)`) sin pasar por la validación de
dominio. Hoy esos dos flujos solo están protegidos por `minLength={8}` en el HTML del
frontend (`Registro.tsx`, `AltaDocente.tsx`) — un `curl` directo a `POST /usuarios` o
`POST /identidad/registro` acepta cualquier contraseña, incluida una vacía. Esta US cierra ese
gap además de subir el umbral, en vez de dejarlo para una US aparte — mismo criterio de "no
fragmentar en mini-ajustes" ya aplicado en el proyecto.

### Alcance del fix

**Backend:**

1. `src/identidad/entities/usuario.py`: `_LARGO_MINIMO_PASSWORD` pasa de `8` a `12`.
   `validar_password_nueva` agrega 3 chequeos de complejidad (al menos una mayúscula, un
   dígito, un símbolo no alfanumérico) usando expresiones regulares simples, sin librería
   nueva. Si falla la longitud, sigue lanzando `PasswordDemasiadoCorta` (mensaje actualizado a
   "al menos 12 caracteres"); si falla cualquiera de las 3 reglas de complejidad (longitud ya
   OK), lanza `PasswordSinComplejidadSuficiente` (excepción nueva).
2. `src/identidad/entities/errors.py`: agrega `PasswordSinComplejidadSuficiente(Exception)`,
   mismo patrón que `PasswordDemasiadoCorta` (sin parámetros, mensaje fijo explicando qué
   falta — o genérico "Debe incluir mayúscula, número y símbolo", a definir en la
   implementación).
3. **Cierre del gap** — agregar `Usuario.validar_password_nueva(password)` a:
   - `use_cases/crear_usuario.py`, antes de `self._hasher.hash(password)`.
   - `use_cases/registrar_estudiante.py`, antes de `self._hasher.hash(password)`.
4. Propagar las excepciones nuevas en los 4 routers que ya manejan `PasswordDemasiadoCorta` o
   que ahora empiezan a poder recibirla:
   - `frameworks/api/perfil_router.py` (ya captura `PasswordDemasiadoCorta` — agregar
     `PasswordSinComplejidadSuficiente`).
   - `frameworks/api/cuentas_router.py` (ídem).
   - `frameworks/api/usuarios_router.py` (`crear_usuario` — hoy solo captura
     `EmailYaRegistrado`, agregar ambas excepciones de password).
   - `frameworks/api/registro_router.py` (`registrar_estudiante` — hoy captura
     `EmailYaRegistrado` e `Invitacion*`, agregar ambas excepciones de password).

**Frontend:**

5. `PasswordInput` (`US-ADJ-35`) gana un prop opcional `mostrarFortaleza?: boolean` — cuando es
   `true`, renderiza debajo del input: 3 barras de fortaleza (Débil/Media/Fuerte, calculado en
   cliente sobre las mismas 4 reglas) + checklist compacto de las reglas cumplidas/faltantes.
6. Activar `mostrarFortaleza` solo en los campos de contraseña **nueva** (no en "contraseña
   actual" de `CambiarPassword`, ni en el login): `registro-password` (`Registro.tsx`),
   `password-nueva` de `CambiarPassword.tsx`, `alta-docente-password` (`AltaDocente.tsx`),
   `password-nueva` de `cuentas/ResetearPassword.tsx`.
7. Los `minLength={8}` hardcodeados en `Registro.tsx`/`AltaDocente.tsx` pasan a `minLength={12}`
   — mensaje de ayuda (`hint`) actualizado en los 4 formularios afectados para reflejar las
   reglas nuevas.

**Fuera de alcance de esta US:**
- `ConfirmarNuevaPassword`, `AutoregistrarDocente`, `AutoregistrarEstudiante` — comandos
  modelados en `BC-identidad-modelo.md` §13 pero implementados recién en las Iteraciones 2 y 3
  de este incremento; cuando se implementen, deben llamar a `validar_password_nueva` ya
  ampliada por esta US, sin duplicar la regla.
- Historial de contraseñas usadas / prohibir reutilizar la anterior — no pedido.

---

## Especificacion del comportamiento

### Precondicion

- `_LARGO_MINIMO_PASSWORD = 8`, sin chequeo de complejidad.
- `CrearUsuario` y `RegistrarEstudiante` no invocan `validar_password_nueva` — aceptan
  cualquier contraseña del lado del dominio.

### Postcondicion

- Una contraseña nueva menor a 12 caracteres es rechazada en los 7 comandos que la fijan
  (`CrearUsuario`, `RegistrarEstudiante`, `CambiarPassword`, `ResetearPassword`, y los 3 de
  `US-ADJ-32` cuando existan) con `PasswordDemasiadoCorta`.
- Una contraseña de 12+ caracteres sin mayúscula, número o símbolo es rechazada con
  `PasswordSinComplejidadSuficiente`.
- `POST /usuarios` (alta de Docente) y `POST /identidad/registro` (registro de Estudiante)
  ahora rechazan contraseñas inválidas del lado del backend, no solo del cliente.
- Los campos de contraseña nueva del frontend muestran el indicador de fortaleza en tiempo
  real mientras se tipea.

### Invariantes

- **INV-ID-11 (ampliada):** toda contraseña nueva (`CrearUsuario`, `RegistrarEstudiante`,
  `CambiarPassword`, `ResetearPassword`, y en el futuro `ConfirmarNuevaPassword`,
  `AutoregistrarDocente`, `AutoregistrarEstudiante`) debe tener mínimo 12 caracteres y al
  menos una mayúscula, un número y un símbolo.

---

## Criterios de aceptacion

```gherkin
Feature: Contraseña segura — política ampliada (US-ADJ-36)

  Scenario: Contraseña demasiado corta rechazada en Cambiar contraseña
    Given un usuario autenticado intenta cambiar su contraseña
    When la contraseña nueva tiene menos de 12 caracteres
    Then el sistema rechaza con "PasswordDemasiadoCorta"

  Scenario: Contraseña larga pero sin complejidad rechazada
    Given un usuario autenticado intenta cambiar su contraseña
    When la contraseña nueva tiene 12+ caracteres pero sin ningún número
    Then el sistema rechaza con "PasswordSinComplejidadSuficiente"

  Scenario: Alta de Docente ahora valida contraseña del lado del backend
    Given un Administrador da de alta un Docente
    When la contraseña temporal no cumple la política (ej. "abc123", vía llamado directo a la API)
    Then el sistema la rechaza — antes de esta US, este flujo no tenía ninguna validación de dominio

  Scenario: Registro de Estudiante ahora valida contraseña del lado del backend
    Given un Estudiante se registra con un link de invitación válido
    When la contraseña elegida no cumple la política
    Then el sistema la rechaza — antes de esta US, este flujo no tenía ninguna validación de dominio

  Scenario: Indicador de fortaleza en tiempo real
    Given un usuario está completando el campo "Contraseña nueva" en cualquier formulario que lo tenga
    When tipea una contraseña que cumple las 4 reglas
    Then el indicador muestra "Fuerte" con las 3 barras activas
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] Sí
- [x] No — amplía una invariante de dominio ya existente (`INV-ID-11`), sin aggregate ni
  comando nuevo. El cierre del gap (`CrearUsuario`/`RegistrarEstudiante`) es agregar una
  llamada ya usada en otros 2 Use Cases del mismo BC, mismo patrón.

**Capa(s) afectadas:**
- [x] Backend — `entities/usuario.py`, `entities/errors.py`, `use_cases/crear_usuario.py`,
  `use_cases/registrar_estudiante.py`, 4 routers (`perfil_router.py`, `cuentas_router.py`,
  `usuarios_router.py`, `registro_router.py`)
- [x] Frontend — `components/PasswordInput.tsx` (prop nuevo), 4 pantallas (activan el prop +
  `minLength`/hint actualizados)

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/entities/usuario.py` | `_LARGO_MINIMO_PASSWORD` → 12, chequeos de complejidad nuevos |
| `src/identidad/entities/errors.py` | `PasswordSinComplejidadSuficiente` (nueva) |
| `src/identidad/use_cases/crear_usuario.py` | Agrega `Usuario.validar_password_nueva(password)` |
| `src/identidad/use_cases/registrar_estudiante.py` | Agrega `Usuario.validar_password_nueva(password)` |
| `src/identidad/frameworks/api/perfil_router.py` | Captura `PasswordSinComplejidadSuficiente` |
| `src/identidad/frameworks/api/cuentas_router.py` | Captura `PasswordSinComplejidadSuficiente` |
| `src/identidad/frameworks/api/usuarios_router.py` | Captura ambas excepciones de password (nuevo) |
| `src/identidad/frameworks/api/registro_router.py` | Captura ambas excepciones de password (nuevo) |
| `frontend/src/components/PasswordInput.tsx` | Prop `mostrarFortaleza?: boolean` |
| `frontend/src/pages/identidad/Registro.tsx` | `minLength={12}`, activa indicador, hint actualizado |
| `frontend/src/pages/identidad/CambiarPassword.tsx` | Activa indicador en "nueva", hint actualizado |
| `frontend/src/pages/identidad/AltaDocente.tsx` | `minLength={12}`, activa indicador, hint actualizado |
| `frontend/src/pages/cuentas/ResetearPassword.tsx` | `minLength={12}` (nuevo), activa indicador, hint actualizado |

---

## Referencias

- Incremento: 5-ADJ
- `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 1
- `docs/design/domain/BC-identidad-modelo.md` §13.4 (`INV-ID-11` ampliada)
- `docs/design/ux/wireframes-identidad-autoservicio.md` §2
- Issue: [#330](https://github.com/vvalotto/cognion/issues/330)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
