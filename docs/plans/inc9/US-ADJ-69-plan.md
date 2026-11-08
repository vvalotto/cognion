# Plan de Implementación: US-ADJ-69 - El login avisa "te queda 1 intento" tras el 2.º fallo

**Patrón:** clean-architecture-bc · **Producto:** cognion · **BC:** Identidad · **Capas:** `entities`, `use_cases`, `frameworks` (router) y `frontend/`

## Diseño
`IniciarSesionUseCase` ya incrementa `usuario.intentos_fallidos_login` y arma `CredencialesInvalidas`. Cuando el contador queda en `_INTENTOS_MAXIMOS - 1` (el 2.º fallo) marca en la excepción `intentos_restantes = 1`. El router lo traduce a un `detail` estructurado, igual que `perfil_router.py` con el cambio de contraseña; el frontend lo lee y lo muestra.

```
POST /identidad/login (contraseña incorrecta)
        │
        ▼
IniciarSesionUseCase                  intentos_fallidos_login += 1
   ├─ 1.er fallo      → CredencialesInvalidas()                            intentos_restantes = None
   ├─ 2.º fallo       → CredencialesInvalidas(); .intentos_restantes = 1   ← nuevo
   └─ 3.er fallo      → bloquea la cuenta (sin cambios)                    intentos_restantes = None
        │
        ▼
auth_router.login                      401
   ├─ sin aviso → detail = "Email o contraseña inválidos."          (como hoy)
   └─ con aviso → detail = {"mensaje": ..., "intentos_restantes": 1}  ← nuevo
        │
        ▼
Login.tsx (apiFetch extrae message y detail) → LoginError(intentosRestantes=1)
        └─ "Te queda 1 intento antes del bloqueo de la cuenta." + link a /recuperar-password
```

- **Email inexistente:** el caso de uso lanza `CredencialesInvalidas` antes de tocar contadores, así que nunca lleva el aviso.
- **Sin cambios de status:** el 3.er fallo sigue `401` y el siguiente `403`.
- **Compatibilidad:** sin aviso, el `detail` sigue siendo texto: los clientes y tests que lo leen no se rompen.

## Componentes a Implementar

### 1. Entidad (`src/identidad/entities/errors.py`)
- [ ] `CredencialesInvalidas.intentos_restantes: int | None = None`, junto a `evento_cuenta_bloqueada`.
- [ ] Docstring: ya no es cierto que no filtre la existencia de la cuenta; documentar el trade-off aceptado (2026-11-08).

### 2. Caso de uso (`src/identidad/use_cases/iniciar_sesion.py`)
- [ ] Tras incrementar el contador: si llegó al máximo, bloquea (igual que hoy); si no, y el contador es `_INTENTOS_MAXIMOS - 1`, `exc.intentos_restantes = 1`.
- [ ] Docstring de `ejecutar` con el nuevo comportamiento.

### 3. Router (`src/identidad/frameworks/api/auth_router.py`)
- [ ] En `except CredencialesInvalidas`: `detail` objeto `{"mensaje": str(exc), "intentos_restantes": ...}` solo si hay aviso; texto en los demás casos.
- [ ] Docstring del endpoint.

### 4. Frontend
- [ ] `frontend/src/pages/identidad/LoginError.tsx`: prop opcional `intentosRestantes`; con valor 1 agrega "Te queda 1 intento antes del bloqueo de la cuenta." y el link "recuperala por email" a `/recuperar-password`.
- [ ] `frontend/src/pages/identidad/Login.tsx`: lee `err.detail.intentos_restantes` (función auxiliar como `segundosDeBloqueoTemporal`) y se lo pasa a `LoginError`; se limpia al reintentar.

### 5. Sin cambios
- `Usuario`, `bloqueo_cuenta.py`, repositorios, `dependencies.py`, migraciones, el cambio de contraseña.

## Tests (Fases 4 a 6)
- **Unitarios backend (`tests/unit/inc9/test_us_adj_69_aviso_ultimo_intento.py`, sin base):** el caso de uso con repositorio falso, secuencia de fallos (1.º sin aviso, 2.º con `intentos_restantes = 1`, 3.º bloquea sin aviso), email inexistente sin aviso, un éxito reinicia, último Administrador avisa en el 2.º; `CredencialesInvalidas().intentos_restantes is None`.
- **Integración (`tests/integration/inc9/test_us_adj_69_login_aviso_integration.py`, base descartable):** `POST /identidad/login` contra la base: el cuerpo del `401` de cada fallo, el `403` del 4.º intento y el texto intacto sin aviso.
- **BDD (`tests/step_defs/inc9/test_us_adj_69_steps.py`):** los 6 escenarios aprobados, por HTTP con base descartable (patrón de `US-2.2.1`).
- **Frontend (Vitest):** `LoginError` con y sin aviso (texto y link), `Login` con un `401` que trae el aviso y con uno que no.
- **Que los tests detectan el error:** correrlos con el código anterior y ver que fallan los escenarios 2 y 6 y los de frontend.

## Documentación (Fase 8)
- Specs de `US-2.2.1` y `US-ADJ-60`: nota de que el contrato cambia en el 2.º fallo.
- `docs/design/domain/BC-identidad-modelo.md` (`INV-ID-10`): el aviso y el trade-off.
- Docstring de `CredencialesInvalidas` (en la implementación).
