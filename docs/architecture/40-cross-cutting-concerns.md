# 40 Preocupaciones transversales

> Vista contrastada con el código de la versión `1.0.0` (Incremento 10.1, Fase 4). Plantilla: `_plantilla-vista.md`.

## Propósito
Reunir lo que atraviesa a todos los Bounded Contexts: seguridad, configuración, logging, salud, errores, persistencia y accesibilidad. Cada tema dice dónde vive y qué debe respetar quien toque el código.

## Interesados
**Mantenedor** (qué reglas comunes no romper), **instalador** (configuración, salud y registros) y **materia** (decisiones transversales en un monolito modular).

## Para leer esta vista
La mayoría de lo transversal vive en `src/shared/` (el único módulo que los BC pueden compartir; no importa de ningún BC, lo verifica `import-linter`) y en `src/settings.py`. Cada BC arma su cableado en su `frameworks/dependencies.py`.

## Alcance
Preocupaciones comunes de la aplicación. No incluye el despliegue (`60-deployment-view.md`) ni el flujo de desarrollo (`50-development-view.md`).

## Fuentes
`src/shared/`, `src/settings.py`, `src/app.py`, `ADR-007`, `009`, `010`, `011`, `013`, `014`, `017`, `018`, `019`, `docs/rf/RNF_v1.md`.

## Mapa de `shared/`

| Elemento | Qué hace | Dónde |
|---|---|---|
| JWT | Emisión y verificación (`PyJWT`, `HS256`) | `shared/entities/jwt.py`, `shared/frameworks/security/jwt_pyjwt.py` |
| Roles | `TipoPerfil` y el chequeo por rol | `shared/entities/tipo_perfil.py`, `shared/interface_adapters/security/` |
| Base de datos | `Base` declarativa, engine y sesión async | `shared/frameworks/db.py` |
| SMTP | Envío de correo con cuenta global o por materia | `shared/frameworks/smtp.py` |
| Logging | Formato, nivel y enmascarado de tokens | `shared/frameworks/logging_config.py` |
| Salud | Comprobación de la base | `shared/frameworks/salud.py` |
| Versión | Lee el archivo `VERSION` | `shared/frameworks/version.py` |

## 1. Seguridad

**Autenticación.** Identidad emite un JWT (`HS256`, 60 minutos por defecto, **sin refresh**, `ADR-013`). El cliente lo manda en `Authorization: Bearer`. `get_current_user` responde `401` si falta o no es válido. El canal WebSocket lo recibe en `?token=` porque el navegador no permite fijar cabeceras en el handshake.

**Autorización (RBAC).** `require_rol([...])` compone sobre `get_current_user` y responde `403` si el rol no está permitido. Tres roles: administrador, docente y estudiante (`ADR-007`, `ADR-019`). Hay combinaciones listas para usar: `require_administrador`, `require_docente`, `require_estudiante` y `require_docente_o_administrador`. Además de la regla de rol, los casos de uso del docente verifican que esté **asignado a la comisión o a la materia** (`ComisionNoAutorizada`, `MateriaNoAutorizada`).

**Contraseñas.** Hash `bcrypt` (`ADR-014`) en un ejecutor propio, para no bloquear el event loop. Política: mínimo 12 caracteres con mayúscula, número y símbolo (`INV-ID-11`, validada en el dominio, no en la base).

**Contra adivinar contraseñas.** Bloqueo al 3.er fallo consecutivo y aviso "te queda 1 intento" tras el 2.º. Un login con email inexistente devuelve el mismo `401` que una contraseña incorrecta. La recuperación de contraseña nunca revela si el email existe.

**Secretos.** `SECRET_KEY` de al menos 32 caracteres y distinta del valor de ejemplo en los entornos `local`, `staging` y `produccion`; la aplicación no arranca si no. Los mensajes de error de configuración no incluyen el valor.

**CORS.** Se lista explícitamente en `CORS_ALLOWED_ORIGINS`; `*` está rechazado porque la API usa credenciales.

**En el navegador.** La sesión (`token` y `rol`) se guarda en `localStorage` bajo `cognion.session` (`frontend/src/lib/session.ts`). Queda expuesta a cualquier script que corra en la página; se acepta para esta escala y no hay refresh token.

## 2. Configuración y entornos

Toda la configuración sale de variables de entorno (`.env`) leídas por `src/settings.py` (Pydantic). Las principales:

| Variable | Valor por defecto | Para qué |
|---|---|---|
| `ENTORNO` | `desarrollo` | `desarrollo`, `local`, `staging` o `produccion`; decide cuánto valida el arranque |
| `DATABASE_URL`, `SECRET_KEY` | sin valor | Obligatorias |
| `EMAIL_MODO` | `smtp` | `consola` deja el contenido de los correos (con sus links) en el log |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | `localhost`, `25` | Cuenta de correo global |
| `SMTP_CUENTAS_POR_MATERIA` | vacío | Cuenta propia por materia (`ADR-023`) |
| `LOG_LEVEL`, `LOG_FORMAT` | `INFO`, `texto` | `json` para un registro estructurado |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Duración del token |
| `ADMINISTRADOR_BLOQUEO_TEMPORAL_MINUTOS` | `15` | Bloqueo del último administrador |
| `VERIFICADOR_VENCIMIENTOS_CADENCIA_SEGUNDOS`, `…_UMBRAL_INACTIVIDAD_MINUTOS` | `120`, `15` | Tarea de vencimientos |
| `CORS_ALLOWED_ORIGINS`, `FRONTEND_URL` | `http://localhost:5173` | Orígenes y base de los links de los correos |

**Entornos.** `desarrollo` no valida nada extra. `local` (instalación en una máquina propia) valida solo el secreto. `staging` y `produccion` rechazan además SMTP local, el remitente de ejemplo, orígenes CORS de `localhost` y `EMAIL_MODO=consola`, y listan **todas** las violaciones juntas.

## 3. Logging

- Formato `texto` (por defecto) o `json` (`LOG_FORMAT`); nivel `LOG_LEVEL`. Los registros de la aplicación (`src.*`) llegan a la salida estándar, junto con los de `uvicorn`.
- **Enmascarado de credenciales** (`US-ADJ-64`, `US-ADJ-68`): el log de acceso reemplaza por `***` el `token=` de una query (JWT del canal, invitación de `/registro`), el token de `/recuperar-password/<token>` y el de `/invitaciones/<token>`. También se enmascara en los tracebacks.
- Con `EMAIL_MODO=consola` los links de recuperación de contraseña quedan en el log; por eso no se permite en `staging` ni `produccion`.
- Los envíos de correo fallidos se registran con nivel `warning`, sin interrumpir la operación.

## 4. Salud y operación

| Ruta | Qué dice |
|---|---|
| `GET /api/health` | El proceso está vivo; devuelve `{"status": "ok", "version": "…"}` |
| `GET /api/health/ready` | Además comprueba la base (`SELECT 1`, tope de 2 segundos); `503` sin detalles ni credenciales si falla |

La imagen Docker usa `/api/health` como `healthcheck`. Con `ADR-010` como decisión base y `US-8.3.3` como ampliación.

## 5. Errores

- `401` credenciales ausentes o inválidas; `403` rol insuficiente o no asignado a la comisión o materia; `404` no existe; `409` conflicto (por ejemplo, email repetido); `422` datos inválidos.
- Los errores con motivo de negocio llevan `detail.codigo` (por ejemplo `invitacion_revocada`, `password_invalida`, `cuenta_bloqueada_temporal`) para que el frontend muestre un mensaje preciso.
- Los errores de dominio son excepciones de `entities/errors.py` de cada BC; el router las traduce a HTTP.

## 6. Persistencia

- Una sola base PostgreSQL, un solo `Base` y un solo engine con `NullPool` (`ADR-017`, `ADR-018`); cada operación abre su conexión, por eso `max_connections=100`.
- Las migraciones son de Alembic (`migrations/versions/`, 19 en esta versión) y se aplican antes de arrancar; `alembic downgrade base` funciona.
- Las operaciones que tocan varias tablas se confirman en una sola transacción (`ADR-009`); en Actividad Evaluativa, el evento y los read models van juntos.
- Fechas y horas se guardan con zona horaria (`DateTime(timezone=True)`, UTC) y el frontend las convierte a la hora local.

## 7. Interfaz y accesibilidad

shadcn/ui sobre Tailwind (copiado al proyecto, no como dependencia opaca), nivel WCAG A como mínimo (`ADR-011`). La proyección en el aula exige un criterio de legibilidad propio (tamaño y contraste) que se resolvió en el diseño de UX (`docs/design/ux/`).

## 8. Versión

`VERSION` es la única fuente. Debe coincidir con `pyproject.toml`, `frontend/package.json` y `uv.lock`; `/api/health` la informa y el CD no publica un tag que no coincida.

## Decisiones reflejadas
`ADR-007`, `009`, `010`, `011`, `013`, `014`, `017`, `018`, `019`, `023`.

## Restricciones y calidad
- **Seguridad:** `RNF_v1.md`, escenario de control de acceso por rol.
- **Disponibilidad:** salud y readiness permiten al operador y al proxy detectar una aplicación caída o sin base.
- **Diagnóstico:** el escenario de diagnóstico post-incidente se apoya en logs estructurados con credenciales enmascaradas.

## Cómo verificar esta vista contra el código
- Configuración: `src/settings.py` (campos y validaciones por entorno).
- Seguridad: `src/shared/interface_adapters/security/` y las constantes `require_*` de `src/identidad/frameworks/dependencies.py`.
- Logging: `src/shared/frameworks/logging_config.py`.
- Salud: `src/app.py` (`/health`, `/health/ready`) y `src/shared/frameworks/salud.py`.

## Cuándo hay que actualizarla
Una variable de configuración, rol o regla de seguridad nueva; un cambio de formato de log o de las rutas de salud; o una decisión nueva que toque a varios BC.

## Sin verificar
- ⚠ El token en `localStorage` no se evaluó contra un modelo de amenazas; es una decisión de simplicidad, no una verificación.
- ⚠ No hay informe de accesibilidad: WCAG A es el objetivo declarado en `ADR-011`, no un resultado medido.
- ⚠ Los códigos `detail.codigo` listados son ejemplos verificados, no el catálogo completo.
