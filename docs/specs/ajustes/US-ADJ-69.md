# US-ADJ-69: El login avisa "te queda 1 intento" tras el 2.º fallo

**Estado**: `Implementada`
**Iteracion / Sprint**: `Incremento 9 — Correcciones y robustez`, Iteración 2
**Tipo**: `ajuste de producto` backend + frontend (reescribe parte del contrato de `US-2.2.1` y `US-ADJ-60`)
**Agregado principal afectado**: `Usuario` (contador `intentos_fallidos_login`, sin cambios de reglas)
**Bounded Context**: Identidad
**Origen**: observación O-1 de la UAT de cierre del 7-ADJ (2026-10-05); decisión de Víctor del 2026-11-08 en #593 (opción 3: advertir antes).
**Issue**: [#604](https://github.com/vvalotto/cognion/issues/604) · cierra [#502](https://github.com/vvalotto/cognion/issues/502) al mergear.
**Interactúa con**: `US-2.2.1` (bloqueo al 3.er intento, `INV-ID-10`), `US-ADJ-60` (último Administrador, bloqueo temporal), `US-2.2.8` (patrón `intentos_restantes` en el cambio de contraseña), `US-ADJ-62` (recuperar por email desbloquea).

---

## Fuente de verdad UX

- `docs/design/ux/wireframes-identidad.md` §2.2b (aviso del 2.º fallo, trade-off aceptado) y §2.2 (enmienda).
- `docs/design/ux/prototipos/identidad-registro-login.html`, pantalla `#login-aviso`.
- Aprobados por Víctor el 2026-11-08.

---

## Descripcion (lenguaje de negocio)

Como **persona que usa una contraseña equivocada al entrar**,
quiero **que el segundo error me avise de que me queda un solo intento**,
para **no bloquear mi cuenta sin darme cuenta y poder recuperar la contraseña a tiempo**.

---

## Contexto

El 3.er intento fallido de login bloquea la cuenta (`INV-ID-10`), pero responde igual que los dos anteriores: `401` y "Email o contraseña incorrectos". La alerta de bloqueo recién aparece en el 4.º intento (`403`). Quien se equivoca no se entera de que su 3.er intento lo bloqueó.

El cambio de contraseña ya resuelve esto con `detail.intentos_restantes` (`US-2.2.8`); el login no.

## Especificacion del comportamiento

- Tras el **2.º fallo consecutivo** de una cuenta existente, la respuesta `401` del login informa `intentos_restantes = 1`.
- **Solo** en el 2.º fallo: el 1.er fallo y el 3.º (el que bloquea) responden como hoy. No se informa "te quedan 2": se revela lo mínimo.
- Forma de la respuesta, igual que el cambio de contraseña: cuando hay aviso, `detail` es un objeto `{"mensaje": "Email o contraseña inválidos.", "intentos_restantes": 1}`; sin aviso, `detail` sigue siendo el texto de hoy.
- Un email inexistente **nunca** recibe el aviso: responde siempre igual que hoy.
- Un login exitoso reinicia el contador (comportamiento actual): fallo, éxito, fallo no avisa.
- Aplica igual al último Administrador (bloqueo temporal): el 2.º fallo avisa.
- Cuenta ya bloqueada (`403`) o deshabilitada: sin cambios.
- **Pantalla:** la alerta de error del login agrega "Te queda 1 intento antes del bloqueo de la cuenta." y un link a `/recuperar-password` ("recuperala por email").

## Trade-off de seguridad (aceptado por Víctor el 2026-11-08)

Hasta ahora un email inexistente y una contraseña incorrecta respondían igual, así que no se podía saber si una cuenta existe. El aviso aparece solo en cuentas que existen, por lo que permite distinguirlas. El bloqueo del 4.º intento ya filtraba la existencia de la cuenta. A esta escala (uso interno, 30 a 60 alumnos por comisión) se acepta. Simular el aviso para emails inexistentes queda fuera de alcance. Hay que anotarlo en `BC-identidad-modelo.md` (`INV-ID-10`) y en el docstring de `CredencialesInvalidas`, que hoy dice que no filtra la existencia.

## Escenarios (BDD)

1. **Primer fallo.** Cuenta existente, 1.er intento con contraseña incorrecta → `401` sin `intentos_restantes`.
2. **Segundo fallo avisa.** Tras el 2.º fallo → `401` con `intentos_restantes = 1`.
3. **Tercer fallo bloquea.** El 3.er fallo bloquea la cuenta → `401` sin `intentos_restantes`; el 4.º intento responde `403` como hoy (contrato de `US-2.2.1` y `US-ADJ-60` intacto).
4. **Email inexistente.** Dos o más intentos con un email que no existe → siempre la respuesta genérica, sin `intentos_restantes`.
5. **El éxito reinicia.** Fallo, login correcto, fallo → el segundo fallo de la tanda no avisa.
6. **Último Administrador.** El 2.º fallo avisa; el 3.º aplica el bloqueo temporal de siempre.
7. **Pantalla.** Con `intentos_restantes = 1` el login muestra el aviso y el link para recuperar la contraseña; sin él, solo el mensaje genérico.

## Fuera de alcance

Contador en el 1.er fallo o "te quedan 2 intentos"; el cambio de contraseña (tiene su propio contador y ya avisa); simular el aviso para emails inexistentes; cambiar el número máximo de intentos (3).

## Notas para `/implement-us`

- **Por dónde entra el dato:** `IniciarSesionUseCase` ya incrementa `usuario.intentos_fallidos_login` y arma `CredencialesInvalidas`; ahí se fija `intentos_restantes = 1` cuando el contador llega a `_INTENTOS_MAXIMOS - 1`. La excepción gana el atributo (por defecto `None`), como `PasswordActualIncorrecta`.
- **Router:** `auth_router.py` arma `detail` como objeto solo cuando hay aviso, para no romper clientes ni tests que leen el texto.
- **Frontend:** `apiFetch` ya extrae `message` y `detail` cuando `detail` es un objeto con `mensaje` (`extractError`). `Login.tsx` hoy descarta el motivo del `ApiError`; debe leer `detail.intentos_restantes` y pasárselo a `LoginError`.
- **Documentación a enmendar:** specs de `US-2.2.1` y `US-ADJ-60` (nota de que el contrato cambia en el 2.º fallo), `BC-identidad-modelo.md` (`INV-ID-10`) y el docstring de `CredencialesInvalidas`.
- Mantener la sincronía de los `Fake*` de `tests/unit/` si se toca algún puerto (aquí no se espera).
- Verificación al cierre de la iteración, en navegador real: tres fallos seguidos y el aviso en el segundo.
