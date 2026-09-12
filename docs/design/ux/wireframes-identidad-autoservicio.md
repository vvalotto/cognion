# BC Identidad — Wireframes: Autoservicio (Recuperación, Autoregistro, Contraseña)

> Estado documental: **vigente — aprobado por Víctor en el cierre del Issue
> [#320](https://github.com/vvalotto/cognion/issues/320) (US-ADJ-34, Iteración 0, Incremento
> 5-ADJ). Implementación: §2 (toggle + indicador de fortaleza) completa (`US-ADJ-35`/`36`);
> §3 (link "olvidaste tu contraseña"), §4 (recuperación), §5 (autoregistro) y §6 (menú de
> usuario) siguen sin implementar — Iteraciones 2, 3 y `US-ADJ-37` respectivamente.**
> Alcance: hallazgos de Identidad y cuentas de `hallazgos-cognion.md` — toggle mostrar/ocultar
> contraseña, política de contraseña segura, recuperación de contraseña por autoservicio,
> autoregistro de Docente/Estudiante con selección de perfil, logout voluntario y
> descubribilidad de "Cambiar contraseña". Amplía `wireframes-identidad.md` §2.1 (Login) y
> `wireframes-cuentas-administracion.md` §2.5-2.8 (Cambiar contraseña, Login bloqueada) — no
> los reemplaza.
>
> Fuente: `docs/rf/RF_v1.md` (RF nuevos de recuperación y autoregistro, numeración definitiva
> pendiente de la Iteración 5 de este incremento), `docs/design/domain/BC-identidad-modelo.md`
> §13 (`US-ADJ-32`, aprobado — comandos `SolicitarRecuperacionPassword`,
> `ConfirmarNuevaPassword`, `AutoregistrarDocente`, `AutoregistrarEstudiante`, `INV-ID-11`
> ampliada), `docs/plans/inc5-adj/inc5-adj-candidatas.md`.
>
> Prototipo: `docs/design/ux/prototipos/identidad-autoservicio.html` — navegable, 11 pantallas.

---

## 1. Identidad visual

Misma paleta y tipografía que `wireframes-identidad.md` §1 y `wireframes-cuentas-administracion.md`
§1 (azul institucional `#1D75B5`, verde de acento `#53AA74`, Roboto) — continuidad visual, sin
redefinir tokens. Primitivas **nuevas** de este documento: `.pwd-toggle` (botón de
mostrar/ocultar sobre cualquier `input[type=password]`), `.pwd-strength` (indicador de
fortaleza, 3 segmentos + etiqueta), `.profile-card` (tarjeta de selección de perfil en
autoregistro), `.user-menu` (menú desplegable del header, reemplaza el bloque `.who` estático
de pantallas anteriores por un botón que abre un dropdown).

---

## 2. Componente transversal — Mostrar/ocultar contraseña e indicador de fortaleza

Aplica a **todo** campo `type="password"` del sistema (existentes y nuevos): login, registro
por invitación, cambiar mi contraseña, resetear contraseña (Administrador), alta de Docente,
recuperación de contraseña, autoregistro. No es una pantalla propia — es una ampliación de
`.field` ya existente en cada formulario.

| Elemento | Detalle |
|---|---|
| Toggle | Ícono 👁 a la derecha del input, alterna `type="password"`/`type="text"` sin recargar ni perder el valor tipeado; ícono cambia a 🙈 mientras está visible |
| Indicador de fortaleza | Solo en campos de contraseña **nueva** (no en el login ni en "contraseña actual" de cambiar contraseña) — 3 barras + etiqueta (Débil/Media/Fuerte), calculado en cliente sobre las mismas 4 reglas de `INV-ID-11` (longitud ≥ 12, mayúscula, número, símbolo): 1 regla cumplida = Débil, 2-3 = Media, las 4 = Fuerte |
| Detalle de reglas | Debajo del indicador, lista compacta de las 4 reglas con ✓ en las cumplidas — mismo patrón que un checklist de requisitos, no un mensaje de error hasta que se intenta enviar |
| Validación de servidor | El indicador es guía de UX, no reemplaza la validación real — el backend sigue rechazando con `PasswordDemasiadoCorta`/`PasswordSinComplejidadSuficiente` si no cumple, aunque el cliente falle en calcularlo bien |

---

## 3. Pantallas — Login (ampliación de `wireframes-identidad.md` §2.1)

### 3.1 Login (`#login`)

Mismos campos y comando que `wireframes-identidad.md` §2.1 (`IniciarSesion`). **Cambios sobre
esa spec:**

| Elemento | Detalle |
|---|---|
| Campo Contraseña | Ahora con toggle mostrar/ocultar (§2) |
| Link nuevo | "¿Olvidaste tu contraseña?" — a la derecha, sobre el botón "Ingresar" — navega a §4.1 |
| Link nuevo | "¿No tenés cuenta? Registrate" — footer, navega a la selección de perfil de autoregistro (§5.1) |

**Nota de diseño — `#login-bloqueada` (`wireframes-cuentas-administracion.md` §2.8) no cambia:**
una cuenta bloqueada sigue sin poder loguearse aunque el usuario recupere su contraseña por este
flujo nuevo — `ConfirmarNuevaPassword` cambia `password_hash` pero no toca `Usuario.bloqueada`
ni los contadores de intentos fallidos (`BC-identidad-modelo.md` §13.4). El mensaje de esa
pantalla ("Contactá a un Administrador") sigue siendo correcto sin cambios.

---

## 4. Pantallas — Recuperación de contraseña

### 4.1 Recuperar — solicitar (`#recuperar-solicitar`)

**Actor:** cualquiera, sin autenticar.
**Comando:** `SolicitarRecuperacionPassword(email)`.

| Elemento | Detalle |
|---|---|
| Campo | Email |
| Acción primaria | "Enviar link de recuperación" |
| Link secundario | "‹ Volver a iniciar sesión" |

### 4.2 Recuperar — email enviado (`#recuperar-solicitado`)

**Evento:** `RecuperacionPasswordSolicitada` (o ningún efecto real si el email no existe —
misma respuesta al llamante, INV-ID-17).

| Elemento | Detalle |
|---|---|
| Mensaje | Genérico: "Si el email ingresado corresponde a una cuenta, te enviamos un link..." — nunca confirma ni niega la existencia de la cuenta |
| Aclaración | Vigencia del link: 1 hora (INV-ID-13) |
| Acción | "Volver a iniciar sesión" |

### 4.3 Recuperar — definir nueva contraseña (`#recuperar-nueva`)

**Actor:** quien abrió el link del email (token en la URL).
**Comando:** `ConfirmarNuevaPassword(token, password_nueva)`.

| Elemento | Detalle |
|---|---|
| Campos | Contraseña nueva (con toggle + indicador de fortaleza, §2), Confirmar contraseña nueva (con toggle) |
| Validación de cliente | Las 4 reglas de `INV-ID-11`, coincidencia entre nueva y confirmación |
| Acción primaria | "Guardar nueva contraseña" |
| Sin | Campo de "contraseña actual" — a diferencia de `CambiarPassword`, este flujo no la requiere (el usuario ya demostró control del email vía el token) |

### 4.4 Recuperar — link vencido/inválido/ya usado (`#recuperar-token-invalido`)

**Evento:** rechazo por `TokenRecuperacionVencido`, `TokenRecuperacionInvalido` o
`TokenRecuperacionYaUsado`.

| Elemento | Detalle |
|---|---|
| Mensaje | "Este link ya no es válido" + explica que los links valen 1 hora y son de un solo uso |
| Acción | "Pedir un nuevo link" — vuelve a §4.1 |
| Sin | Formulario de contraseña — mismo criterio que `wireframes-identidad.md` §2.4 (registro con link vencido): no sugerir que se puede completar la acción de todos modos |

No se distingue en la UI entre vencido/inválido/ya usado — mismo mensaje para los tres,
mismo criterio de simplicidad que `wireframes-identidad.md` §2.4.

### 4.5 Recuperar — éxito (`#recuperar-exito`)

**Evento:** `PasswordRecuperada`.

| Elemento | Detalle |
|---|---|
| Confirmación | "Contraseña actualizada. Ya podés iniciar sesión con tu nueva contraseña." |
| Acción primaria | "Iniciar sesión" |

---

## 5. Pantallas — Autoregistro con selección de perfil

### 5.1 Elegir perfil (`#autoregistro-perfil`)

**Actor:** cualquiera, sin autenticar.

| Elemento | Detalle |
|---|---|
| Selección | Dos tarjetas (`.profile-card`): "Soy Docente" / "Soy Estudiante" — sin tercera opción de Administrador (INV-ID-15) |
| Link secundario | "¿Ya tenés cuenta? Iniciar sesión" |

### 5.2 Autoregistro — Docente (`#autoregistro-docente`)

**Comando:** `AutoregistrarDocente(nombre, email, password)`.

| Elemento | Detalle |
|---|---|
| Contexto | Tag "Perfil: Docente" (informativo, no editable — mismo patrón que `wireframes-identidad.md` §2.6) |
| Campos | Nombre completo, Email, Contraseña (con toggle + indicador, §2), Confirmar contraseña |
| Copy de ayuda | "Tu cuenta queda activa de inmediato" — sin mención a aprobación ni verificación de email (INV-ID-16) |
| Acción primaria | "Crear cuenta" |
| Link secundario | "‹ Elegir otro perfil" |

### 5.3 Autoregistro — Estudiante (`#autoregistro-estudiante`)

**Comando:** `AutoregistrarEstudiante(nombre, email, password, comision_id)`.

| Elemento | Detalle |
|---|---|
| Contexto | Tag "Perfil: Estudiante" |
| Selectores | Materia → Comisión, en cascada (elegir materia acota las comisiones visibles) — mismo patrón de selector ya usado en `US-2.1.11`/`US-4.1.3` |
| Campos | Nombre completo, Email, Contraseña (con toggle + indicador), Confirmar contraseña |
| Orden de campos | Materia/Comisión **antes** que los datos personales — refuerza que la elección de comisión es la decisión principal de esta pantalla, mismo criterio que el `comision-tag` de `wireframes-identidad.md` §2.3 (contexto visible antes que el formulario) |
| Acción primaria | "Crear cuenta" |
| Link secundario | "‹ Elegir otro perfil" |

### 5.4 Autoregistro — éxito (`#autoregistro-exito`)

**Evento:** `UsuarioAutoregistrado`.

| Elemento | Detalle |
|---|---|
| Confirmación | "Cuenta creada. Tu cuenta ya está activa. Iniciá sesión para continuar." — mismo criterio que `wireframes-identidad.md` §2.5: sin login automático post-registro |
| Acción primaria | "Iniciar sesión" |
| Sin | Pantalla única para ambos perfiles — no hay copy condicional por Docente/Estudiante, el mensaje genérico alcanza |

---

## 6. Pantalla — Menú de usuario (descubribilidad, `US-ADJ-37`)

### 6.1 Menú de usuario (`#menu-usuario`, mockup del header, no una ruta propia)

**Actor:** cualquier Usuario autenticado (Docente, Estudiante o Administrador).

| Elemento | Detalle |
|---|---|
| Punto de entrada | El bloque `.who` (avatar + nombre) de `app-header`, hoy estático en todas las pantallas autenticadas (`portal-entrada.html`, `analytics-portal-desempeno.html`, etc.), pasa a ser un botón (`.who-btn`) que abre un dropdown (`.user-menu`) |
| Contenido del menú | Encabezado con nombre + email; dos ítems: "🔑 Cambiar contraseña" (navega a `/mi-cuenta/cambiar-password`, pantalla ya existente desde `US-2.2.8`, sin cambios) y "↩ Cerrar sesión" (invoca `clearSession()`, ya existente desde `US-1.1.6`, y navega a `/login`) |
| Mismo menú para los 3 roles | Sin variación de contenido por rol — ambos ítems son universales |
| Alcance | Afecta el componente compartido del header (`AppLayout`/`AppNav`, `US-ADJ-27`) — no una pantalla nueva, se repite en toda vista autenticada |

---

## 7. Responsive

Mismo criterio que `wireframes-identidad.md` §3: pantallas de auth (login, recuperar,
autoregistro) usan tarjeta centrada de ancho máximo 420-480px, pantalla completa por debajo de
480px. El menú de usuario (§6) colapsa a la misma posición (esquina superior derecha) en
mobile, sin cambios de contenido.

No aplica el escenario 2 de RNF Usabilidad (legibilidad en proyección) — mismo criterio que
`wireframes-identidad.md` §3.

---

## 8. Fuera de alcance de este wireframe

- Verificación de email en el autoregistro — decisión de producto ya tomada (sin verificación
  en v1, `BC-identidad-modelo.md` §13.4, INV-ID-16).
- Aprobación del Administrador sobre cuentas autoregistradas — decisión ya tomada (activa de
  inmediato).
- Cualquier cambio a `#login-bloqueada` — sigue sin recuperación self-service, ver nota de
  §3.1.
- Rediseño del `.who` estático en pantallas que todavía no se tocan en este incremento — el
  cambio a `.who-btn`/`.user-menu` se aplica al componente compartido, así que se propaga solo
  con el cambio de `AppNav.tsx`, sin tocar cada pantalla una por una.

---

## 9. Hot spots — resueltos con Víctor

Ninguno pendiente — decisiones de alcance ya cerradas en la conversación previa a este
documento (convivencia con invitación, roster de Estudiante, activación inmediata de Docente,
canal de email de recuperación) y reflejadas en `BC-identidad-modelo.md` §13.

---

## 10. Próximo paso

Prototipo y spec completos — pasan a aprobación explícita de Víctor en el comentario de cierre
de https://github.com/vvalotto/cognion/issues/320 (`US-ADJ-34`, DoD tipo `Modelado`,
`docs/plans/WORKFLOW-DESARROLLO.md` §2). Habilita las Iteraciones 1 a 3 de
`docs/plans/inc5-adj/inc5-adj-candidatas.md`.
