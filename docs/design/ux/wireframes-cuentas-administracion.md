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
| Extiende | `wireframes-identidad.md` §2.2 (Login — error) con una variante específica |
| Alerta | Destructiva: "Cuenta bloqueada", dirige explícitamente a contactar a un Administrador — sin link de recuperación self-service (no existe en v1) |
| Formulario | Campos deshabilitados tras el bloqueo, botón "Ingresar" deshabilitado |

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
