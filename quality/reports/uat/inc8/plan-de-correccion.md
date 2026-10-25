# Plan de corrección — UAT de la versión local `v0.9.0`

Documento de **priorización, no de ejecución** (`PROCEDIMIENTO-UAT.md` §11): propone qué hacer con cada hallazgo de `registro-hallazgos.md`; no implementa nada. **Estado: aprobado por Víctor el 2026-10-25** (gate de cierre cumplido). Quedaron con la propuesta por defecto, a confirmar al retomar: `v0.9.0` espera solo a los 🔴 (§5, 2), cargar/editar pregunta del hallazgo #6 sin decidir (§5, 3) y el hallazgo #3 después de la etiqueta (§5, 4); la prueba del iPhone con Norton pausado (#8) sigue pendiente de Víctor. Issue de la UAT: [#567](https://github.com/vvalotto/cognion/issues/567).

## 1. Balance de la UAT (2026-10-25)

Pasaron: la instalación limpia con un comando (A), la siembra de las 340 preguntas con simulación, idempotencia y validación (B, 0 diferencias contra los archivos de origen), el alta de actores desde la aplicación incluida la invitación desde un iPhone (C), el período abierto con pausa y reanudación, los reportes del Docente, la sesión en vivo con iPad (sala de espera, bloqueo sin participantes, cancelación, reconexión, histograma, ranking, podio) y el RBAC (D), el respaldo, el ensayo de restauración, detener y retomar sin perder datos (E), y el acceso por IP y por nombre, con la tapa cerrada (F). No se ejecutó E6 (decisión de Víctor). **10 hallazgos: 3 🔴, 3 🟡, 4 ⚪ (con 1 🔴 condicionado).**

## 2. Qué bloquea `v0.9.0`

| # | Hallazgo | Sev. | Track | Propuesta | Bloquea |
|---|---|---|---|---|---|
| 2 | El modo consola de emails no escribe nada en el log (recuperar contraseña, invitaciones y avisos de actividad, invisibles) | 🔴 | Formal (`src/`) | `US-ADJ` de logging local: configurar el logging de la aplicación al arrancar y un test que verifique la salida real del servidor, no solo `caplog` | **Sí** |
| 7 | Las fechas de una actividad se guardan corridas 3 h (hora local tomada como UTC) | 🔴 | Informal si alcanza con el frontend | Enviar la fecha con su zona (`toISOString`) en los formularios con fecha; revisar "extender plazo" y los demás; verificar en navegador con la hora real | **Sí** |
| 8 | El iPhone no abre el WebSocket (403, URL absoluta); el iPad y la Mac sí. Causa probable: Norton Mobile Security como VPN de dispositivo | 🔴→🟡 | Spike y, si hace falta, formal | **Víctor:** repetir la prueba con Norton pausado. Si el iPhone anda, queda 🟡 (entorno) y no bloquea; documentarlo. Si sigue igual, `US-ADJ`: aceptar la forma absoluta del pedido en el servidor | **Condicional** |

## 3. Pueden esperar a `v0.9.1`

| # | Hallazgo | Sev. | Track | Propuesta |
|---|---|---|---|---|
| 9 | El log de acceso guarda JWT e invitaciones completos | 🟡 | Formal | Se agrupa con el #2 (misma área: logging); si se separa, filtrar `token=` del log de acceso |
| 3 | `bootstrap_administrador` pide la contraseña una sola vez | 🟡 | Formal (`src/identidad/frameworks/cli/`) | Pedirla dos veces y comparar |
| 4 | El link de invitación usa la dirección con la que el Docente abrió la app | 🟡 | Informal (docs) | Advertirlo en `DESPLIEGUE-LOCAL.md`; opcional: usar `FRONTEND_URL` |
| 6 | Unidad temática → Tema dependientes con "Todos", en los filtros del banco y en "Nueva actividad" | 🟡 | Informal (`frontend/`) | Decidido por Víctor; falta decidir si cargar/editar pregunta cambia igual |
| 1 | El título de la pestaña es `frontend` | ⚪ | Informal | Cambiar `frontend/index.html:7` a "Cognión" |
| 5 | Autoregistro sin "repetir email" | ⚪ | Informal | Agregar el campo en el formulario |
| 10 | `respaldar.sh` nombra todo `cognion_local-` aunque la base sea otra | ⚪ | Informal (script) | Usar el nombre de la base en el prefijo y la rotación |

## 4. Orden propuesto

1. **`US-ADJ` de logging local (#2, #9)**: formal, chica; es lo único que impide usar la recuperación de contraseña y ver las notificaciones en el despliegue local.
2. **Fix de fechas (#7)**: informal, pero se verifica en el navegador con la hora real de la Mac y se prueba que un parcial de 14:00 a 16:00 queda de 14:00 a 16:00.
3. **Prueba del iPhone con Norton pausado (#8)**: la hace Víctor; define si hay un `US-ADJ` más.
4. **Repetir solo los pasos afectados**: C4, C7, D1 (emails en el log), D1 (fechas) y, si hubo cambio, D5 con el iPhone.
5. **Lote informal de frontend** (#1, #5, #6) y de documentación (#4, #10), en uno o dos PRs, antes o después de la etiqueta según prefiera Víctor.
6. Con los 🔴 resueltos o reclasificados: cerrar `BL-013`, merge a `main`, etiqueta `v0.9.0`.

## 5. Decisiones pendientes de Víctor

- ¿Aprobás este plan y el orden?
- ¿`v0.9.0` espera también a los 🟡/⚪ o los dejás para `v0.9.1`? (Propuesta: solo los 🔴.)
- #6: ¿los formularios de cargar y editar pregunta cambian igual que los filtros?
- #3: ¿lo corregimos antes de etiquetar, dado que fue la causa probable de tu problema de contraseña?
