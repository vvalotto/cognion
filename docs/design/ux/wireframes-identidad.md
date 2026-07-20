# BC Identidad — Wireframes: Registro, Login y Alta de Docente

> Estado documental: **vigente — aprobado por Víctor (US-1.0.2, Issue #4, cerrado 2026-07-18).**
> Usado como input de las specs US-IEDD de la Iteración 1 (`docs/specs/inc1/US-1.1.0`,
> `US-1.1.2`, `US-1.1.3`, `US-1.1.4`).
>
> Fuente: `docs/rf/RF_v1.md` (RF-01, RF-02), `docs/design/domain/BC-identidad-modelo.md`
> (comandos `RegistrarEstudiante`, `IniciarSesion`, `CrearUsuario`), `ADR-012` (invitación).
>
> Prototipo: `docs/design/ux/prototipos/identidad-registro-login.html` — navegable, 7 pantallas.

---

## 1. Identidad visual

Sin marca propia de Cognión definida a la fecha. Se tomó como referencia el sitio institucional
de la Facultad de Ingeniería (UNER) — mismo contexto académico donde se despliega el sistema —
para no partir de cero y anticipar consistencia con la identidad de la facultad:

| Token | Valor | Origen |
|---|---|---|
| Azul primario | `#1D75B5` | Barra superior y marca de ingenieria.uner.edu.ar |
| Verde de acento | `#53AA74` | Color de links e íconos de acción del sitio de referencia |
| Texto | `#2B2B2B` (primario) / `#707070` (secundario) | Gris de cuerpo de texto del sitio de referencia |
| Tipografía | Roboto | Tipografía del sitio de referencia |
| Marca | Isotipo propio (círculo azul con dos trazos tipo "onda", azul/verde) + wordmark "Cognión" | Diseño propio — **no reproduce el isotipo de la UNER**, solo su lógica cromática |

Esta paleta es un punto de partida operativo para no bloquear el desarrollo del frontend — no
reemplaza una definición de marca formal de Cognión, que puede revisarse en un incremento
dedicado a identidad visual sin impacto funcional.

---

## 2. Pantallas

### 2.1 Login (`#login` en el prototipo)

**Actor:** Docente, Administrador o Estudiante ya registrado.
**Comando:** `IniciarSesion(email, password)`.

| Elemento | Detalle |
|---|---|
| Campos | Email, Contraseña |
| Acción primaria | "Ingresar" |
| Sin | Link "olvidé mi contraseña" — no existe recuperación self-service en v1 (RF-03/RF-19 son Incremento 2, mediados por Administrador) |
| Sin | Cualquier mención a estado de cuenta bloqueada — RF-19/INV-ID-10 se diseña en Incremento 2 |

### 2.2 Login — error (`#login-error`)

**Evento:** `CredencialesInvalidas`.

| Elemento | Detalle |
|---|---|
| Mensaje | "Email o contraseña incorrectos" — genérico, no distingue si el email existe o no (no filtrar existencia de cuentas) |
| Campos | Se mantienen con el valor ingresado (excepto que la contraseña se re-solicita vacía en la implementación real; el prototipo la muestra con placeholder por claridad visual) |

### 2.3 Registro — link válido (`#registro`)

**Actor:** Estudiante.
**Comando:** `RegistrarEstudiante(token, nombre, email, password)`.

| Elemento | Detalle |
|---|---|
| Contexto visible | Tag con la comisión a la que se va a unir (`comisión.materia` + identificador), tomada del `token` de la URL — refuerza que la asignación es automática (RF-01, INV-ID-05) |
| Campos | Nombre completo, Email, Contraseña, Confirmar contraseña |
| Validación de contraseña | Mínimo 8 caracteres (INV-ID-11); confirmar contraseña debe coincidir — validación de cliente antes de enviar, la regla de negocio la aplica el backend |
| Acción primaria | "Crear cuenta" |
| Link secundario | "¿Ya tenés cuenta? Iniciar sesión" — cubre el caso de que alguien reabra un link de invitación después de haberse registrado |

### 2.4 Registro — link vencido/inválido (`#registro-error`)

**Evento:** `RegistroRechazado` (`InvitacionVencida`, `InvitacionInvalida` o `InvitacionYaUsada`).

| Elemento | Detalle |
|---|---|
| Mensaje | "Este link ya no es válido" + explicación de que no hay recuperación automática (`ADR-012`, INV-ID-03) |
| Acción | Indica que el docente debe generar un nuevo link — sin mecanismo de reenvío/extensión en la UI |
| Sin | Formulario de registro — no se muestran campos, para no sugerir que se puede completar el registro de todos modos |

No se distingue en la UI entre "vencido", "inválido" e "ya usado" — mismo mensaje y mismo
tratamiento para los tres casos (decisión de simplicidad; el backend sí distingue las tres
excepciones para logging/debug, pero no hay requerimiento de mostrarlas por separado al usuario).

### 2.5 Registro — éxito (`#registro-exito`)

**Eventos:** `InvitacionAceptada`, `UsuarioRegistrado`.

| Elemento | Detalle |
|---|---|
| Confirmación | Nombre de la comisión asignada, para reforzar que la asignación fue automática e inmediata |
| Acción primaria | "Iniciar sesión" — el registro no autentica automáticamente (decisión de simplicidad, sin login automático post-registro en v1) |

### 2.6 Admin — Alta de Docente (`#alta-docente`)

**Actor:** Administrador autenticado.
**Comando:** `CrearUsuario(nombre, email, password, perfil=Docente)` — parte de US-1.1.0.

| Elemento | Detalle |
|---|---|
| Contexto | Header de aplicación (distinto del header de auth): marca + usuario autenticado, breadcrumb "Cuentas › Nuevo Docente" |
| Perfil | Fijo en "Docente" (tag informativo, no editable) — **esta pantalla no ofrece elegir otro perfil**; alta de Administrador queda fuera de alcance de este wireframe |
| Campos | Nombre completo, Email, Contraseña temporal, Confirmar contraseña |
| Copy de ayuda | Aclara que la contraseña es temporal y que el docente la usa para generar invitaciones — sin prometer cambio de contraseña self-service (eso es RF-19, Incremento 2) |
| Acciones | "Crear cuenta de Docente" (primaria) / "Cancelar" (vuelve a login en el prototipo; en la app real vuelve al listado de cuentas) |
| Fuera de alcance de esta pantalla | Asignación a comisión (`AsignarDocenteAComision`) — comando separado, no se modela su UI en esta US |

### 2.7 Admin — Docente creado (`#alta-docente-exito`)

**Evento:** `UsuarioCreado`.

| Elemento | Detalle |
|---|---|
| Confirmación | Nombre y email del Docente creado |
| Aclaración | "Todavía no está asignado a ninguna comisión" — deja explícito que falta el paso de `AsignarDocenteAComision`, para que no se lea como flujo completo |
| Acción | "Dar de alta otro Docente" — flujo pensado para altas en lote al arrancar una comisión |

---

## 3. Responsive

RNF Usabilidad, escenario 1 (PC, tablet, smartphone; browsers vigentes). Las pantallas de
auth (login, registro) usan una tarjeta centrada de ancho máximo 420px que se adapta a
pantalla completa por debajo de 480px (sin bordes redondeados, ocupa el viewport). Las
pantallas de administración (`alta-docente`, `alta-docente-exito`) usan un layout de una sola
columna con ancho máximo de contenido — no requieren layout de grilla en esta iteración porque
no hay tablas ni datos tabulares todavía (eso corresponde al listado de cuentas, fuera de
alcance de esta US).

No aplica el escenario 2 de RNF Usabilidad (legibilidad en proyección de aula) — es específico
de las pantallas de sesión en vivo (Incremento 6), no de estas pantallas de identidad.

---

## 4. Fuera de alcance de este wireframe

- Alta de Administrador (decisión explícita de Víctor en la revisión de este artefacto).
- Cambio de contraseña (RF-19) y reseteo/desbloqueo por Administrador (RF-03) — Incremento 2.
- Estado de "cuenta bloqueada" en login (INV-ID-10) — depende de RF-19/RF-03, Incremento 2.
- Listado y gestión de cuentas existentes (tabla, edición, baja) — RF-03, Incremento 2.
- Asignación de Docente a Comisión (`AsignarDocenteAComision`) y creación de Comisión
  (`CrearComision`) — mismo US-1.1.0 a nivel de dominio, pero sin wireframe propio todavía;
  se decide si necesita UI dedicada o alcanza con un flujo simple al escribir la spec de
  US-1.1.0.

---

## 5. Próximo paso

Prototipo y spec completos — pasan a aprobación explícita de Víctor en el comentario de cierre
de https://github.com/vvalotto/cognion/issues/4 (DoD tipo `Modelado`,
`docs/plans/WORKFLOW-DESARROLLO.md` §2).
