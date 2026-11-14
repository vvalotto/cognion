# 05 · Decisiones de implementación por capa

> Pregunta: ¿cada capa hace lo que le corresponde y nada más?

## Qué se miró

- Los 32 controllers de `interface_adapters/controllers/` (análisis sintáctico de sus métodos).
- Los routers de los cinco contextos y el manejo de errores.
- Todos los `commit()` de `src/` y los casos de uso con más de una escritura.
- [`app.py`](../../src/app.py), [`servidor.py`](../../src/servidor.py), [`settings.py`](../../src/settings.py), `shared/frameworks/db.py` y el `ConnectionManager` de WebSocket.

## Fortalezas

- **Código prolijo y explicado.** 0 marcas `TODO` o `FIXME`, docstrings en todo, y las 6 capturas de `Exception` genéricas están justificadas en un comentario.
- **Configuración que falla temprano.** `Settings` rechaza en `staging` y `produccion` el secreto de ejemplo, hosts locales, el comodín de CORS y el modo de email por consola, y lista todas las violaciones juntas sin mostrar el secreto.
- **Casos de uso legibles.** `ResponderPreguntaEnVivoUseCase.execute` se lee como el escenario: cargar, validar, corregir, persistir, publicar.
- **Decisiones de escala explícitas.** El `ConnectionManager` en memoria y el verificador de vencimientos dicen en su docstring para qué volumen están pensados.

## Hallazgos

### IM-01 · Los controllers no cumplen ninguna función

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** M
- **Evidencia:**
  - De 74 métodos en 32 controllers, 66 tienen una sola sentencia: delegar en un caso de uso y devolver lo que devuelva. Ejemplo: [`conduccion_en_vivo_controller.py`](../../src/actividad_evaluativa/interface_adapters/controllers/conduccion_en_vivo_controller.py).
  - No existe ningún presenter. La traducción de entidad a respuesta y de error a HTTP está en los routers.
  - En Actividad Evaluativa la capa `interface_adapters/` son 520 líneas, casi todas de pasamanos.
- **Por qué importa:** la capa existe porque la arquitectura la nombra, no porque resuelva algo. Cuesta: cada endpoint nuevo pide un método más, una dependencia más en el composition root (422 líneas en Actividad Evaluativa) y a veces partir el controller para no pasar el umbral de CBO ([IQ-01](08-instrumentos-de-calidad.md#iq-01--el-umbral-de-cbo-está-moldeando-el-diseño)).
- **Recomendación:** elegir una de dos y registrarla en un ADR:
  1. **Darle trabajo a la capa** (recomendada si se resuelve IM-02): el controller devuelve un tipo de salida propio y los routers dejan de importar entidades.
  2. **Eliminarla**: los routers llaman a los casos de uso. Es menos código y es honesta con lo que hoy pasa.

### IM-02 · La traducción de errores a HTTP está repetida a mano

- **Vara:** Decisión · **Severidad:** Alta · **Confianza:** Verificado · **Esfuerzo:** M
- **Evidencia:**
  - 138 `raise HTTPException` en 21 archivos de routers; 32 solo en `sesiones_en_vivo_router.py` (546 líneas).
  - Ningún `exception_handler` registrado en `app.py`.
  - 78 clases de error en los `entities/errors.py` (39 en Actividad Evaluativa, 25 en Identidad), todas heredan directamente de `Exception`, sin base común.
- **Por qué importa:**
  - Cada endpoint repite el mismo `try/except` con la lista de errores que su autor recordó. Un error de dominio que nadie listó sale como 500.
  - Qué código HTTP corresponde a cada error está decidido endpoint por endpoint; nada impide que el mismo error sea 404 en uno y 422 en otro.
  - Es la causa de buena parte de los 71 métodos largos que DesignReviewer marca en `frameworks/`.
- **Recomendación:**
  1. Una base `ErrorDeDominio` en `shared/entities/` con pocas categorías: no existe (404), no autorizado (403), regla violada (422), conflicto (409).
  2. Cada error hereda de su categoría.
  3. Un manejador por categoría en `app.py`. Los routers pierden casi todos sus `try/except`.

### IM-03 · La transacción vive en el repositorio, no en el caso de uso

- **Vara:** Conformidad · **Severidad:** Alta · **Confianza:** Verificado (el mecanismo), Inferido (que haya ocurrido una inconsistencia) · **Esfuerzo:** M
- **Evidencia:**
  - Hay 20 `commit()` en los repositorios de Identidad y Banco y 1 en el event store. Ningún caso de uso controla la transacción.
  - [`crear_materia.py`](../../src/banco_preguntas/use_cases/crear_materia.py) guarda la materia (commit) y después el banco (otro commit). Su docstring dice "en la misma operación" y cita `INV-BP-01`, que exige que toda materia tenga banco.
  - `EliminarCuentaUseCase` borra los tokens de recuperación (commit) y después el usuario (commit).
  - Otros 6 casos de uso de Identidad y Banco hacen dos escrituras del mismo modo.
- **Por qué importa:** si la segunda escritura falla, la primera ya quedó confirmada: una materia sin banco, un usuario sin tokens pero no eliminado. El invariante está declarado y no está garantizado. El adaptador de Actividad Evaluativa ya se defiende del caso ("devuelve 0 si la materia no tiene Banco").
- **Recomendación:** unidad de trabajo por caso de uso. Los repositorios hacen `flush`; la dependencia que entrega la sesión confirma al terminar bien y revierte ante una excepción. Con eso el event store deja de confirmar por su cuenta ([DM-04](04-dominio-y-event-sourcing.md#dm-04--la-transacción-termina-dentro-de-append)).

### IM-04 · El canal en vivo autentica pero no autoriza

- **Vara:** Conformidad (escenario de seguridad: control de acceso por rol) · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:** el endpoint WebSocket de `sesiones_en_vivo_router.py` (líneas 417–445) verifica que el JWT sea válido y conecta. No comprueba que el usuario pertenezca a la comisión de esa sesión ni su rol. El token viaja en la URL (`?token=...`).
- **Por qué importa:** cualquier usuario con sesión iniciada puede escuchar el canal de cualquier sesión en vivo si conoce su identificador, y recibir enunciados y ranking. A la escala de una comisión el riesgo es bajo, pero es una excepción al control por rol que el resto de la API sí cumple. Un token en la URL puede quedar en el registro de accesos del proxy.
- **Recomendación:** antes de `conectar`, exigir que el usuario sea docente de la comisión o participante de la sesión. Para el token, un ticket de un solo uso y vida corta pedido por HTTP.

### IM-05 · Dos supuestos de proceso único sin protección

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:**
  - El `ConnectionManager` guarda las conexiones en un diccionario del proceso.
  - El verificador de vencimientos es una tarea que arranca en el `lifespan` de cada proceso.
  - El `Dockerfile` arranca un solo proceso de `uvicorn`, así que hoy funciona.
- **Por qué importa:** con dos procesos o dos réplicas, parte de los alumnos no recibe los mensajes y el verificador corre dos veces. La restricción está escrita en docstrings, pero nada la hace cumplir: agregar `--workers 2` "para que ande más rápido" rompe la sesión en vivo sin ningún error.
- **Recomendación:** un bloqueo consultivo de PostgreSQL para el verificador, y una advertencia explícita en `docs/INSTALACION.md` y en la vista de despliegue. Si alguna vez hace falta más de un proceso, `LISTEN/NOTIFY` de PostgreSQL alcanza para el canal.

### IM-06 · `NullPool` en producción por una necesidad de los tests

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Verificado (la configuración), Inferido (el costo) · **Esfuerzo:** S
- **Evidencia:** `shared/frameworks/db.py` crea el motor con `poolclass=NullPool` (`ADR-018`). El comentario explica el motivo: tests que corren en distintos event loops. `deploy/servidor/docker-compose.yml` sube `max_connections` a 100 para absorberlo.
- **Por qué importa:** cada operación abre y cierra una conexión a PostgreSQL. En una sesión en vivo con 60 alumnos respondiendo a la vez son 60 conexiones simultáneas y 60 negociaciones. El escenario de rendimiento se midió en una Mac con conexiones simuladas; en el servidor chico previsto el margen es menor.
- **Recomendación:** que la clase de pool salga de la configuración: `NullPool` en tests, pool normal en ejecución. Volver a medir el escenario de 60 alumnos en un servidor.

### IM-07 · Los adaptadores entre contextos construyen sus dependencias

- **Vara:** Decisión · **Severidad:** Baja · **Confianza:** Verificado · **Esfuerzo:** se resuelve con AC-01
- **Evidencia:** `PreguntaConsultaPortInProcess.__init__` recibe una sesión y crea adentro los repositorios de Banco de Preguntas.
- **Por qué importa:** el adaptador solo se puede probar con una base real. Con la interfaz pública de [AC-01](03-acoplamiento-entre-contextos.md#ac-01--ningún-contexto-publica-una-interfaz-el-consumidor-se-acopla-a-sus-internos) recibiría esa interfaz ya construida.

## Juicio

Las capas internas están bien. Los problemas están en los bordes: quién traduce (IM-01, IM-02), quién confirma la transacción (IM-03) y quién autoriza en el canal en vivo (IM-04). IM-02 e IM-03 tienen el mejor retorno: son cambios acotados que eliminan código repetido y cierran un riesgo real de datos inconsistentes.
