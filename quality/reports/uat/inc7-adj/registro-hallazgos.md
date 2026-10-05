# Registro de hallazgos — UAT de cierre del Incremento 7-ADJ

Severidades según `docs/plans/PROCEDIMIENTO-UAT.md` §8. Origen de cada hallazgo en `registro-ejecuciones.md`.

| # | Paso | Hallazgo | Severidad | Estado |
|---|---|---|---|---|
| 1 (UAT v1) | Bloque 1 | Autoregistro: `201` sin persistir, intermitente, solo desde el navegador en dev; y un `422` en la recuperación de contraseña con URL y token correctos | 🟡 Observación | **No reproducible** (13 envíos: 10 autoregistros de Docente en dev y build, 1 de Estudiante, 2 recuperaciones completas; cada 201 persistió, 0 duplicados, sin `422`). Cerrado sin cambios de código. Si reaparece: capturar en el momento el log del backend y la fila de `usuario` |
| O-1 | Bloque 3 / 4 (login) | El **3.er intento fallido** —el que bloquea la cuenta— sigue mostrando "Email o contraseña incorrectos"; la alerta de bloqueo (temporal o permanente) aparece recién en el **4.º** intento. Es lo que fija el contrato (`US-ADJ-60`: "el siguiente login responde 403"; mismo criterio desde `US-2.2.1`), no una regresión. Consecuencia de UX: el usuario no sabe que su 3.er intento lo bloqueó | ⚪ Observación (UX, conforme a la spec) | Abierto — a decisión de Víctor: dejar como está, o avisar en el 3.er intento (tocaría `src/`: respuesta del login → track formal) |

## Notas y límites de esta conclusión

- El spike se condujo con el **navegador integrado de Claude Desktop** (Chromium), no con el navegador en el que apareció el hallazgo original ni a través del proxy `cognion-frontend-red` desde un dispositivo móvil. "No reproducible" significa eso, no "no puede ocurrir".
- La hipótesis de `StrictMode` + `AbortController` no se sostiene: el código ya crea el controller en el efecto y los 5 intentos en dev funcionaron.
- Hipótesis no verificada sobre el origen: el hallazgo original se observó el 2026-10-02, durante la UAT v1, con una base de desarrollo que más tarde se vació por un incidente de tests (2026-10-03, `US-ADJ-60`); un desfase entre la base consultada y la base real del backend explicaría un "201 sin fila" sin que el código falle. No se puede confirmar.
