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

> **Enmienda 2026-11-08 (Inc.9 It.2, `US-ADJ-69`):** el mensaje del 1.º fallo sigue siendo genérico. A partir del 2.º fallo ver §2.2b, que **sí** revela que la cuenta existe (trade-off aceptado, ver abajo).

### 2.2b Login — te queda 1 intento (`#login-aviso`) — `US-ADJ-69`

**Origen:** observación O-1 de la UAT del 7-ADJ (#502). Decisión de Víctor del 2026-11-08 (#593): avisar antes del bloqueo.
**Evento:** `CredencialesInvalidas` con el 2.º fallo consecutivo (el 3.º bloquea la cuenta, INV-ID-10).

| Elemento | Detalle |
|---|---|
| Cuándo aparece | Solo tras el **2.º** fallo consecutivo de una cuenta existente. El 1.º fallo muestra el mensaje genérico de §2.2 |
| Mensaje | "Email o contraseña incorrectos" + "Te queda 1 intento antes del bloqueo de la cuenta." |
| Ayuda | Link "recuperala por email" hacia `/recuperar-password`, que además desbloquea la cuenta (`US-ADJ-62`) |
| Mismo patrón que | `CambiarPassword` ("Intentos restantes antes del bloqueo: N."), `US-2.2.8` |
| Campos | Igual que §2.2 |
| Sin | Contador en el 1.º fallo ni "te quedan 2 intentos": solo el último intento, para no dar más información de la necesaria |

**Trade-off de seguridad (aceptado por Víctor el 2026-11-08):** hasta ahora un email inexistente y una contraseña incorrecta respondían igual, así que no se podía saber si una cuenta existe. Este aviso aparece **solo en cuentas que existen**, así que permite distinguirlas. El bloqueo del 4.º intento ya filtraba la existencia de la cuenta. A esta escala (uso interno, 30 a 60 alumnos por comisión) se acepta. Queda fuera de alcance simular el aviso para emails inexistentes.

### 2.3 Registro — link válido (`#registro`)

**Actor:** Estudiante.
**Comando:** `RegistrarEstudiante(token, nombre, email, password)`.

| Elemento | Detalle |
|---|---|
| Contexto visible | Tag con la comisión a la que se va a unir (`comisión.materia` + identificador), tomada del `token` de la URL — refuerza que la asignación es automática (RF-01, INV-ID-05) |
| Campos | Nombre completo, Email, **Repetir email**, Contraseña, Confirmar contraseña |
| Validación de email | **Repetir email** debe coincidir con Email (sin espacios en los bordes y sin distinguir mayúsculas); "Los emails no coinciden." antes de enviar — mismo criterio que el autoregistro (`wireframes-identidad-autoservicio.md` §5.2, hallazgo #5 de la UAT de `v0.9.0`) |
| Validación de contraseña | **Enmienda 2026-11-08:** la política vigente es INV-ID-11 ampliada (`US-ADJ-36`): 12 caracteres, una mayúscula, un número y un símbolo, no "mínimo 8" como decía este documento. El checklist en vivo ya existe en la aplicación. Confirmar contraseña debe coincidir — validación de cliente antes de enviar; la regla de negocio la aplica el backend |
| Envío | **Enmienda 2026-11-08 (#605 Parte A, spike #595):** "Crear cuenta" queda deshabilitado mientras falte una regla del checklist, con la leyenda "Completá los requisitos de la contraseña para continuar." (ver `#registro-requisitos` en el prototipo) |
| Errores del servidor | **Enmienda 2026-11-08 (#605 Parte A):** el recuadro de error sigue arriba del formulario, pero al aparecer la pantalla se **desplaza hasta él y le da el foco** (en un celular el botón está debajo del pliegue y el error quedaba fuera de la vista). Si el `422` trae el detalle como lista (validación del formulario del servidor), se muestra un mensaje legible en español en vez de "Error inesperado." |
| Acción primaria | "Crear cuenta" |
| Link secundario | "¿Ya tenés cuenta? Iniciar sesión" — cubre el caso de que alguien reabra un link de invitación después de haberse registrado |

### 2.4 Registro — link vencido/inválido (`#registro-error`)

**Evento:** `RegistroRechazado` (`InvitacionVencida`, `InvitacionInvalida` o `InvitacionYaUsada`).

| Elemento | Detalle |
|---|---|
| Mensaje | Según el motivo (ver tabla de abajo) + "pedile a tu docente un link nuevo" |
| Acción | Indica que el docente debe generar un nuevo link — sin mecanismo de reenvío/extensión en la UI |
| Sin | Formulario de registro — no se muestran campos, para no sugerir que se puede completar el registro de todos modos |

**Enmienda 2026-11-08 (Inc.9 It.2, `US-ADJ-67`):** con el link grupal el motivo importa, porque cambia lo que el estudiante debe hacer. La pantalla distingue cuatro motivos (el prototipo los alterna con botones; la aplicación muestra el que informa el servidor):

| Motivo | Título | Orientación |
|---|---|---|
| Venció | "Este link venció" | El docente lo generó con una duración limitada y ya terminó; pedile uno nuevo |
| Desactivado | "Este link fue desactivado" | El docente lo desactivó; pedile uno nuevo |
| Ya usado (invitación individual anterior) | "Este link ya fue utilizado" | Si ya te registraste, iniciá sesión; si no, pedile uno nuevo |
| No es correcto | "Este link no es correcto" | Revisá que copiaste el link completo o pedile uno nuevo |

Reemplaza la decisión anterior de mostrar el mismo mensaje para los tres casos. Los links individuales ya emitidos siguen valiendo hasta que venzan, por eso "ya usado" se mantiene.

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
