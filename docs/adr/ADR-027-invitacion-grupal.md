# ADR-027 — Link de invitación grupal con vencimiento corto (matiza el uso único y los 7 días de ADR-012)

**Estado:** Aceptado
**Fecha:** 2026-11-08
**Origen:** `US-ADJ-67` (Issue [#590](https://github.com/vvalotto/cognion/issues/590)), Incremento 9, Iteración 2; decisiones de Víctor en #593. Relacionado con `ADR-012` (política de invitación) y `RF-25` (autoregistro).

---

## Contexto

`ADR-012` fijó la invitación como individual: un solo uso y 7 días. En la prueba real con estudiantes (2026-11-06) el Docente mostró **un único link a toda la clase**: el primero lo consumió y el resto recibió "ya fue utilizada" (14 consultas del preview, 3 rechazos del registro y 6 estudiantes que terminaron por autoregistro). El uso es razonable: en una clase se comparte un link por pantalla o por chat, no uno por persona.

El autoregistro de Estudiante (`RF-25`) ya permite registrarse en cualquier comisión sin invitación, así que un link para toda la clase no abre una puerta nueva: la facilita y la acota en el tiempo.

## Opciones consideradas

- **Dejar solo el link individual.** Obliga al Docente a generar un link por estudiante; en la prueba real no lo hizo y el costo lo pagaron los estudiantes.
- **Link grupal sin vencimiento ni cupo** (hasta que el Docente lo desactive). Un link filtrado serviría para siempre.
- **Link grupal con vencimiento corto y desactivación manual, sin cupo.** Elegida.
- **Link grupal con cupo máximo de registros.** Descartada por Víctor: con vencimiento corto y desactivación el riesgo ya está acotado, y el autoregistro permite entrar sin link.

## Decisión

Se agrega a `Invitacion` una variante **grupal**:

- **Varios usos** hasta que venza o el Docente la desactive; **sin cupo**.
- **Duración elegible** al generarla: 15 minutos, 1 hora (por defecto) o 1 día. No se puede extender: se genera otro.
- **Un solo link grupal vigente por comisión:** generar uno nuevo desactiva el anterior en la misma operación.
- **Desactivación manual** por el Docente asignado; no afecta a quienes ya se registraron.
- **Contador de registrados** (`usos`) sumado por la base en una sola sentencia, para que registros simultáneos no pierdan cuentas.
- **El grupal reemplaza al individual en la interfaz.** El backend individual se conserva (un uso, 7 días) y las invitaciones individuales ya emitidas valen hasta que venzan.
- **Motivos distintos:** el preview y el registro informan `invitacion_vencida`, `invitacion_revocada`, `invitacion_usada` o `invitacion_invalida` (y `password_invalida` para la contraseña) en `detail.codigo`, para que la pantalla oriente al estudiante.

## Justificación

El Docente da una clase con 30 a 60 estudiantes: un link por persona es un costo sin beneficio de seguridad cuando el autoregistro ya está abierto. Lo que sí reduce el riesgo es que el link **venza pronto** y se pueda **desactivar**; por eso se acotó la duración a tres valores y se agregó la desactivación. El contador atómico y el código de motivo salen de la prueba real: el primero evita perder cuentas con la clase entera registrándose a la vez, y el segundo evita que una contraseña rechazada se muestre como "este link no es válido".

## Impacto en configuración

- Migración `f7a3c9d15e82_invitacion_grupal`: columnas `grupal`, `usos` y `revocada_en` en `invitacion` (las filas existentes quedan como individuales).
- `docs/design/domain/BC-identidad-modelo.md`: agregado `Invitación` e invariantes `INV-ID-01`, `INV-ID-03` y los nuevos `INV-ID-22` e `INV-ID-23`.
- `ADR-012`: nota que remite a este ADR.
- Wireframes `wireframes-portal-entrada.md` §3.4 y `wireframes-identidad.md` §2.3 y §2.4 (ya actualizados en el gate UX).

## Consecuencias

- ✅ Una sola acción del Docente habilita a toda la clase; el estudiante entiende por qué un link no sirve.
- ✅ Un link filtrado deja de servir en minutos u horas, o cuando el Docente lo desactiva.
- ⚠️ Cualquiera que tenga el link puede registrarse mientras esté vigente; el riesgo es el mismo que el del autoregistro y se acota con la duración.
- ⚠️ Sin cupo, un link vigente puede registrar más estudiantes que los de la comisión: el Docente lo ve en el contador y puede desactivarlo.
- ⚠️ El `detail` de los errores de invitación pasa de texto a objeto (`codigo`, `mensaje`); los status HTTP no cambian.
