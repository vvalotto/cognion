# ADR-028 — Unidad de trabajo por request para Identidad y Banco; el event store conserva su commit

**Estado:** Aceptado
**Fecha:** 2026-11-25
**Origen:** Issue [#667](https://github.com/vvalotto/cognion/issues/667), hallazgos `IM-03` y `DM-04` de la revisión de diseño (`docs/revision-diseno-2026-11/`); decidido con Víctor en la Iteración 2 del Incremento 12. Relacionado con `ADR-017` (sesión de base compartida), `ADR-018` (`NullPool`) y `ADR-002` (event sourcing). Lo implementa `US-12.2.1` (Issue [#668](https://github.com/vvalotto/cognion/issues/668)).

---

## Contexto

Hoy cada repositorio hace `commit()` dentro de su propio método: son 21 en 8 archivos (20 en los repositorios de Identidad y Banco y 1 en `SQLAlchemyEventStore.append`). Ningún caso de uso controla la transacción, así que un caso de uso que escribe dos veces confirma dos veces.

Se reprodujo contra la base real (`cognion_test`), forzando un fallo en la segunda escritura:

| Caso de uso | Qué queda si falla la segunda escritura |
|---|---|
| `crear_materia` (guarda materia y después banco) | Una **materia sin banco**: viola `INV-BP-01` |
| `confirmar_nueva_password` (usuario y después token) | La contraseña cambia y el **token queda sin marcar como usado: el mismo token se aceptó una segunda vez** |
| `registrar_estudiante` (usuario y después invitación) | El estudiante queda creado y la invitación sin consumir (leído, no ejecutado) |
| `eliminar_cuenta`, `solicitar_recuperacion_password` | Sin daño, reintentable (leído) |

Son 5 los casos de uso con dos escrituras seguidas (el informe decía 8: cuatro de los que contaba tienen sus dos escrituras en ramas excluyentes). Ningún caso de uso hace dos `append` seguidos: cada operación de Actividad Evaluativa escribe un solo stream, así que el riesgo que describe `DM-04` ("escribir en dos streams de forma atómica") hoy es hipotético.

Del total, 47 de los 82 casos de uso escriben (Actividad Evaluativa 18, Banco 8, Identidad 21).

Dos hechos verificados condicionan la solución:

1. **Un fallo después del `yield` de una dependencia de FastAPI llega tarde.** Con FastAPI 0.139, si el `commit()` de una dependencia con `yield` falla en el código posterior al `yield`, **el cliente ya recibió un 200** (la respuesta se envía antes). Solo con `scope="function"` el fallo se produce antes de enviar y el cliente ve el error (500). Se comprobó también en cadena con las fábricas de controllers que dependen de `SessionDep`.
2. **La sesión en vivo publica en el canal justo después de persistir** (`cerrar_pregunta_actual`: "publica recién después de persistir"). Con un único commit al final del request, los alumnos recibirían "pregunta cerrada" antes del commit y podrían leer el estado viejo.

## Opciones Consideradas

| Opción | Qué es | Costo y riesgo |
|---|---|---|
| **A. Por request, completa** | `get_session` confirma o revierte; repositorios y event store solo hacen `flush` | Cambio chico en código, pero exige `scope="function"` y diferir la publicación al canal hasta después del commit. Toca la persistencia de la sesión en vivo, lo más delicado |
| **A'. Por request, acotada** | Lo mismo para Identidad y Banco; el event store conserva su commit como excepción documentada | Chico. Bajo riesgo: no toca la ruta de tiempo real |
| **B. Explícita en el caso de uso** | Un puerto `UnitOfWork` que cada caso de uso llama | Alto: 47 casos de uso y sus tests. Un commit olvidado descarta todo en silencio |
| **C. Parche de los 5 casos** | Un método de repositorio compuesto por caso | El menor, pero deja los 21 `commit()`, no resuelve `DM-04` y obliga a cambiar el criterio de salida de la iteración |

## Decisión

**La transacción de un request de Identidad, Banco, Notificaciones y Analytics la maneja una unidad de trabajo por request, en la dependencia que entrega la sesión (`scope="function"`): los repositorios hacen `flush()`, la dependencia confirma al terminar bien y revierte ante una excepción. El event store de Actividad Evaluativa conserva su `commit()` como única excepción: un evento (o un lote del mismo stream) es una transacción.**

## Justificación

- **Resuelve lo reproducido.** Los 5 casos con dos escrituras comparten una sesión y pasan a confirmarse o revertirse enteros, sin tocar ninguno de los 47 casos de uso (los repositorios dejan de confirmar, los casos de uso no cambian).
- **Mantiene la sesión en vivo como está.** Su evento y sus proyecciones ya se confirman juntos en `append` (`US-6.2.3`) y el canal publica después; no hay ningún defecto demostrado ahí, y es la ruta con más pruebas de tiempo real (Playwright y 2544 tests la protegen, pero un cambio de semántica de commit es el que más puede romperla). Hacer la opción A completa exigiría un mecanismo nuevo (publicación diferida post-commit) para un problema que hoy no existe.
- **Descarta B** por el costo (47 casos de uso) frente a un beneficio —el límite visible— que a esta escala no compensa. **Descarta C** porque dejaría la deuda de los 21 `commit()` y movería el criterio de salida.
- **`scope="function"` es obligatorio**, no un detalle: sin él, un commit fallido pasaría en silencio con un 200.

## Impacto en Configuración

- `src/shared/frameworks/db.py`: `get_session` confirma al terminar bien y revierte ante una excepción; un `SessionDep` único con `Depends(get_session, scope="function")` que reemplaza los cinco que hoy define cada BC (`notificaciones`, `banco_preguntas`, `actividad_evaluativa`, `identidad`, `analytics`).
- `src/shared/frameworks/db.py`: un administrador de contexto `unidad_de_trabajo()` para lo que corre fuera de un request y que, sin los commits de los repositorios, quedaría sin confirmar: `lifespan` de `src/app.py`, `bootstrap_administrador` y `cargar_datos_iniciales`. Las lecturas puras (`salud`, la autorización del canal) no lo necesitan.
- Los 20 `commit()` de los repositorios de Identidad y Banco pasan a `flush()`. El de `SQLAlchemyEventStore.append` se queda.
- `tests/unit/inc12/test_guardas_con_excepciones.py`: la lista de `commit()` baja de 21 archivos-conteos a 1 (el event store), justificada.
- `docs/plans/inc12/inc12-candidatas.md` y el Issue #668: el criterio de salida pasa a "ningún `commit()` fuera de la unidad de trabajo, salvo el del event store".
- `docs/architecture/` (vista de datos y transversal), `CLAUDE.md` si la regla se vuelve operativa.

## Consecuencias

- ✅ Una materia sin banco o un token reutilizable dejan de ser posibles: las escrituras de un caso de uso se confirman o se revierten juntas.
- ✅ Casi todo el cambio está en la capa de frameworks y en los repositorios; los casos de uso y sus tests con fakes no se tocan.
- ✅ La sesión en vivo queda como está.
- ⚠️ **El límite de la transacción queda fuera del caso de uso**, en la dependencia: no se ve leyendo el caso de uso. Se acepta a cambio de no tocar 47 casos de uso, y la guarda de commits impide que reaparezcan.
- ⚠️ **`DM-04` queda como limitación conocida**: un caso de uso que necesite escribir en dos streams a la vez no podría hacerlo de forma atómica. Hoy no existe; si aparece, se revisa este ADR (la opción A completa).
- ⚠️ **Dos reglas de implementación que `US-12.2.1` debe respetar:**
  1. Los repositorios hacen `flush()` dentro del mismo bloque donde hoy traducen conflictos (por ejemplo `email_unico`), para que una violación de integridad siga apareciendo donde se traduce y no al confirmar.
  2. Un `rollback()` en un repositorio descarta todo lo pendiente del request, no solo su escritura. Hoy `email_unico` lo hace; con la unidad de trabajo debe ser un punto de guardado (`begin_nested`) o aceptarse solo cuando es la primera escritura del caso de uso.
- ⚠️ **Los casos de uso que envían un email después de guardar** (`solicitar_recuperacion_password`, `generar_invitacion`) lo enviarían antes del commit: si el commit fallara, el enlace llegaría con un token que no existe y habría que pedirlo de nuevo. Se acepta a esta escala; no se hace diferido.
- ⚠️ El costo de `NullPool` (`ADR-018`) no cambia: cada operación sigue abriendo una conexión; la unidad de trabajo no suma conexiones, porque la sesión del request es una sola.

## Enmienda 2026-11-26 (al implementar `US-12.2.1`)

La decisión decía que la unidad de trabajo "confirma al terminar bien y **revierte ante una excepción**". Al armar el plan apareció que eso desactivaría un control de seguridad: tres lugares de Identidad **guardan un cambio y después levantan un error a propósito**: `iniciar_sesion` (suma el intento fallido, bloquea la cuenta al llegar al máximo y levanta `CredencialesInvalidas`), `cambiar_password` (el mismo contador, con `PasswordActualIncorrecta`) y `rechazar_si_bloqueada` (levanta un bloqueo temporal vencido y puede rechazar igual). Con un rollback ante cualquier excepción el intento fallido no se guardaría y el bloqueo de cuenta (`INV-ID-10`, `INV-ID-21`) dejaría de funcionar.

**Corrección, decidida por Víctor (2026-11-26): se revierte solo ante errores no controlados.**

- **Error controlado:** el resultado de una regla de negocio o de un control de seguridad. Un control de seguridad se respeta siempre: lo escrito hasta ese punto se **confirma**, igual que hoy. Son los `HTTPException` con código menor a 500 (lo que hoy levantan los routers) y toda clase definida en un `entities/errors.py`; desde `US-12.2.2`, toda subclase de `ErrorDeDominio`.
- **Error no controlado:** una falla técnica, como un error de acceso a la base, la pérdida de la conexión, un tiempo de espera, un error del código, o un `HTTPException` de 500 o más. **Revierte todo.**
- Una función `es_error_controlado(exc)` en `shared/frameworks/db.py` decide; reconoce las clases de dominio por el módulo donde están definidas (`*.entities.errors`), sin importar ningún contexto.

**Qué cambia respecto del texto original:** un error controlado ya no revierte. **Qué no cambia:** los cinco defectos reproducidos (una materia sin banco, un token reutilizable, etc.) los causa una falla técnica en la segunda escritura, y esa sí revierte.

**El trade-off que se acepta:** un error controlado levantado *entre* dos escrituras dejaría media operación. Hoy no existe ninguno: solo `iniciar_sesion`, `cambiar_password` y `rechazar_si_bloqueada` escriben antes de levantar un error, y es intencional. Una guarda (`test_guardas_con_excepciones.py`) fija esa lista, para que un caso nuevo sea una decisión consciente. **Responsabilidad:** un caso de uso que levanta un error controlado debe dejar un estado consistente.
