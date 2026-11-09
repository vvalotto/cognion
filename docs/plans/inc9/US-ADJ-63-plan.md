# Plan de Implementación: US-ADJ-63 - El hash de contraseñas no bloquea el event loop

**Patrón:** clean-architecture-bc · **Producto:** cognion · **BC:** Identidad · **Capas:** `entities/ports`, `use_cases`, `frameworks/security`

## Diseño
`bcrypt.hashpw`/`checkpw` son síncronos (325 ms por verificación en la VM de GCP) y los casos de uso `async` los llaman directo: con un solo proceso de `uvicorn`, mientras bcrypt trabaja **no se atiende nada más**, incluidos los WebSockets de una sesión en vivo. La corrección es correr bcrypt en un hilo (bcrypt libera el GIL) detrás de una interfaz asíncrona del puerto.

```
caso de uso (async)                         puerto (entities)                 adaptador (frameworks)
  await self._hasher.verificar_async(...) ─►  PasswordHasherPort               BcryptPasswordHasher
                                               ├─ hash / verificar  (sync)       ├─ hash / verificar        (bcrypt, sin cambios)
                                               └─ hash_async /                   └─ hash_async / verificar_async
                                                  verificar_async (abstractos)        └─ run_in_executor(pool de bcrypt, self.hash …)
```

### Hallazgo de Fase 0 y decisión de diseño (a confirmar)
El puerto lo implementan solo `BcryptPasswordHasher` y `FakePasswordHasher`, pero **144 llamadas en 58 archivos de tests** usan `hash`/`verificar` **de forma síncrona** para sembrar usuarios (`BcryptPasswordHasher().hash("x")`). La spec proponía volver `async` esos mismos métodos; eso obliga a reescribir las 144 llamadas, y una que se olvide de `await` no falla al instante: guarda una corrutina como hash y se rompe después, lejos de la causa.

| | Opción | Lo bueno | Lo malo |
|---|---|---|---|
| **A** | Los métodos `hash`/`verificar` del puerto pasan a `async` (spec) | Una sola interfaz | Reescribir 144 llamadas en 58 archivos de tests; un `await` omitido pasa inadvertido |
| **A2 (propuesta)** | **Agregar** `hash_async`/`verificar_async` al puerto y mantener `hash`/`verificar` | Cero cambios en las 144 llamadas; los casos de uso quedan igual de limpios (no saben de hilos); el cambio es chico y fácil de revisar | El puerto expone dos formas; hay que impedir que los casos de uso usen la síncrona |
| B | Defaults asíncronos con `to_thread` dentro del puerto | No hay que tocar el fake | Mete `asyncio` y la gestión de hilos en `entities/` |

**Propuesta: A2**, con una **guarda automática** (escenario 6): un test recorre el código de los casos de uso y falla si alguno llama a `hash`/`verificar` del hasher en vez de a las formas `*_async`, o si no usa `await`. Así la forma síncrona queda para sembrar datos en tests y herramientas, y no puede volver a colarse en el camino de un request.

### Ejecutor de hilos (decisión de la spec)
Se usa un **ejecutor propio**, `ThreadPoolExecutor(max_workers=os.cpu_count())`, creado una sola vez en el adaptador (con `thread_name_prefix="bcrypt"`), en vez del ejecutor por defecto de `asyncio` (que en 2 vCPU admite 6 hilos). Acota el trabajo de bcrypt a la cantidad de núcleos, para que una ráfaga de logins no le deje sin CPU al hilo del event loop. En la VM de 2 vCPU sale ~5,6 verificaciones por segundo (medido en la spec) y el resto de la aplicación sigue respondiendo.

## Componentes a Implementar

### 1. Puerto (`src/identidad/entities/ports/password_hasher_port.py`)
- [ ] Agregar `async def hash_async(self, password: str) -> str` y `async def verificar_async(self, password: str, password_hash: str) -> bool`, abstractos y documentados. `hash`/`verificar` quedan igual.

### 2. Adaptador (`src/identidad/frameworks/security/password_hasher.py`)
- [ ] Ejecutor propio de bcrypt (módulo-nivel, perezoso) y `hash_async`/`verificar_async` con `loop.run_in_executor(...)` sobre `self.hash`/`self.verificar`. Mismo algoritmo, costo (12) y formato de hash (`ADR-014`).

### 3. Casos de uso (9 puntos en 8 archivos de `src/identidad/use_cases/`)
- [ ] `iniciar_sesion` (`verificar`), `cambiar_password` (`verificar` y `hash`), `crear_usuario`, `resetear_password`, `confirmar_nueva_password`, `autoregistrar_docente`, `autoregistrar_estudiante`, `registrar_estudiante` (`hash`): `await self._hasher.<op>_async(...)`. Resultados, errores y efectos (contadores, bloqueo, eventos) no cambian. Controllers, routers y `frontend/` no cambian.

### 4. Fake de tests (`tests/unit/inc1/_fakes.py`)
- [ ] `FakePasswordHasher` implementa `hash_async`/`verificar_async` (delegan en las síncronas). Los tests de casos de uso siguen igual.

## Tests (Fases 4 a 6)
- **Unitarios (`tests/unit/inc9/`, sin base):**
  - *Event loop libre:* con el **hasher real**, una tarea que anota el tiempo cada 10 ms mientras se verifican 3 contraseñas a la vez (y otra con 3 `hash`); el mayor hueco debe quedar bajo el umbral. **Para no depender del equipo:** umbral de 150 ms (la spec pedía 120) contra los ~250 a 325 ms que bloquea la versión actual, y el test se repite hasta 3 veces antes de fallar.
  - *Compatibilidad:* un hash bcrypt generado con `bcrypt.hashpw` directo (independiente del adaptador) verifica con `verificar_async`; el hash nuevo tiene el formato `$2b$12$` y verifica contra su contraseña; una contraseña distinta se rechaza.
  - *Guarda:* recorrido AST de `src/*/use_cases/` que prohíbe llamar `hash`/`verificar` a un hasher y exige `await` en `*_async`.
  - *Fake y puerto:* `hash_async`/`verificar_async` son abstractos (no se puede instanciar un hasher sin ellos).
- **Regresión:** `tests/unit/inc1/test_password_hasher.py` y todos los tests de casos de uso de Identidad (login, bloqueo, cambio, reseteo, recuperación, registro, autoregistro, bootstrap) **sin cambiar sus aserciones**.
- **Integración / BDD (base descartable inline):** el login y la recuperación contra la API real siguen en verde (se corre el subconjunto de Identidad); BDD de los 6 escenarios, 5 sin base.
- **Que los tests detectan el error:** correr los escenarios de tiempo con los casos de uso llamando a la forma síncrona y ver que fallan.

## Documentación (Fase 8)
- `ADR-014`: nota breve (bcrypt corre en un ejecutor propio; mismo costo y algoritmo).
- `docs/specs/ajustes/US-ADJ-63.md`: estado → `Implementada`, y registrar la decisión A2 y el ejecutor propio.

## Verificación posterior (fuera de esta US)
En la VM de GCP, repetir la ráfaga de 60 logins (`US-8.6.7`, #551) y medir el tiempo hasta el último y la latencia de un request ajeno durante la ráfaga (referencia: 19,5 s). La VM está pausada.

## Riesgos
- **Un caso de uso futuro llama la forma síncrona:** lo frena la guarda automática.
- **Prueba de tiempo intermitente en un CI cargado:** margen de 150 ms vs 250 a 325 ms, hasta 3 intentos. Si aun así molesta, se baja el costo de bcrypt **solo en la prueba** (parámetro del adaptador), sin tocar el valor de producción.
- **Cierre del ejecutor al apagar:** los hilos de `ThreadPoolExecutor` se unen al salir del intérprete; no hay trabajo en curso que perder (un login interrumpido se reintenta).
