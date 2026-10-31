# US-8.1.5: Bootstrap del primer Administrador

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-8.1`
**Tipo**: `infra backend` (comando operativo — sin endpoint)
**Bounded Context**: Identidad
**Issue**: #518

---

## Descripcion (lenguaje de negocio)

Como **responsable de operar el sistema**,
quiero **crear el primer Administrador de una instalación limpia con un único comando, sin dejar ninguna contraseña en el repositorio**,
para **poder entrar al sistema recién desplegado y dar de alta al resto desde el producto**.

---

## Contexto

`ADR-016` decidió un script standalone para el primer Administrador (no un endpoint público ni un seed en migración).
Existe `scripts/seed_admin.py` desde `US-1.1.0`, pero para un despliegue real tiene huecos:

1. **No está en la imagen**: el `Dockerfile` no copia `scripts/`, así que no se puede ejecutar en Fly.io.
2. La contraseña solo se acepta por variable de entorno (queda en el historial del shell y en la lista de procesos).
3. Variables faltantes o contraseña que no cumple `INV-ID-11` terminan en un traceback, no en un mensaje claro.
4. Su idempotencia es solo por email: con otro email crearía un segundo Administrador.

## Especificacion del comportamiento

- Lógica en `src/identidad/` (va en la imagen): `BootstrapAdministradorUseCase` reutiliza `CrearUsuarioUseCase`
  (sin duplicar reglas) y **no hace nada si ya existe un Administrador operativo** (`AdministradorYaExiste`).
- Comando: `uv run python -m src.identidad.frameworks.cli.bootstrap_administrador`
  (en Fly: `fly ssh console -C "..."`). `scripts/seed_admin.py` queda como envoltorio del mismo comando.
- Entrada: `ADMIN_NOMBRE` y `ADMIN_EMAIL` por entorno. La contraseña, por `ADMIN_PASSWORD` si está definida; si no,
  **se pide por terminal sin eco** (`getpass`). Nunca como argumento de línea de comandos.
- Códigos de salida: `0` creado o ya existía un Administrador operativo (idempotente); `1` entrada inválida
  (faltan variables, contraseña que no cumple `INV-ID-11`, email ya usado por otra cuenta); `2` sin terminal ni
  `ADMIN_PASSWORD`.
- La contraseña nunca se imprime ni se escribe en logs; los mensajes de error nombran qué falta, no el valor.

## Escenarios (BDD)

1. Base sin Administrador, datos válidos → crea el Administrador, exit 0.
2. Segunda ejecución (incluso con otro email) → no crea nada, informa que ya existe, exit 0.
3. Falta `ADMIN_EMAIL` → mensaje que nombra la variable, exit 1.
4. Contraseña de 8 caracteres → mensaje de `INV-ID-11` sin repetir la contraseña, exit 1.
5. Sin `ADMIN_PASSWORD` y sin terminal → exit 2 con instrucción.
6. Sin `ADMIN_PASSWORD` y con terminal → la pide sin eco.
7. Contra una base real (vacía→head): crea, y el segundo intento no duplica (`verificar_migraciones.sh`).

## Fuera de alcance

Recuperación si todos los Administradores quedaron inoperables; rotación de contraseña (ya existe en el producto).

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.
