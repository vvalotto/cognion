# BC Identidad — Wireframes: Gestión de Cuentas por Administrador

> Estado documental: **vigente — aprobado por Víctor (2026-08-19, sesión de modelado de la
> Iteración 2 del Incremento 2).**
> Usado como input de las specs US-IEDD de la Iteración 2 (`docs/specs/inc2/US-2.2.1` a
> `US-2.2.9`).
>
> Fuente: `docs/rf/RF_v1.md` (RF-03, RF-19), `docs/design/domain/BC-identidad-modelo.md`
> (§3 "Diferidos", §9, §11 — comandos `CambiarPassword`, `ResetearPassword`, invariantes
> INV-ID-10/INV-ID-11), `docs/design/ux/wireframes-identidad.md` §4 (fuera de alcance:
> "Cambio de contraseña (RF-19) y reseteo/desbloqueo por Administrador (RF-03) — Incremento
> 2", "Listado y gestión de cuentas existentes — RF-03, Incremento 2").
>
> Prototipo: `docs/design/ux/prototipos/identidad-cuentas-administracion.html` — navegable,
> 7 pantallas.

---

## 1. Identidad visual

Misma paleta y tipografía que `wireframes-identidad.md` §1 y `wireframes-banco-preguntas.md`
§1 (azul institucional `#1D75B5`, verde de acento `#53AA74`, Roboto) — continuidad visual
entre BCs e iteraciones, sin redefinir tokens nuevos.

---

## 2. Pantallas

### 2.1 Listado de cuentas (`#cuentas`)

**Actor:** Administrador.
**Query:** `ListarCuentas(rol?, estado?, busqueda?)`.

| Elemento | Detalle |
|---|---|
| Contexto | Header de aplicación autenticada, breadcrumb "Administración › Cuentas" |
| Filtros | Rol (Todos/Docente/Estudiante/Administrador), Estado (Todos/Activa/Bloqueada), búsqueda libre por nombre o email |
| Tabla | Nombre, Email, Rol (tag), Estado (tag), acción "Ver" |
| Acción "+ Nueva cuenta" | Referencia el flujo de alta directa ya implementado (`US-1.1.9`, alta de Docente) — esta pantalla no reemplaza ni duplica ese flujo, solo lo enlaza |
| Fuera de alcance | Alta de Administrador (ya excluida en `wireframes-identidad.md` §4) |

### 2.2 Detalle de cuenta (`#cuenta-detalle`)

**Actor:** Administrador.
**Query:** `ObtenerCuenta(usuario_id)`.

| Elemento | Detalle |
|---|---|
| Contexto | Breadcrumb "Administración › Cuentas › {nombre}" |
| Alerta | Si `bloqueada = true`, alerta destructiva explicando el motivo (3 intentos fallidos consecutivos) |
| Datos | Email, Rol, Estado, Comisión (si aplica, perfil Estudiante), fecha de creación |
| Acción única | "Resetear contraseña y desbloquear" — un solo botón, con aclaración de que es la única forma de desbloquear (INV-ID-10, sin comando de desbloqueo separado) |
| Fuera de alcance | Edición de nombre/email/comisión — RF-03 solo pide resolver bloqueos/recuperación, no un CRUD de perfil completo |

### 2.3 Resetear contraseña / desbloquear (`#cuenta-resetear`)

**Actor:** Administrador.
**Comando:** `ResetearPassword(usuario_id, password_nueva, administrador_id)`.

| Elemento | Detalle |
|---|---|
| Aviso | Alerta de advertencia: "Esta acción también desbloquea la cuenta" |
| Campos | Nueva contraseña temporal, Confirmar contraseña |
| Validación de cliente | Mínimo 8 caracteres (INV-ID-11), coincidencia entre ambos campos |
| Acciones | "Resetear contraseña" (destructiva por el impacto, no por ser peligrosa en sí) / "Cancelar" (vuelve al detalle) |

### 2.4 Confirmación de reseteo (`#cuenta-reseteada`)

**Evento:** `PasswordReseteada`, `CuentaDesbloqueada` (si estaba bloqueada).

| Elemento | Detalle |
|---|---|
| Confirmación | Nombre de la cuenta, mensaje de éxito (contraseña reseteada + cuenta desbloqueada) |
| Acción | "Volver al listado de cuentas" |

### 2.5 Cambiar mi contraseña (`#cambiar-password`)

**Actor:** cualquier Usuario autenticado (Administrador, Docente o Estudiante).
**Comando:** `CambiarPassword(usuario_id, password_actual, password_nueva)`.

| Elemento | Detalle |
|---|---|
| Contexto | Accesible desde cualquier rol autenticado — no es una pantalla de administración |
| Campos | Contraseña actual, Contraseña nueva, Confirmar contraseña nueva |
| Validación de cliente | Nueva ≥ 8 caracteres (INV-ID-11), coincidencia entre nueva y confirmación |
| Aclaración | "Tu sesión actual sigue activa" — cambiar la contraseña no invalida el JWT en curso (`ADR-013`) |

### 2.6 Cambiar mi contraseña — error (`#cambiar-password-error`)

**Evento:** rechazo por `PasswordActualIncorrecta`.

| Elemento | Detalle |
|---|---|
| Alerta | Destructiva: "Contraseña actual incorrecta", con la cantidad de intentos restantes antes del bloqueo automático (INV-ID-10) |
| Comportamiento | El formulario permanece con los campos vacíos, listo para reintentar |

### 2.7 Contraseña cambiada (`#cambiar-password-exito`)

**Evento:** `PasswordCambiada`.

| Elemento | Detalle |
|---|---|
| Confirmación | Mensaje de éxito, aclara que no fue necesario volver a iniciar sesión |
| Acción | "Continuar" — vuelve a la pantalla desde la que se navegó (banco, materias, cuentas, según el rol) |

### 2.8 Login — cuenta bloqueada (`#login-bloqueada`)

**Evento:** intento de `IniciarSesion` sobre una cuenta con `bloqueada = true` (INV-ID-10).

| Elemento | Detalle |
|---|---|
| Layout | Propio de esta pantalla — tarjeta centrada sin el bloque de marca (`Cognión`/subtítulo) del resto de `AuthLayout`, ícono de la app (40px) centrado sobre el título "Ingresar" — no reutiliza el encabezado de `wireframes-identidad.md` §2.2 |
| Alerta | Destructiva, con ícono 🔒: "Cuenta bloqueada" — "Superaste el máximo de intentos permitidos. Podés **recuperar tu contraseña por email** o pedirle a un Administrador que la restablezca." — "recuperar tu contraseña por email" es un link a `/recuperar-password` (`wireframes-identidad-autoservicio.md` §4); recuperarla desbloquea la cuenta (`US-ADJ-62`). *Enmendado por `US-ADJ-62`: antes decía "Contactá a un Administrador para restablecer tu contraseña", sin link, porque la recuperación self-service no desbloqueaba.* |
| Formulario | Campos deshabilitados tras el bloqueo, botón "Ingresar" a todo el ancho, deshabilitado |

> Corrección 2026-08-23 (UAT/UX en vivo): la primera versión de esta fila decía que la
> pantalla "extiende `wireframes-identidad.md` §2.2" con el mismo encabezado que el resto de
> Login — la implementación siguió ese texto en vez del prototipo HTML (`#login-bloqueada`),
> que ya mostraba el layout propio descripto arriba. Corregido para que la spec escrita deje
> de contradecir al prototipo, que es la fuente de verdad.

### 2.9 Login — cuenta deshabilitada (`#login-deshabilitada`) — `US-ADJ-59`

**Evento:** intento de `IniciarSesion` sobre una cuenta con `deshabilitada = true` (INV-ID-18).
El backend responde `403` con `detail.codigo = "cuenta_deshabilitada"`; el frontend lo distingue
del `403` de cuenta bloqueada (que sigue siendo texto plano).

| Elemento | Detalle |
|---|---|
| Layout | Idéntico a `#login-bloqueada` (§2.8): tarjeta centrada sin el bloque de marca, ícono de la app (40px) sobre el título "Ingresar" |
| Alerta | Destructiva, con ícono 🚫: "Cuenta deshabilitada" — "Tu cuenta fue dada de baja y no puede iniciar sesión. Contactá a un Administrador." — **sin** link de recuperación de contraseña: recuperarla no reactiva una cuenta deshabilitada (solo un Administrador la reactiva) |
| Formulario | Campos deshabilitados, botón "Ingresar" a todo el ancho, deshabilitado — igual que §2.8 |
| Diferencia con §2.8 | Cambian el ícono (🚫 en vez de 🔒), el título y el texto; no hay cuenta "pendiente de desbloqueo", la acción es siempre hablar con un Administrador |

Fuente de verdad visual: prototipo `identidad-cuentas-administracion.html`, pantalla
"8. Login — cuenta deshabilitada".

### 2.10 Eliminar / deshabilitar cuenta (`EliminarCuenta`) — `US-ADJ-60`

> **Aclaración de origen:** esta pantalla se construyó en la prueba de estabilización
> (2026-09-09/10, `EliminarCuenta.tsx`) sin artefacto UX aprobado. Esta sección la documenta por
> primera vez y define la variante de Administrador de `US-ADJ-60`. Alcanza a las tres variantes de
> rol; solo la de Administrador cambia respecto de lo ya implementado.

**Evento:** el Administrador pulsa el ícono de eliminar de una fila de Cuentas (`DELETE /usuarios/{id}`).
El backend borra físicamente la cuenta si no tiene datos asociados y la deshabilita si los tiene —
**salvo un Administrador, que nunca se borra: siempre se deshabilita** (INV-ID-19).

| Elemento | Docente / Estudiante (ya implementado) | **Administrador (nuevo, `US-ADJ-60`)** |
|---|---|---|
| Título y subtítulo | "Eliminar cuenta" | **"Deshabilitar cuenta"** — "Cuenta de Administrador" |
| Breadcrumb | Administración › Cuentas › Eliminar | Administración › Cuentas › **Deshabilitar** |
| Cuenta | Nombre y email de la cuenta | Igual, rotulado "Cuenta a deshabilitar" |
| Aviso (ámbar, informativo) | "Si tiene datos asociados … se deshabilita en vez de borrarse … Si no tiene datos asociados, se borra en forma permanente y no se puede deshacer." | **"Un Administrador nunca se borra"** — "La cuenta se deshabilita: deja de poder iniciar sesión, pero no se pierde nada y se puede reactivar desde el listado. No se puede deshabilitar al único Administrador operativo." |
| Acciones | "Sí, eliminar" (destructivo) · "Cancelar" | **"Sí, deshabilitar"** (destructivo) · "Cancelar" |

**Estado de error — único Administrador operativo (`409`):** al confirmar, si la cuenta es el único
Administrador operativo, la pantalla **no navega**: muestra arriba una alerta destructiva con ícono ⛔,
"No se puede deshabilitar esta cuenta" — "Es el único Administrador operativo. El sistema necesita al
menos uno activo: habilitá primero a otro Administrador y volvé a intentar." Los botones quedan
habilitados (el Administrador puede reintentar tras habilitar a otro, o cancelar). Hoy `handleEliminar`
no captura errores: este estado es nuevo.

Fuente de verdad visual: prototipo `identidad-cuentas-administracion.html`, pantallas "9. Deshabilitar
Administrador" y "10. Error — único Administrador".

### 2.11 Login — cuenta bloqueada temporalmente (`#login-bloqueada-temporal`) — `US-ADJ-60`

**Evento:** intento de `IniciarSesion` sobre la cuenta del **último Administrador operativo**
bloqueada de forma temporal por 3 intentos fallidos (INV-ID-21). El backend responde `403` con
`detail.codigo = "cuenta_bloqueada_temporal"` y `reintentar_en_segundos`.

| Elemento | Detalle |
|---|---|
| Layout | **El del login normal** (con marca, "Iniciar sesión" y su subtítulo), **no** el de §2.8/§2.9: a diferencia de esas dos, acá el usuario puede volver a intentar |
| Alerta | Destructiva, con ícono ⏳: "Cuenta bloqueada temporalmente" — "Superaste el máximo de intentos. Podés volver a intentar en unos {N} minutos." (`N` = `reintentar_en_segundos` redondeado hacia arriba a minutos; mínimo 1) |
| Formulario | **Habilitado.** Un intento antes de que venza vuelve a mostrar la alerta con el tiempo restante; no consume intentos ni extiende el bloqueo |
| Diferencia con §2.8 | El bloqueo permanente (§2.8) deshabilita el formulario y manda a un Administrador; este se levanta solo y no necesita a nadie |

> **Decisión de diseño a confirmar:** formulario habilitado en vez de deshabilitado como en §2.8/§2.9,
> porque el bloqueo es transitorio y deshabilitarlo obligaría a recargar la página para reintentar.
> Alternativa: deshabilitarlo igual y pedir recargar.

Fuente de verdad visual: prototipo `identidad-cuentas-administracion.html`, pantalla "11. Login —
bloqueada temporalmente".

---

## 3. Responsive

Mismo criterio que `wireframes-identidad.md` §3 y `wireframes-banco-preguntas.md` §3: las
pantallas de administración (`cuentas`, `cuenta-detalle`, `cuenta-resetear`) usan layout de
una columna con tabla que hace scroll horizontal por debajo de 560px; las pantallas de
formulario angosto (`cambiar-password`, `cuenta-reseteada`) reutilizan la tarjeta centrada de
ancho máximo ~420-480px del patrón de auth.

No aplica el escenario 2 de RNF Usabilidad (legibilidad en proyección) — mismo criterio que
`wireframes-identidad.md` §3.

---

## 4. Fuera de alcance de este wireframe

- Alta de Administrador (ya excluida en `wireframes-identidad.md` §4).
- Edición de datos de perfil (nombre, email, comisión) desde el detalle de cuenta — RF-03 no
  lo pide.
- Recuperación de contraseña self-service por email (link "olvidé mi contraseña" en login) —
  no existe en v1, mediado siempre por Administrador (`BC-identidad-modelo.md` §9, punto 3).
- Historial/auditoría de bloqueos o reseteos — sin RNF de auditoría que lo exija en v1
  (mismo criterio que hot spot 2 del modelo de dominio).

---

## 5. Próximo paso

Prototipo y spec completos — aprobados por Víctor en la sesión de modelado del 2026-08-19.
Pasan a las specs US-IEDD de la Iteración 2 (`docs/specs/inc2/US-2.2.1` a `US-2.2.9`,
`docs/plans/inc2/inc2-candidatas.md`).
