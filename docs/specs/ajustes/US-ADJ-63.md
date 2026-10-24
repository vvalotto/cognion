# US-ADJ-63: El hash de contraseñas no bloquea el event loop

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 8 — Despliegue y operación` (hallazgo de la Iteración 6, `US-8.6.3`)
**Tipo**: `fix de rendimiento` backend (refactor del puerto y del adaptador de hashing)
**Agregado principal afectado**: ninguno (puerto de infraestructura de Identidad)
**Bounded Context**: Identidad
**Origen**: prueba manual de despliegue en GCP, paso 13 (`quality/reports/uat/inc8-gcp/bitacora-despliegue.md`).
**Issue**: [#562](https://github.com/vvalotto/cognion/issues/562)
**Interactúa con**: `US-8.6.7` (criterio de 60 logins), `ADR-014` (bcrypt), `ADR-009`/`ADR-018` (un solo proceso, `NullPool`).

---

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.

---

## Descripcion (lenguaje de negocio)

Como **Docente que conduce una sesión en vivo mientras otros usuarios entran a la plataforma**,
quiero que **el inicio de sesión de una persona no congele la aplicación para todos los demás**,
para **que la proyección y las respuestas de los alumnos no se traben cuando alguien inicia sesión, se registra o cambia su contraseña**.

---

## Contexto

### Problema (medido en la VM de GCP)

`BcryptPasswordHasher.hash()` y `verificar()` son **funciones síncronas** (`bcrypt.hashpw`/`bcrypt.checkpw`), y los casos de uso de
Identidad, que son `async`, las llaman directamente. Con un solo proceso de `uvicorn` (decisión de arquitectura: el canal WebSocket vive en
memoria y el `VerificadorDeVencimientos` corre en el mismo proceso), **mientras bcrypt trabaja toda la aplicación espera**: no atiende otros
requests ni mensajes de WebSocket.

Mediciones en la VM `e2-micro` de la prueba (2 vCPU, costo/rondas = 12, el valor por defecto):

| Medición | Resultado |
|---|---|
| `checkpw` en serie | mediana **325 ms** (3,1 por segundo) |
| 24 verificaciones con 2 hilos | 5,6 por segundo, aceleración ×1,82 (bcrypt libera el GIL) |
| Ráfaga de 60 logins con el código actual | se serializa: el último espera ≈ **19,5 s** |
| Mismos 60 con verificación en hilos | ≈ 10,7 s hasta el último, **sin bloquear al resto** |

Además de la espera de cada persona, **cada verificación congela 325 ms** al resto de los usuarios conectados, incluidos los de una sesión en
vivo, aunque ellos no estén iniciando sesión.

### Dónde ocurre (9 puntos de uso en 8 casos de uso)

`iniciar_sesion.py` (`verificar`), `cambiar_password.py` (`verificar` y `hash`), `confirmar_nueva_password.py`, `resetear_password.py`,
`autoregistrar_docente.py`, `autoregistrar_estudiante.py`, `crear_usuario.py` (que usa también el bootstrap del Administrador) y
`registrar_estudiante.py` (todos `hash`). No hay usos fuera de Identidad.

### Opciones de diseño

| | Opción | Lo bueno | Lo malo |
|---|---|---|---|
| A | **Puerto asíncrono**: `PasswordHasherPort.hash`/`verificar` pasan a `async`, y el adaptador corre bcrypt con `asyncio.to_thread` | El caso de uso no sabe nada de hilos (Clean Architecture); los demás puertos ya son asíncronos; es el único cambio de interfaz | Hay que tocar los 9 puntos de uso y los fakes de tests |
| B | Mantener el puerto síncrono y envolver cada llamada con `to_thread` dentro de los casos de uso | Cambia menos firmas | Mete un detalle de infraestructura (hilos) en la capa de casos de uso y se repite 9 veces |
| C | Bajar el costo de bcrypt | Verifica más rápido | Reduce la seguridad (`ADR-014`); no arregla el bloqueo, solo lo acorta |
| D | Varios procesos de `uvicorn` | Reparte la carga | **Rompe** el canal WebSocket en memoria y el verificador de vencimientos; descartada |

**Recomendación: A.** Es la que respeta la arquitectura y se hace una vez. La decisión final se confirma en la Fase 2 de `/implement-us`.

---

## Especificacion del comportamiento

- `PasswordHasherPort.hash` y `verificar` pasan a ser `async def`.
- `BcryptPasswordHasher` ejecuta bcrypt con `asyncio.to_thread`; **mismo algoritmo, mismo costo y mismo formato de hash**.
- Los 8 casos de uso hacen `await` en cada llamada al hasher; sus resultados, errores y efectos (contadores de intentos, bloqueo, eventos) no cambian.
- Los controllers y routers no cambian.
- Los fakes del hasher en `tests/unit/` pasan a `async`.
- **Decisión a tomar en la Fase 2:** usar el ejecutor por defecto de `asyncio` (con 2 vCPU admite 6 hilos) o uno propio acotado a la cantidad de núcleos, para que una ráfaga de bcrypt no deje sin CPU al hilo del event loop.

## Escenarios (BDD)

1. **El event loop sigue respondiendo.** Con una corrutina que registra el paso del tiempo cada 10 ms, mientras se verifican 3 contraseñas de forma
   concurrente con el hasher real, el mayor hueco entre dos pulsos es menor a 120 ms. *(Hoy el mismo escenario da huecos de ~300 ms o más.)*
2. **Lo mismo para `hash()`:** crear un usuario no congela las demás corrutinas.
3. **Comportamiento funcional idéntico:** login correcto e incorrecto, bloqueo a los 3 intentos, cuenta deshabilitada, último Administrador,
   cambio de contraseña y recuperación se comportan igual (la suite existente sigue en verde sin cambiar sus aserciones).
4. **Compatibilidad:** un hash generado antes de este cambio se verifica correctamente después.
5. **Fakes y casos de uso:** ningún caso de uso llama al hasher sin `await` (lo comprueba `mypy` y un test que falla ante una corrutina sin esperar).

## Verificación posterior (no es criterio de aceptación de esta US)

En la VM de GCP, repetir la ráfaga de 60 logins de `US-8.6.7` y registrar el tiempo hasta el último y la latencia de un request ajeno
durante la ráfaga. Referencia previa: 19,5 s hasta el último con el código actual.

## Fuera de alcance

- Cambiar el costo de bcrypt o el algoritmo (`ADR-014`): es un cambio de seguridad y se decide aparte.
- Más de un proceso de `uvicorn` (rompe el estado en memoria).
- Límites de concurrencia o de tasa para logins (*rate limiting*), colas de login.
- Enmascarar los tokens en los logs de acceso (hallazgo distinto del mismo paso 13).

## Notas

- **Track formal obligatorio** (`CLAUDE.md`, clasificación de hallazgos): toca `src/`. Se implementa con `/implement-us`.
- Los CRITICAL de CBO suelen aparecer recién en el pre-push; esta US no agrega dependencias, así que no se espera.
- Puntos de historia estimados: **3**.
