# US-ADJ-68: El log de acceso no muestra el token de las invitaciones

**Estado**: `Implementada`
**Iteracion / Sprint**: `Incremento 9 — Correcciones y robustez`, Iteración 1
**Tipo**: `mejora de seguridad` backend (logging transversal)
**Agregado principal afectado**: ninguno
**Bounded Context**: transversal (`shared`), lo consume la API de Identidad
**Origen**: revisión del log de la VM de GCP tras la prueba real con estudiantes (2026-11-07).
**Issue**: [#594](https://github.com/vvalotto/cognion/issues/594)
**Interactúa con**: `US-ADJ-64` (enmascarado de tokens en el log), `#590` / `US-ADJ-67` (link de invitación grupal), `ADR-012`.

---

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.

---

## Descripcion (lenguaje de negocio)

Como **responsable de operar Cognión**,
quiero que **el registro de accesos no guarde el código secreto de las invitaciones**,
para **que nadie que lea el log pueda usar una invitación que todavía no se usó para registrarse en una comisión**.

---

## Contexto

La pantalla de registro consulta la invitación con `GET /api/identidad/invitaciones/{token}` (`registro_router.py`,
`Registro.tsx` línea 61). El token viaja **en la ruta**, y `uvicorn` escribe la ruta completa en el log de acceso. En la
VM de GCP se contaron **21 líneas** con un token completo tras la prueba real del 2026-11-06.

`US-ADJ-64` ya enmascara dos formas: `token=<valor>` en una query string (JWT del WebSocket, `/registro?token=`) y
`/recuperar-password/<token>` en la ruta del SPA. **No cubre `/invitaciones/<token>`**. Una invitación sin usar es válida
hasta 7 días (`ADR-012`), así que el log contiene credenciales vigentes. Con el link grupal de #590, que será reutilizable,
la exposición sería peor: por eso esta corrección va **antes**.

## Especificacion del comportamiento

- Toda ocurrencia de `/invitaciones/<token>` en el log de acceso, y en cualquier mensaje o argumento de log que pase por el
  filtro, se escribe como `/invitaciones/***`.
- Un token es un segmento de 20 o más caracteres de `[A-Za-z0-9_-]` justo después de `/invitaciones/` (los tokens reales
  tienen 43). Mismo criterio que `/recuperar-password/<token>`.
- El resto de la línea queda igual: método, resto de la ruta, versión HTTP y código de estado.
- No se enmascara lo que no es un token: `POST /api/comisiones/<uuid>/invitaciones` (sin segmento posterior) queda intacto.
- `token=<valor>` y `/recuperar-password/<token>` siguen enmascarados como antes.
- Sin cambios en la API ni en `frontend/`.

## Escenarios (BDD)

1. **Preview de invitación.** Con un `uvicorn` real, `GET /api/identidad/invitaciones/<token de 43 caracteres>` deja en el
   log `/api/identidad/invitaciones/***` y el código de estado.
2. **Token en la ruta con otro estado.** Si la invitación está usada o vencida (`422`) o no existe (`404`), el log también
   la muestra enmascarada.
3. **No se pierde información útil.** La línea conserva método, ruta sin el token y estado.
4. **Generar una invitación no se altera.** `POST /api/comisiones/<uuid>/invitaciones` aparece igual que antes.
5. **Lo anterior sigue funcionando.** `token=<JWT>` y `/recuperar-password/<token>` siguen enmascarados.
6. **Token corto.** Un segmento de menos de 20 caracteres tras `/invitaciones/` no se toca (no es un token real).

## Fuera de alcance

Rotar o invalidar las invitaciones que ya hayan quedado en logs anteriores; enmascarar otros datos personales del log
(emails en el cuerpo); cambiar la forma en que el frontend envía el token.

## Notas para `/implement-us`

- Es una extensión de `src/shared/frameworks/logging_config.py`: una tercera expresión regular junto a `_TOKEN_EN_QUERY` y
  `_TOKEN_EN_RUTA`, aplicada en `enmascarar_tokens`. Actualizar el docstring del módulo.
- **Probar con el proceso real**, no solo con `caplog` (`US-ADJ-64`: `caplog` dejó pasar el error original). Reusar
  `tests/integration/inc8/_servidor_real.py` y `_escenarios_logging.py`.
- Tests unitarios de `enmascarar_tokens` con los 6 casos y verificación de que `FiltroTokens` sanea también los
  argumentos (`%s`) que `uvicorn` pasa al formatear.
- Es el requisito previo de `US-ADJ-67` (#590): cerrarla antes de empezar esa.
