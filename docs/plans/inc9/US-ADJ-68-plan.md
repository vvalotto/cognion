# Plan de Implementación: US-ADJ-68 - El log de acceso no muestra el token de las invitaciones

**Patrón:** clean-architecture-bc · **Producto:** cognion · **BC:** transversal (`shared`) · **Capa:** `frameworks`

## Diseño
El token de una invitación viaja en la ruta de `GET /identidad/invitaciones/{token}` (`registro_router.py`; en producción, bajo `/api`). `uvicorn` escribe esa ruta completa en el log de acceso. `US-ADJ-64` ya enmascara `token=<valor>` y `/recuperar-password/<token>`; falta `/invitaciones/<token>`. El cambio es solo del filtro de logging: ni la API, ni el dominio, ni `frontend/` se tocan.

```
uvicorn escribe  GET /api/identidad/invitaciones/<43 caracteres> HTTP/1.1" 404
        │
        ▼
FiltroTokens.filter(record)            (ya instalado en uvicorn.access y uvicorn.error)
   └─ _sanear(msg) y _sanear(args)  ──►  enmascarar_tokens(texto)
          ├─ _TOKEN_EN_QUERY     token=<valor>                      → token=***   (ya existe)
          ├─ _TOKEN_EN_RUTA      /recuperar-password/<token>        → /…/***      (ya existe)
          └─ _TOKEN_INVITACION   /invitaciones/<token ≥ 20 chars>   → /invitaciones/***   ← nuevo
```

- **Criterio de token:** segmento de 20 o más caracteres de `[A-Za-z0-9_-]` justo después de `/invitaciones/`, igual que `/recuperar-password/`. Los tokens reales tienen 43 (`secrets.token_urlsafe(32)`).
- **Sin falsos positivos relevantes:** `POST /comisiones/<uuid>/invitaciones` no tiene nada después de `/invitaciones` y queda intacto; un segmento de menos de 20 caracteres tampoco se toca.
- **Una consecuencia a tener presente para `US-ADJ-67` (#590):** si se agrega una ruta `/invitaciones/<uuid>` (por ejemplo, revocar un link grupal por su id), el UUID de 36 caracteres también quedaría enmascarado. Es inocuo, pero esa US puede decidir distinguirlo.

## Componentes a Implementar

### 1. Filtro de logging (`src/shared/frameworks/logging_config.py`)
- [ ] `_TOKEN_INVITACION = re.compile(r"(/invitaciones/)[A-Za-z0-9_\-]{20,}")`, junto a las otras dos.
- [ ] `enmascarar_tokens` aplica las tres sustituciones.
- [ ] Actualizar el docstring del módulo y el de `enmascarar_tokens` (hoy mencionan el token de la invitación solo en la query).

### 2. Sin cambios
- Dominio, casos de uso, `registro_router.py`, `settings`, `frontend/`, `dependencies.py`.

## Tests (Fases 4 a 6)
- **Unitarios (`tests/unit/inc9/test_us_adj_68_token_invitacion_log.py`, sin base):** `enmascarar_tokens` con la ruta de la API (con y sin prefijo `/api`), token de 43 caracteres, `POST /comisiones/<uuid>/invitaciones` intacto, segmento corto intacto, convivencia con `token=` y `/recuperar-password/<token>` en la misma línea, varias ocurrencias en un texto; `FiltroTokens` sanea los argumentos `%s` como los pasa `uvicorn` y no descarta el registro.
- **Integración (`tests/integration/inc9/test_us_adj_68_log_invitaciones_integration.py`, base descartable):** un `uvicorn` real (`ServidorReal`); se consulta una invitación vigente creada por la API y un token inexistente, y se lee la salida real del proceso: aparece `/invitaciones/***`, no el token, y la línea conserva `GET` y el estado. Se verifica también que generar una invitación y `/registro?token=` se registran como siempre.
- **BDD (`tests/step_defs/inc9/test_us_adj_68_steps.py`):** los 6 escenarios aprobados; los del servidor real con base descartable.
- **Que los tests detectan el error:** correrlos con el filtro anterior y ver que los escenarios 1, 2 y 3 fallan.

## Documentación (Fase 8)
- Docstring de `logging_config.py` (en la implementación).
- `docs/specs/ajustes/US-ADJ-68.md`: estado → `Implementada`.
- Nota breve en `CLAUDE.md`: no hace falta, el detalle vive en la spec y el reporte.

## Riesgos
- **Los logs ya escritos** (en la VM de GCP, tras la prueba del 2026-11-06) conservan tokens: esta US no los reescribe. Las invitaciones de esa prueba ya están usadas o son de una base de prueba para desechar.
- **Un token que aparezca en otro formato** (por ejemplo, en el cuerpo de una respuesta) no está cubierto: el log de acceso de `uvicorn` no registra cuerpos, así que hoy no ocurre.
