# US-ADJ-67: El Docente genera un link de invitación grupal con vencimiento corto

**Estado**: `Implementada`
**Iteracion / Sprint**: `Incremento 9 — Correcciones y robustez`, Iteración 2
**Tipo**: `ajuste de producto` backend + frontend (reemplaza el link individual en la UI; matiza `ADR-012`)
**Agregado principal afectado**: `Invitacion`
**Bounded Context**: Identidad
**Origen**: prueba real con estudiantes sobre la VM de GCP (2026-11-06): el Docente compartió un único link con toda la clase y solo el primer estudiante pudo usarlo (14 consultas del preview, 3 rechazos del registro y 6 estudiantes que terminaron por autoregistro).
**Issue**: [#590](https://github.com/vvalotto/cognion/issues/590)
**Interactúa con**: `ADR-012` (invitación: un solo uso, 7 días), `RF-01`, `RF-25` (autoregistro), `US-ADJ-26` (generar invitación desde el Docente), `US-ADJ-08` (preview), `US-ADJ-68` (el token no aparece en el log, ya hecha), `#605` (el registro exige la política de contraseña).

---

## Fuente de verdad UX

- `docs/design/ux/wireframes-portal-entrada.md` §3.4 (detalle de comisión del Docente: link grupal, estados, desactivar) y §4.
- `docs/design/ux/wireframes-identidad.md` §2.4 (motivos de link no válido) y §2.3 (registro).
- Prototipos: `docs/design/ux/prototipos/portal-entrada.html` (pantalla 7) e `identidad-registro-login.html` (`#registro-error`, `#registro-requisitos`).
- Aprobados por Víctor el 2026-11-08.

---

## Descripcion (lenguaje de negocio)

Como **Docente que da una clase**,
quiero **generar un solo link que toda la comisión pueda usar durante un tiempo corto, y poder desactivarlo**,
para **que mis estudiantes se registren sin que yo tenga que repartir un link por persona, y sin dejar un link abierto para siempre**.

---

## Contexto

La invitación actual es individual: un solo uso y 7 días (`ADR-012`). En la prueba real el Docente la mostró a toda la clase; el primero la consumió y el resto recibió "ya fue utilizada". El uso del Docente es razonable: en una clase se comparte un link por pantalla o por chat.

El autoregistro de Estudiante (`RF-25`) ya permite que cualquiera se registre en cualquier comisión sin invitación: el link grupal no abre una puerta nueva, solo la facilita y la acota en el tiempo.

El criterio 5 del Issue (enmascarar `/invitaciones/<token>` en el log) ya lo cumplió `US-ADJ-68`. Además, el Issue cita `INV-ID-13` como "un solo uso"; los invariantes reales son `INV-ID-01` (uso único) e `INV-ID-03` (vigencia).

## Decisiones tomadas (Víctor, 2026-11-08, #593)

- **Duraciones elegibles:** 15 minutos, 1 hora y 1 día; por defecto 1 hora.
- **Sin cupo máximo** de registros.
- **El link grupal reemplaza al individual en la UI.** El backend individual se conserva (compatibilidad, tests y UAT); las invitaciones individuales ya emitidas siguen valiendo hasta que venzan.
- **Un solo link grupal vigente por comisión:** generar uno nuevo desactiva el anterior.
- El link solo da de alta **Estudiantes**: el alta de Docentes no usa invitaciones.

## Especificacion del comportamiento

**Modelo.** `Invitacion` gana tres atributos: `grupal` (bool, `false` en las existentes), `usos` (cantidad de registros hechos con ella) y `revocada_en` (nullable). Estados de una invitación: *vigente*, *vencida* (`ahora >= expira_en`), *revocada* (`revocada_en` no nulo) o *usada* (solo individual, `usada_en` no nulo). Una invitación grupal se puede usar cualquier cantidad de veces mientras esté vigente; no marca `usada_en`.

**Generar.** Un Docente asignado a la comisión genera un link grupal indicando la duración (`15`, `60` o `1440` minutos; por defecto `60`). Se crea con `expira_en = ahora + duración` y, **en la misma operación**, se revoca el link grupal vigente que hubiera para esa comisión. Otra duración responde `422`; un Docente no asignado, `403`.

**Última invitación grupal.** El Docente consulta la última invitación grupal de su comisión para ver el estado al volver a la pantalla: vigente (con token, vencimiento y cantidad de registrados), vencida o revocada (con la cantidad de registrados, sin token). Sin ninguna, no hay estado.

**Desactivar.** El Docente asignado desactiva el link grupal vigente: se fija `revocada_en`. La operación es idempotente y no afecta a quienes ya se registraron. Un Docente no asignado recibe `403`.

**Registro.** Con un link grupal vigente cada registro crea un Estudiante en la comisión e incrementa `usos` **de forma atómica** (60 estudiantes pueden registrarse a la vez sin perder cuentas). Si el registro se rechaza (email repetido, contraseña inválida) no cuenta como uso.

**Motivos distintos.** El preview (`GET /invitaciones/{token}`) y el registro (`POST /registro`) informan el motivo con `detail = {"codigo": ..., "mensaje": ...}` y los códigos `invitacion_invalida` (404), `invitacion_vencida`, `invitacion_revocada` e `invitacion_usada` (422). Los errores de contraseña del registro llevan su propio código (`password_invalida`, 422), para que la pantalla no los confunda con un link inválido. Los status HTTP no cambian.

**Pantallas.**
- Detalle de comisión del Docente: selector de duración, "Generar link grupal", link con "Copiar", estado ("Vigente", cuándo vence, cuántos se registraron), "Desactivar link" y la leyenda de reemplazo; avisos "Venció" y "Desactivado" (wireframe §3.4).
- Link no válido: cuatro motivos con su orientación (wireframe §2.4); el registro con una contraseña rechazada por el servidor muestra el error en el formulario.

## Escenarios (BDD)

1. **Generar con duración por defecto.** El Docente asignado genera un link grupal sin indicar duración → `201`, vence en 1 hora.
2. **Duraciones elegibles.** 15 minutos, 1 hora y 1 día se aceptan; cualquier otra → `422`.
3. **Docente no asignado.** Generar o desactivar un link de una comisión ajena → `403`.
4. **Varios estudiantes con el mismo link.** Tres estudiantes se registran con el mismo link → los tres `201`, los tres en la comisión, `usos = 3`.
5. **Registros simultáneos.** Veinte registros a la vez con un link → veinte `201` y `usos = 20` exactos.
6. **Link vencido.** Pasada la vigencia, el preview y el registro responden `invitacion_vencida`.
7. **Desactivar.** Tras desactivar, el preview y el registro responden `invitacion_revocada`; los ya registrados siguen en la comisión. Desactivar dos veces no falla.
8. **Un solo link vigente.** Generar un link nuevo desactiva el anterior (el anterior responde `invitacion_revocada`, el nuevo funciona).
9. **Última invitación grupal.** Vigente con token y registrados; vencida o revocada sin token; sin links, sin estado.
10. **El individual no cambia.** La invitación individual sigue siendo de un solo uso y 7 días; la segunda vez responde `invitacion_usada`.
11. **Contraseña inválida.** Con un link grupal vigente, una contraseña que no cumple la política responde `password_invalida` y no cuenta como uso; el link sigue sirviendo.
12. **Email repetido.** Responde `409` y no cuenta como uso.
13. **Pantallas.** El detalle de comisión del Docente muestra el estado del link y permite generarlo y desactivarlo; la pantalla de link no válido muestra el motivo informado; el registro muestra en el formulario el error de contraseña del servidor.

## Fuera de alcance

Cupo máximo; QR o envío del link por email; lista nominal de quién se registró con cada link (solo la cantidad); duraciones configurables; eliminar el endpoint individual; que el link alcance a Docentes; renovar o extender un link vencido (se genera uno nuevo).

## Notas para `/implement-us`

- **Migración nueva** con las tres columnas de `invitacion` (`grupal` y `usos` con valor por defecto para las filas existentes), y un `downgrade` que las quite. La guarda de `US-8.3.4` exige que las migraciones y su `downgrade` usen constraints con nombre; el chequeo de `tests/uat/inc8/verificar_migraciones.sh` debe seguir en verde.
- **Atomicidad del contador:** el incremento de `usos` tiene que ser una sola sentencia (`UPDATE ... SET usos = usos + 1`), no leer-modificar-guardar. El registro simultáneo se prueba con una base real.
- **Un solo link vigente:** generar y revocar el anterior en la misma transacción; considerar un índice parcial único (`comision_id` donde `grupal` y `revocada_en` es nulo y no venció no se puede expresar con `expira_en`, así que la regla se aplica en el caso de uso, no en la base).
- **Email repetido en paralelo:** dos registros del mismo email a la vez hoy terminarían en una violación de unicidad; verificar si ya se traduce a `409` y, si no, hacerlo (con un link grupal el doble toque es más probable).
- **Contrato de errores:** hoy los errores de invitación llevan `detail` como texto. Pasar a un objeto con `codigo` cambia lo que leen `Registro.tsx`, `InvitacionPreview` y los tests existentes; `extractError` ya soporta `detail.mensaje`.
- **Frontend:** `ComisionDetalleDocente.tsx`, `RegistroError.tsx` (motivo por `?motivo=`), `Registro.tsx` (preview y registro) y el cliente `identidad-comisiones-api.ts`. Verificación en navegador real al cierre de la iteración: abrir el link con tres estudiantes, vencerlo y desactivarlo, con celular.
- **Documentación a enmendar:** `ADR-012` (nota que remite al ADR nuevo), `ADR-027` (nuevo: invitación grupal, matiza el uso único y los 7 días), `BC-identidad-modelo.md` (agregado `Invitacion`, `INV-ID-01` e `INV-ID-03`, nuevo invariante de vigencia grupal), `wireframes` (ya hechos) y el docstring de `Invitacion`.
- Mantener la sincronía de los `Fake*` de `tests/unit/` si se toca el puerto `InvitacionRepositoryPort`.
- Es la US más grande de la iteración: si al planificar supera lo razonable, separar backend y frontend en dos commits dentro de la misma US.
