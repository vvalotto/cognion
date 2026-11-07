# ADR-014 — bcrypt para hashing de contraseñas (vs. argon2id)

**Estado:** Aceptado
**Fecha:** 2026-07-16

---

## Contexto

RF-01 requiere que el estudiante fije una contraseña al registrarse por invitación, y RF-02
requiere autenticación de los tres roles. Ningún ADR previo definía el algoritmo de hashing de
contraseñas — ADR-007 cubre JWT + RBAC pero no el almacenamiento de credenciales.

## Opciones Consideradas

- **argon2id** — descartada: ganador del Password Hashing Competition y más resistente a
  ataques con GPU/ASIC, pero es una librería menos establecida en el ecosistema Python/FastAPI
  del proyecto y no aporta beneficio justificado frente al escenario de Seguridad de
  `RNF_v1.md` (RBAC estándar, sin mecanismos adicionales de ocultamiento).
- **bcrypt** — elegida.

## Decisión

Las contraseñas se almacenan hasheadas con bcrypt.

## Justificación

bcrypt es el estándar de facto en el ecosistema Python/FastAPI, con soporte maduro y
ampliamente auditado. Es suficiente para el escenario de Seguridad de `RNF_v1.md`, que no
exige mecanismos avanzados, y evita introducir una dependencia menos probada sin necesidad.

## Impacto en Configuración

- `pyproject.toml` — dependencia `bcrypt` (o `passlib[bcrypt]`).
- `src/identidad/interface_adapters/` — hashing/verificación de contraseña en registro y login.

## Consecuencias

- ✅ Librería madura y ampliamente auditada, con buen soporte en el ecosistema FastAPI.
- ⚠️ Costo computacional fijo por versión de bcrypt (a diferencia de argon2, no permite tunear
  el costo en memoria) — aceptable para la escala de 30–60 usuarios por comisión.

## Ejecución sin bloquear el event loop (`US-ADJ-63`, 2026-11-07)

- bcrypt (costo 12) tarda 325 ms por verificación en la VM `e2-micro` de GCP y es síncrono: ejecutado en el hilo
  del event loop congelaba toda la aplicación, incluidos los WebSockets de una sesión en vivo, porque `uvicorn`
  corre en un solo proceso (el canal en vivo vive en memoria).
- `PasswordHasherPort` suma `hash_async`/`verificar_async`, que son las que usan los casos de uso. El adaptador
  `BcryptPasswordHasher` las ejecuta en un `ThreadPoolExecutor` propio de `os.cpu_count()` hilos (bcrypt libera el
  GIL). `hash`/`verificar` siguen existiendo, sin cambios, para sembrar datos en tests y herramientas fuera del
  event loop; un test (`tests/unit/inc9/`) impide que un caso de uso vuelva a llamarlas.
- **Sin cambios de seguridad:** mismo algoritmo, costo (12) y formato de hash; los hashes ya guardados siguen
  verificando. Subir el costo o cambiar de algoritmo es otra decisión.
