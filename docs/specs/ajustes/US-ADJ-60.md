# US-ADJ-60: El sistema siempre conserva al menos un Administrador operativo

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 7-ADJ — Ciclo de vida de la cuenta y ajustes de la UAT v1`
(decisión de Víctor, 2026-10-02; reglas confirmadas en el plan de corrección §7)
**Tipo**: `feat` backend + migración + frontend
**Agregado principal afectado**: `Usuario` (perfil `Administrador`)
**Bounded Context**: Identidad
**Origen**: UAT manual de cierre de alcance v1, hallazgo **#4** 🔴
(`quality/reports/uat/inc7/registro-hallazgos.md`, `plan-de-correccion.md` §3).
**Depende de**: `US-ADJ-59` (la noción de "operativo" solo tiene sentido si `deshabilitada` se
hace cumplir).

---

## Fuente de verdad UX

Solo la **Parte B (frontend)** la necesita, y **hoy no existe el artefacto aprobado**. Hay que
ampliar `docs/design/ux/wireframes-cuentas-administracion.md` (y el prototipo
`identidad-cuentas-administracion.html`) con: (1) el texto de confirmación de "Eliminar cuenta"
para un Administrador, (2) el mensaje cuando se intenta dar de baja al último Administrador
operativo, y (3) el estado de login `#login-bloqueada-temporal`. Sin esa aprobación de Víctor no
se toca `frontend/` (gate UX, `CLAUDE.md`). La **Parte A (backend)** no depende de esto.

---

## Descripcion (lenguaje de negocio)

Como **dueño del sistema**,
quiero que **nunca pueda quedar sin ningún Administrador que pueda operarlo**,
para **no depender de una intervención manual en la base de datos para recuperar el control**.

Como **único Administrador**,
quiero que **equivocarme con la contraseña no me deje fuera para siempre**,
para **poder volver a intentar pasado un rato sin que nadie tenga que desbloquearme**.

---

## Contexto del dominio

### Problema (verificado en el código)

El sistema puede quedar sin Administrador operativo por tres vías, ninguna protegida:

1. **Borrado físico.** `EliminarCuentaUseCase` (`eliminar_cuenta.py:57-58`) trata al
   Administrador como a cualquier cuenta: si no creó Comisiones lo **borra de la base**.
2. **Baja del último.** Nada impide deshabilitar al único Administrador activo.
3. **Bloqueo automático.** Hay **dos** caminos que bloquean a los 3 fallos consecutivos, y
   ambos aplican a un Administrador sin excepción: el login (`IniciarSesionUseCase`,
   `iniciar_sesion.py:49-53`) y el cambio de la propia contraseña
   (`Usuario.registrar_fallo_cambio_password()`, usado por `CambiarPasswordUseCase`). El hallazgo
   original solo mencionaba el login; esta spec cubre los dos.

`ADR-016` ya trata al Administrador como caso especial para el **alta** (bootstrap fuera del
producto), pero no para la baja ni el bloqueo.

### Definiciones

- **Administrador operativo:** `Usuario` con perfil `Administrador`, `deshabilitada = false` y
  `bloqueada = false` (incluye el bloqueo temporal de la regla 3: mientras dura, esa cuenta no
  cuenta como operativa).
- **Último Administrador operativo:** el que sería el único operativo si se lo excluye a él del
  conteo, es decir, no existe **otro** Administrador operativo.

### Alcance del fix

**Parte A — Backend, BC Identidad:**

**Regla 1 — un Administrador nunca se borra físicamente.**
`EliminarCuentaUseCase`, para perfil `Administrador`, siempre hace baja lógica
(`usuario.deshabilitar()` + `actualizar`), tenga o no Comisiones creadas. Devuelve el `Usuario`
deshabilitado (el endpoint ya responde `200` con el detalle cuando hay baja lógica, y `204` solo
con borrado físico). `tiene_comisiones_creadas` deja de usarse para este caso; si queda sin
usos, retirarlo del puerto.

**Regla 2 — no se da de baja al último Administrador operativo.**
Antes de deshabilitar, si el `Usuario` es un Administrador operativo y no existe otro operativo,
lanza `UltimoAdministradorOperativoError` (nueva, `entities/errors.py`). El endpoint
`DELETE /usuarios/{id}` la mapea a **409 Conflict** con `detail` estructurado
`{"codigo": "ultimo_administrador_operativo", "mensaje": "..."}`. Dar de baja a un Administrador
que ya está deshabilitado o bloqueado es idempotente y no dispara la regla (no cuenta como
operativo).
Para contar, se agrega al `UsuarioRepositoryPort`:
`contar_administradores_operativos(excluyendo: UUID | None = None) -> int` (un `SELECT count`
sobre `administrador ⨝ usuario`). Se pone en el repositorio de usuarios, **no** en
`CuentaQueryPort`, para que los use cases de login y de cambio de contraseña no sumen una
dependencia nueva (riesgo de CBO, lección repetida de los Incrementos 2 a 4).

**Regla 3 — el bloqueo automático del último Administrador operativo es temporal.**
En los dos caminos de bloqueo automático, al 3.er fallo consecutivo:
- si el `Usuario` es un Administrador operativo y **no existe otro** operativo → no se bloquea
  de forma permanente: queda `bloqueada = true` con `bloqueada_hasta = ahora + duración`
  (nuevo campo, `timestamptz` nullable);
- en cualquier otro caso (Docente, Estudiante, o Administrador habiendo otro operativo) →
  bloqueo permanente, como hoy (`bloqueada_hasta = NULL`).
La **duración** es configurable (`settings.py`: `administrador_bloqueo_temporal_minutos`,
default **15**) y se inyecta a los use cases desde el composition root
(`frameworks/dependencies.py`), mismo patrón que la cadencia del `VerificadorDeVencimientos`: ni
las entidades ni los use cases importan `settings`.
La política vive en un único método de la entidad (p. ej.
`Usuario.bloquear_por_intentos_fallidos(es_ultimo_administrador, ahora, duracion)`) que usan los
dos use cases; el use case solo resuelve `es_ultimo_administrador` con el repositorio.
**Vencimiento perezoso, sin proceso de fondo:** al iniciar sesión o cambiar la contraseña, si la
cuenta está `bloqueada` con `bloqueada_hasta` no nulo y `ahora ≥ bloqueada_hasta`, se levanta el
bloqueo (`bloqueada = false`, contadores a 0, `bloqueada_hasta = NULL`) y el flujo continúa.
Mientras no venció, lanza `CuentaBloqueadaTemporalmenteError(usuario_id, bloqueada_hasta)` →
**403** con `detail` estructurado
`{"codigo": "cuenta_bloqueada_temporal", "mensaje": "...", "reintentar_en_segundos": N}`.
Un reseteo de contraseña por otro Administrador (`resetear_password`) también limpia
`bloqueada_hasta`. El `403` de bloqueo permanente conserva su `detail` en texto plano.

**Migración Alembic (`migrations/versions/`):** `usuario.bloqueada_hasta timestamptz NULL`. Round-trip real
(`upgrade`/`downgrade`) verificado, como en `US-2.1.2`.

**Parte B — Frontend (bloqueada por el gate UX):**
- `EliminarCuenta.tsx`: para una cuenta de Administrador, el aviso dice que **se deshabilita y se
  puede reactivar** (hoy diría "se borra en forma permanente", incorrecto para este rol), y que
  no se puede dar de baja al único Administrador operativo. Hoy `handleEliminar` no captura
  errores: hay que manejar el `409` y mostrar el mensaje en la pantalla.
- `Login.tsx`: `detail.codigo === "cuenta_bloqueada_temporal"` → alerta propia ("Cuenta
  bloqueada temporalmente — volvé a intentar en N minutos"), distinta de la de bloqueada
  permanente (que manda a "Contactá a un Administrador", inútil para el último).

**Fuera de alcance:**
- Mostrar `bloqueada_hasta` en el detalle de Cuenta del Administrador (se puede sumar después).
- Bloqueo con retardo creciente u otros esquemas de fuerza bruta.
- Cambiar el comportamiento de Docente/Estudiante.
- **Condición de carrera:** dos Administradores que se dan de baja mutuamente *a la vez* podrían
  pasar ambos la regla 2 y dejar cero operativos. A esta escala (un Administrador) se acepta y
  se documenta; si hiciera falta, se resuelve con `SELECT … FOR UPDATE` sobre los perfiles
  `Administrador` dentro de la transacción del use case.

### Decisiones tomadas (plan de corrección §7)

- Decisión 3: bloqueo **temporal** para el último Administrador operativo (opción A), el resto
  bloquea como hoy. El valor de 15 min es la propuesta de esta spec y se puede ajustar sin
  tocar el diseño.
- Interacción con `US-ADJ-62`: recuperar la contraseña también limpia el bloqueo temporal
  (`bloqueada_hasta = NULL`) y libera al último Administrador.

---

## Especificacion del comportamiento

### Precondicion

- Un Administrador sin Comisiones creadas se borra físicamente; nada protege al último; el
  bloqueo a los 3 fallos es permanente para todos.

### Postcondicion

- Un Administrador **nunca** desaparece de la tabla `usuario`: la baja siempre es lógica.
- No se puede deshabilitar al último Administrador operativo (`409`, sin cambios).
- El último Administrador operativo que falla 3 veces queda bloqueado solo por un tiempo y se
  libera solo; cualquier otra cuenta conserva el bloqueo permanente.
- Siempre existe al menos un Administrador capaz de iniciar sesión (ya sea ahora o al vencer el
  bloqueo temporal).

### Invariantes

- **INV-ID-19 (nueva):** un `Usuario` con perfil `Administrador` nunca se elimina físicamente.
- **INV-ID-20 (nueva):** debe existir siempre al menos un Administrador operativo; no se puede
  deshabilitar al último.
- **INV-ID-21 (nueva, enmienda a INV-ID-10):** el bloqueo automático por intentos fallidos del
  último Administrador operativo es temporal y vence solo; el de cualquier otra cuenta es
  permanente hasta que un Administrador (o la recuperación, `US-ADJ-62`) la desbloquee.

---

## Criterios de aceptacion

```gherkin
Feature: Siempre existe al menos un Administrador operativo (US-ADJ-60)

  Scenario: Dar de baja a un Administrador sin Comisiones es siempre baja lógica
    Given dos Administradores operativos A y B, y A no creó ninguna Comisión
    When un Administrador da de baja a A
    Then la respuesta es 200 con el detalle de A
    And A sigue existiendo en la tabla usuario con deshabilitada = true

  Scenario: No se puede dar de baja al último Administrador operativo
    Given un único Administrador operativo A
    When se hace DELETE /usuarios/{A}
    Then la respuesta es 409 con codigo "ultimo_administrador_operativo"
    And A sigue con deshabilitada = false

  Scenario: Un Administrador bloqueado no cuenta como operativo
    Given un Administrador A operativo y un Administrador B con bloqueada = true
    When se hace DELETE /usuarios/{A}
    Then la respuesta es 409 con codigo "ultimo_administrador_operativo"

  Scenario: Dar de baja a un Administrador ya deshabilitado es idempotente
    Given un Administrador A deshabilitado y un Administrador B operativo
    When se hace DELETE /usuarios/{A}
    Then la respuesta es 200
    And B sigue operativo

  Scenario: Tres logins fallidos del último Administrador lo bloquean solo por un tiempo
    Given un único Administrador operativo A
    When se hacen 3 POST /identidad/login con una contraseña incorrecta
    Then A queda con bloqueada = true y bloqueada_hasta = ahora + 15 minutos
    And el siguiente login responde 403 con codigo "cuenta_bloqueada_temporal"
    And el detail trae reintentar_en_segundos mayor que 0

  Scenario: El bloqueo temporal se levanta solo al vencer
    Given A bloqueado temporalmente con bloqueada_hasta ya vencida
    When A hace login con su contraseña correcta
    Then la respuesta es 200 con un JWT válido
    And A queda con bloqueada = false y bloqueada_hasta = NULL

  Scenario: Habiendo otro Administrador operativo el bloqueo sigue siendo permanente
    Given dos Administradores operativos A y B
    When A falla 3 veces el login
    Then A queda con bloqueada = true y bloqueada_hasta = NULL
    And el detail del 403 es el texto plano de cuenta bloqueada

  Scenario: Tres fallos al cambiar la propia contraseña también son temporales para el último
    Given un único Administrador operativo A autenticado
    When A envía 3 veces PUT /usuarios/me/password con una contraseña actual incorrecta
    Then A queda con bloqueada = true y bloqueada_hasta = ahora + 15 minutos

  Scenario: Docente y Estudiante conservan el bloqueo permanente
    Given un Docente operativo
    When falla 3 veces el login
    Then queda con bloqueada = true y bloqueada_hasta = NULL

  Scenario: Un reseteo de contraseña limpia el bloqueo temporal
    Given A bloqueado temporalmente
    When otro Administrador resetea su contraseña
    Then A queda con bloqueada = false y bloqueada_hasta = NULL

  Scenario: La confirmación de baja de un Administrador no promete un borrado (frontend, tras el gate UX)
    Given estoy en la pantalla "Eliminar cuenta" de un Administrador
    Then el aviso dice que la cuenta se deshabilita y se puede reactivar
    And no dice que se borra en forma permanente
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] Sí
- [x] No — se resuelve con una invariante de dominio nueva (`INV-ID-19/20/21`), un puerto con un
  método más y una columna. Si la implementación decide otro mecanismo para el bloqueo temporal
  que un campo `bloqueada_hasta`, registrarlo en un ADR corto.

**Capa(s) afectadas:**
- [x] Entities — `Usuario` (política de bloqueo, `bloqueada_hasta`, vencimiento), errores nuevos
- [x] Use Cases — `EliminarCuentaUseCase`, `IniciarSesionUseCase`, `CambiarPasswordUseCase`
- [x] Interface Adapters — `UsuarioRepositoryPort`/gateway (`contar_administradores_operativos`),
  routers (`409` y `403` estructurados)
- [x] Frameworks — modelo ORM + migración Alembic, `settings.py`, `dependencies.py`
- [x] Frontend — `EliminarCuenta.tsx`, `Login.tsx` (Parte B, tras el gate UX)

**Riesgo de CBO:** `IniciarSesionUseCase` y `CambiarPasswordUseCase` no suman clases
colaboradoras (el conteo va por el repositorio que ya reciben); `EliminarCuentaUseCase` ya recibe
4 colaboradores — revisar el CBO antes de pushear (el pre-push gate lo detectó recién en la fase
de PR en `US-2.1.2`/`2.1.5`/`2.1.6`/`2.2.2`).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/entities/usuario.py` | `bloqueada_hasta`; método de política de bloqueo; vencimiento del bloqueo temporal; `resetear_password` limpia `bloqueada_hasta` |
| `src/identidad/entities/errors.py` | `UltimoAdministradorOperativoError`, `CuentaBloqueadaTemporalmenteError` |
| `src/identidad/entities/ports/usuario_repository_port.py` | `contar_administradores_operativos(excluyendo)` |
| `src/identidad/use_cases/eliminar_cuenta.py` | Regla 1 y regla 2 |
| `src/identidad/use_cases/iniciar_sesion.py`, `cambiar_password.py` | Regla 3 (política + vencimiento perezoso) |
| `src/identidad/interface_adapters/gateways/usuario_repository.py` | Implementación del conteo y persistencia de `bloqueada_hasta` |
| `src/identidad/frameworks/db/models.py` + `migrations/versions/` | Columna `usuario.bloqueada_hasta` (round-trip verificado) |
| `src/settings.py`, `src/identidad/frameworks/dependencies.py` | `administrador_bloqueo_temporal_minutos` y su inyección |
| `src/identidad/frameworks/api/cuentas_router.py`, `auth_router.py`, `perfil_router.py` | `409` y `403` estructurados |
| tests unit/integration/BDD (patrón de `inc5-adj`/`inc6-adj`: `tests/integration/inc7-adj/`, `tests/features/inc7-adj/US-ADJ-60-*.feature`) | Tests de los escenarios |
| `frontend/src/pages/cuentas/EliminarCuenta.tsx`, `pages/identidad/Login.tsx` (+ tests) | Parte B |
| `docs/design/domain/BC-identidad-modelo.md` | `INV-ID-19/20/21`, `bloqueada_hasta` en §4, enmienda a `INV-ID-10` |
| `docs/design/ux/wireframes-cuentas-administracion.md` + prototipo | Los tres estados nuevos (gate UX) |

---

## Referencias

- Incremento: 7-ADJ — `docs/plans/inc7-adj/inc7-adj-candidatas.md`
- `quality/reports/uat/inc7/plan-de-correccion.md` §3 (`US-ADJ-60`), §7 decisión 3
- `quality/reports/uat/inc7/registro-hallazgos.md` hallazgo #4
- `docs/adr/ADR-016` (bootstrap del primer Administrador), `ADR-013`
- Issue: [#475](https://github.com/vvalotto/cognion/issues/475)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
