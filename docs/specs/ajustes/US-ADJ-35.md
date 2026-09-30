# US-ADJ-35: Toggle mostrar/ocultar contraseña

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 5-ADJ — Identidad Autoservicio y Analytics del Docente`,
Iteración 1
**Tipo**: `feature` (componente compartido nuevo, frontend puro)
**Bounded Context**: ninguno específico — componente transversal de UI
**Origen**: `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 1. Hallazgo 1 de
`hallazgos-cognion.md` ("Mostrar contraseña"). Independiente de `US-ADJ-36`/`37` — sin orden
obligatorio entre las tres.

---

## Fuente de verdad UX

`docs/design/ux/wireframes-identidad-autoservicio.md` §2 ("Componente transversal — Mostrar/
ocultar contraseña e indicador de fortaleza"). Prototipo navegable:
`docs/design/ux/prototipos/identidad-autoservicio.html` — todos los campos de contraseña del
prototipo ya muestran el patrón (botón 👁, alterna a 🙈 al activarse).

---

## Descripcion (lenguaje de negocio)

Como **cualquier usuario que completa un formulario con contraseña** (login, registro, cambio,
reseteo, alta de Docente),
quiero **poder mostrar temporalmente lo que tipeé**
para **verificar que no me equivoqué antes de enviar, sin tener que escribirla dos veces a
ciegas**.

---

## Contexto del dominio

### Problema

Ninguno de los 10 inputs `type="password"` del sistema (repartidos en 5 pantallas) tiene forma
de revisar lo tipeado. Cada pantalla repite el mismo patrón `<Label>` + `<Input
type="password">` de forma independiente, sin componente compartido — agregar el toggle a mano
en cada una duplicaría la misma lógica 10 veces.

Relevamiento exacto de los campos a reemplazar:

| Archivo | Inputs `type="password"` |
|---|---|
| `frontend/src/pages/identidad/Login.tsx` | 1 — `login-password` |
| `frontend/src/pages/identidad/Registro.tsx` | 2 — `registro-password`, `registro-confirmar-password` |
| `frontend/src/pages/identidad/CambiarPassword.tsx` | 3 — `password-actual`, `password-nueva`, `password-confirmacion` |
| `frontend/src/pages/identidad/AltaDocente.tsx` | 2 — `alta-docente-password`, `alta-docente-confirmar-password` |
| `frontend/src/pages/cuentas/ResetearPassword.tsx` | 2 — `password-nueva`, `password-confirmacion` |

### Alcance del fix

**Frontend puro** — sin cambios de backend.

1. Componente nuevo `frontend/src/components/PasswordInput.tsx`: envuelve `Input` (de
   `@/components/ui/input`) agregando un botón de toggle posicionado dentro del campo (ícono
   `Eye`/`EyeOff` de `lucide-react`, ya usado en el proyecto — `ChevronDown` en `select.tsx`).
   Props: las mismas que `Input` (`id`, `value`, `onChange`, `minLength`, etc., vía spread) más
   ningún prop propio obligatorio — el toggle es interno, sin estado que el padre necesite
   conocer.
2. Reemplazar los 10 `<Input type="password">` de la tabla de arriba por `<PasswordInput>` en
   sus 5 archivos, sin cambiar ningún otro comportamiento de esos formularios (validación,
   `minLength`, handlers `onChange` existentes se mantienen).

**Fuera de alcance de esta US:**
- Indicador de fortaleza — es `US-ADJ-36`, que reutiliza `PasswordInput` como base pero agrega
  ese elemento por separado (prop opcional, a definir en esa spec).
- Cualquier cambio de validación — esta US es puramente de visibilidad del texto tipeado.

---

## Especificacion del comportamiento

### Precondicion

- Ningún input de contraseña del sistema tiene toggle de visibilidad.
- Cada pantalla define su propio `<Input type="password">` sin componente compartido.

### Postcondicion

- Los 10 inputs de contraseña usan `PasswordInput`, con un botón que alterna entre ocultar y
  mostrar el texto tipeado, sin perder el valor ni recargar el formulario.
- El resto del comportamiento de cada formulario (validación, envío, mensajes de error) queda
  exactamente igual a antes de esta US.

### Invariantes

Ninguna — frontend puro, sin dominio.

---

## Criterios de aceptacion

```gherkin
Feature: Toggle mostrar/ocultar contraseña (US-ADJ-35)

  Scenario: Mostrar la contraseña tipeada
    Given un usuario escribió su contraseña en cualquier campo de password
    When hace clic en el botón de mostrar
    Then el campo muestra el texto en claro, sin perder el valor
    And el ícono del botón cambia para indicar que ahora oculta

  Scenario: Volver a ocultar
    Given un campo de contraseña está mostrando el texto en claro
    When hace clic en el botón de ocultar
    Then el campo vuelve a enmascarar el texto

  Scenario: El toggle no afecta la validación existente
    Given el campo "Contraseña nueva" de Registro tiene minLength=8 (o el valor vigente)
    When el usuario alterna mostrar/ocultar varias veces
    Then la validación de longitud mínima sigue funcionando igual que antes de esta US
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] Sí
- [x] No — componente de presentación puro, mismo patrón que `Select`/`Input` ya existentes en
  `components/ui/`.

**Capa(s) afectadas:**
- [x] Frontend — `components/PasswordInput.tsx` (nuevo), 5 pantallas modificadas (solo el
  import y el tag del input, sin tocar lógica)

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/components/PasswordInput.tsx` (nuevo) | Envuelve `Input` + botón toggle (`Eye`/`EyeOff` de `lucide-react`) |
| `frontend/src/pages/identidad/Login.tsx` | 1 input reemplazado |
| `frontend/src/pages/identidad/Registro.tsx` | 2 inputs reemplazados |
| `frontend/src/pages/identidad/CambiarPassword.tsx` | 3 inputs reemplazados |
| `frontend/src/pages/identidad/AltaDocente.tsx` | 2 inputs reemplazados |
| `frontend/src/pages/cuentas/ResetearPassword.tsx` | 2 inputs reemplazados |

---

## Referencias

- Incremento: 5-ADJ
- `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 1
- `docs/design/ux/wireframes-identidad-autoservicio.md` §2
- Issue: [#329](https://github.com/vvalotto/cognion/issues/329)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
