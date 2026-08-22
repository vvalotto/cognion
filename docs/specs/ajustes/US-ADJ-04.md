# US-ADJ-04: Alinear visualmente las pantallas de Cuentas/Contraseñas con el prototipo aprobado

**Estado**: `Especificada`
**Iteracion / Sprint**: `SP-ADJ-01` (misma iteración de ajuste que `US-ADJ-01`)
**Tipo**: `refactor frontend`
**Agregado principal afectado**: — (sin cambios de dominio, solo presentación)
**Bounded Context**: Identidad (frontend)

---

## Descripcion (lenguaje de negocio)

Como **Administrador y como cualquier Usuario autenticado**,
quiero **que las pantallas de gestión de cuentas y cambio de contraseña se vean como el
prototipo que Víctor ya aprobó** (breadcrumb, cards con sombra, tags de color por rol/estado,
pantallas de confirmación con ícono de éxito)
para **tener la misma calidad visual e institucional que ya tienen las pantallas de login/
registro y las del Banco de Preguntas (`US-ADJ-01`)**.

---

## Contexto del dominio

### Problema

Detectado en revisión manual post-`US-ADJ-01` (2026-08-22): las pantallas de la Iteración 2
de cuentas (`US-2.2.6` a `US-2.2.9`, agosto 2026) no reproducen el lenguaje visual de
`docs/design/ux/prototipos/identidad-cuentas-administracion.html` — mismo prototipo, misma
paleta y radii que `banco-preguntas-carga-filtrado.html` (`wireframes-cuentas-administracion.md`
§1: "Misma paleta y tipografía... continuidad visual entre BCs e iteraciones").

Causa raíz: mismo patrón que `HITO-4` (origen de `US-ADJ-01`) — las primitivas `Card`/
`Badge`/`Breadcrumb` no existían todavía cuando se implementaron `US-2.2.6` a `US-2.2.9`
(anteriores a `US-ADJ-01`, que las creó). `Cuentas.tsx`, `CuentaDetalle.tsx`,
`ResetearPassword.tsx`, `CuentaReseteada.tsx` y `CambiarPassword.tsx` cumplen los criterios
de aceptación funcionales de sus US y pasan su suite de tests, pero usan markup plano en vez
de las primitivas ya disponibles.

`Login.tsx`/`LoginCuentaBloqueadaError.tsx` quedan **fuera de alcance**: siguen su propio
prototipo ya aprobado (`identidad-registro-login.html`, Incremento 1) y ya están alineadas.

### Modelo involucrado

Sin cambios de dominio — US puramente de presentación (frontend). No hay Aggregate, Value
Object, Domain Event, Port ni Command afectados. Reutiliza las primitivas ya creadas por
`US-ADJ-01` (`Card`, `CardContent`, `Badge`, `Breadcrumb`, variante `destructive-solid` de
`Button`) — no agrega componentes nuevos a `components/ui/`.

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Reutilizado | `Card`/`CardContent` (`US-ADJ-01`) | Formularios, tabla de cuentas, pantallas de confirmación |
| Reutilizado | `Badge` (`US-ADJ-01`) | Tags de color por Rol (docente/estudiante/administrador) y Estado (activa/bloqueada) — variantes nuevas sobre el mismo componente |
| Reutilizado | `Breadcrumb` (`US-ADJ-01`) | Ruta de navegación en cabecera de cada pantalla |
| Reutilizado | `Button variant="destructive-solid"` (`US-ADJ-01`) | Botón "Resetear contraseña" en `ResetearPassword.tsx` |

`Badge` gana variantes nuevas (`rol-docente`, `rol-estudiante`, `rol-admin`, `estado-activa`,
`estado-bloqueada`) — mismo patrón `cva` ya usado por `tipo-om`/`nivel-alto`, sin romper las
variantes existentes de Banco de Preguntas.

---

## Especificacion del comportamiento

### Precondicion

- `US-2.2.6` a `US-2.2.9` implementadas y mergeadas (esta US no agrega comportamiento nuevo,
  solo re-viste pantallas existentes).
- `US-ADJ-01` mergeada — las primitivas `Card`/`Badge`/`Breadcrumb`/`destructive-solid` ya
  existen en `frontend/src/components/`.
- Prototipo `docs/design/ux/prototipos/identidad-cuentas-administracion.html` sigue siendo la
  fuente de verdad UX — sin cambios de diseño respecto a lo ya aprobado.

### Postcondicion

- Cada pantalla listada en "Artefactos a modificar" reproduce, verificado visualmente
  (navegador real contra el prototipo, mismo criterio que `US-ADJ-01`):
  - Breadcrumb con la ruta correspondiente ("Administración › Cuentas [› ...]" o
    "Mi cuenta › Cambiar contraseña").
  - Tarjetas con sombra (`Card`) para filtros, tabla, bloque de datos y formularios.
  - Tags de color por Rol (azul docente / violeta estudiante / naranja administrador) y por
    Estado (verde activa / rojo bloqueada) en `Cuentas.tsx` y `CuentaDetalle.tsx`.
  - Columna/botón "Ver" en la fila de la tabla de `Cuentas.tsx` (hoy la fila entera es
    clickeable pero no hay acción visible, a diferencia del prototipo).
  - Pantallas de confirmación (`CuentaReseteada.tsx`, éxito de `CambiarPassword.tsx`) como
    `result-card` centrada con ícono de éxito (✓), no texto suelto.
  - Botón "Resetear contraseña" en `ResetearPassword.tsx` con `destructive-solid` (sólido),
    no la variante `destructive` (soft) actual.
- Ningún criterio de aceptación funcional de `US-2.2.2` a `US-2.2.9` cambia — mismos
  endpoints, mismas validaciones, mismas rutas. Es un refactor de presentación puro.
- Suite de tests existente (Vitest + RTL) sigue en verde; se ajustan los tests que dependían
  de estructura DOM que cambia.

### Invariantes

| ID | Invariante |
|----|------------|
| — | Sin invariantes de dominio — US de presentación pura. |

---

## Criterios de aceptacion

```gherkin
Feature: Alineación visual de Cuentas/Contraseñas con el prototipo aprobado (US-ADJ-04)

  Scenario: Listado de cuentas con tags de color y acción Ver
    Given un Administrador autenticado en "Cuentas"
    When la tabla de cuentas carga
    Then el Rol de cada cuenta se muestra con un tag de color
    And el Estado se muestra con un tag de color (verde activa, rojo bloqueada)
    And cada fila tiene un botón "Ver"

  Scenario: Detalle de cuenta con tarjeta de datos
    Given un Administrador autenticado viendo el detalle de una cuenta bloqueada
    When la pantalla carga
    Then el breadcrumb muestra "Administración › Cuentas › {nombre}"
    And los datos de la cuenta se muestran dentro de una tarjeta con sombra
    And el Rol y el Estado se muestran con tags de color

  Scenario: Confirmación de reseteo como pantalla de éxito
    Given un Administrador que acaba de resetear la contraseña de una cuenta
    When llega a la pantalla de confirmación
    Then ve un ícono de éxito (✓) y el mensaje dentro de una tarjeta centrada

  Scenario: Sin regresión funcional
    Given la suite de tests existente de Cuentas/Contraseñas
    When se ejecuta después de este ajuste
    Then todos los tests siguen pasando sin cambios en los criterios de aceptación de US-2.2.2 a US-2.2.9
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] Sí — agrega variantes nuevas a `Badge` (`rol-*`/`estado-*`), pero sigue el patrón ya
  establecido por `US-ADJ-01` — no amerita un ADR nuevo, es la aplicación consistente de una
  decisión ya tomada.
- [x] No — sin cambios de capas `entities`/`use_cases`/`interface_adapters`/`frameworks` del
  backend ni de contratos de API.

**Capa(s) afectadas:**
- [x] Frontend — `components/ui/badge.tsx` (variantes nuevas) + las 5 pantallas de Cuentas/
  Contraseñas
- [ ] Backend — sin cambios

---

## Fuente de verdad UX

`docs/design/ux/prototipos/identidad-cuentas-administracion.html` (ya aprobado, sin cambios
de diseño en esta US) y `docs/design/ux/wireframes-cuentas-administracion.md`. Verificación
de cierre: comparación visual en navegador real contra el prototipo, mismo criterio que
`US-ADJ-01`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/components/ui/badge.tsx` | Variantes nuevas `rol-docente`/`rol-estudiante`/`rol-admin`/`estado-activa`/`estado-bloqueada` |
| `frontend/src/pages/Cuentas.tsx` | Breadcrumb, filtros en `Card`, tabla en `Card`, tags de color, columna/botón "Ver" |
| `frontend/src/pages/CuentaDetalle.tsx` | Breadcrumb como componente, bloque de datos en `Card`, tags de color |
| `frontend/src/pages/ResetearPassword.tsx` | Breadcrumb como componente, formulario en `Card`, botón `destructive-solid` |
| `frontend/src/pages/CuentaReseteada.tsx` | `result-card` centrada con ícono de éxito |
| `frontend/src/pages/CambiarPassword.tsx` | Breadcrumb, formulario en `Card`, pantalla de éxito como `result-card` con ícono |

---

## Referencias

- Relacionada con: `US-2.2.2`/`US-2.2.3`/`US-2.2.4`/`US-2.2.5` (backend, sin cambios),
  `US-2.2.6` a `US-2.2.9` (US que esta US re-viste, sin tocar su comportamiento), `US-ADJ-01`
  (mismo criterio y primitivas, aplicado antes a Banco de Preguntas)
- Candidatas: `SP-ADJ-01`, segunda US de la iteración de ajuste conjunta (después de
  `US-ADJ-01`, antes o junto con `US-ADJ-03`)

---

*Basado en el template de `docs/specs/ajustes/US-ADJ-01.md`. US de ajuste (`SP-ADJ-01`,
`docs/plans/PLAN-CM.md` §12).*
