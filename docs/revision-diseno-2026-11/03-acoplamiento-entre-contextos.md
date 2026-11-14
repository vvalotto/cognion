# 03 · Modularidad y acoplamiento entre contextos

> Pregunta: ¿los cinco bounded contexts son realmente independientes?

## Qué se miró

- Todos los imports de `src/<bc>/` hacia otro contexto, clasificados por la capa de destino.
- El contrato de aislamiento de `import-linter` y `ADR-026`.
- Dos adaptadores completos: [`pregunta_consulta_port_in_process.py`](../../src/actividad_evaluativa/frameworks/adapters/pregunta_consulta_port_in_process.py) y [`evaluacion_desempeno_consulta_port_in_process.py`](../../src/analytics/frameworks/adapters/evaluacion_desempeno_consulta_port_in_process.py).

## Fortalezas

- **El consumidor define su puerto.** Cada contexto declara en `entities/ports/` lo que necesita del otro, con sus propios tipos (`ContenidoPregunta`, `NivelesDePregunta`). El núcleo de cada contexto no conoce a los demás.
- **Los imports entre contextos están confinados** a `frameworks/adapters/`. Fuera de esa carpeta no hay ninguno.
- **`shared/` no depende de ningún contexto** (contrato cumplido) y es chico: 565 líneas.

## Mapa de dependencias entre contextos

Imports desde `frameworks/adapters/` hacia otro contexto, por destino:

| Origen | Destino | Qué importa |
|---|---|---|
| Actividad Evaluativa | Identidad | 4 repositorios SQL, la entidad `Usuario` |
| Actividad Evaluativa | Banco de Preguntas | 3 repositorios SQL, 1 caso de uso, la entidad `PreguntaPlantilla` |
| Actividad Evaluativa | Notificaciones | 2 adaptadores, 2 casos de uso |
| Analytics | Actividad Evaluativa | 4 entidades, 2 puertos, modelos ORM |
| Analytics | Identidad, Banco | 2 repositorios SQL, modelos ORM |
| Identidad | Actividad Evaluativa | 1 adaptador |
| Identidad | Banco de Preguntas | 1 repositorio SQL, 1 caso de uso |
| Identidad | Notificaciones | 1 adaptador |
| Banco de Preguntas | Identidad | 1 repositorio SQL |
| Notificaciones | Identidad | 1 repositorio SQL |

## Hallazgos

### AC-01 · Ningún contexto publica una interfaz; el consumidor se acopla a sus internos

- **Vara:** Conformidad · **Severidad:** Alta · **Confianza:** Verificado · **Esfuerzo:** L
- **Evidencia:**
  - `CLAUDE.md` dice: "Comunicación entre BCs: solo por puertos definidos en `entities/ports/` — nunca imports directos entre BCs".
  - El contrato de aislamiento ignora `"src.*.frameworks.adapters.** -> src.**"`: 71 imports aceptados sin mirar a qué apuntan.
  - En la práctica los adaptadores instancian repositorios SQL de otro contexto y usan sus entidades. Ejemplo: `PreguntaConsultaPortInProcess.__init__` crea `SQLAlchemyBancoRepository(session)` y `SQLAlchemyPreguntaRepository(session)`, y en las líneas 85, 105 y 129 hace `isinstance(pregunta, PreguntaPlantillaOpcionMultiple)`.
- **Por qué importa:**
  - El puerto protege al consumidor, pero el proveedor no tiene frontera: cambiar la firma de un repositorio de Banco o un campo de `PreguntaPlantilla` rompe a Actividad Evaluativa, y nada en Banco avisa que ese repositorio tiene clientes externos.
  - El adaptador de Actividad Evaluativa defiende un invariante de Banco ("devuelve 0 si la materia no tiene Banco, no debería ocurrir"). Es conocimiento de un contexto escrito en otro.
- **Recomendación:**
  1. Que cada contexto exponga un módulo público (por ejemplo `src/<bc>/publico.py`) con las consultas que ofrece y tipos de datos propios, sin entidades ni repositorios.
  2. Cambiar el contrato: los adaptadores solo pueden importar `src.<otro_bc>.publico`.
  3. Migrar de a un contexto proveedor por vez, empezando por Banco de Preguntas (tiene un solo consumidor fuerte).

### AC-02 · Identidad depende de los tres contextos que dependen de ella

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** M
- **Evidencia:** hay dependencias en ambos sentidos entre Identidad y Actividad Evaluativa, entre Identidad y Banco de Preguntas, y entre Identidad y Notificaciones (tabla de arriba).
- **Por qué importa:** no existe un orden entre contextos. Un subdominio genérico (Identidad) depende del núcleo, cuando debería ser al revés. Ningún contexto de negocio puede probarse, entenderse o extraerse sin los demás.
- **Recomendación:**
  1. Declarar la dirección permitida con un contrato `layers` entre contextos (por ejemplo: Analytics → Actividad Evaluativa → Banco → Identidad → Notificaciones).
  2. Invertir las tres dependencias que quedan al revés. `EliminarCuentaUseCase` pregunta a Actividad Evaluativa si el estudiante tiene evaluaciones: esa consulta puede inyectarla el composition root de `app.py`, que ya conoce a todos.

### AC-03 · Analytics lee los eventos crudos de Actividad Evaluativa y los recorre completos

- **Vara:** Decisión · **Severidad:** Alta · **Confianza:** Verificado (el acoplamiento), Inferido (el impacto en tiempo de respuesta) · **Esfuerzo:** L
- **Evidencia:**
  - `ADR-026` acepta que Analytics lea los modelos ORM de otros contextos.
  - [`evaluacion_desempeno_consulta_port_in_process.py`](../../src/analytics/frameworks/adapters/evaluacion_desempeno_consulta_port_in_process.py) consulta `EventoModel` e interpreta el payload con claves literales (`payload["actividad_id"]`, `payload["estudiante_id"]`, `payload["materia_id"]`).
  - `_todos_los_streams_evaluacion` (líneas 137–145) trae todos los eventos de tipo Evaluación de toda la base, y el filtro por actividad y por estudiante se hace después en Python (líneas 159–171).
- **Por qué importa:**
  - El formato de los eventos es un contrato entre dos contextos, sin tipo ni versión ([DM-02](04-dominio-y-event-sourcing.md#dm-02--los-eventos-no-tienen-versión-de-esquema)). Un cambio de payload en Actividad Evaluativa rompe Analytics en ejecución, no al compilar.
  - El costo de cada consulta crece con todo el historial, no con la comisión consultada. Con un cuatrimestre no se nota; con varios años sí. `RF-18` (KPIs históricos) apunta exactamente a ese caso.
- **Recomendación:**
  - Corto plazo: filtrar en SQL (`payload->>'actividad_id'` con índice) y agregar un test de contrato que fije las claves del payload que Analytics lee.
  - Antes de implementar `RF-18`: una proyección de desempeño mantenida al registrar cada respuesta, como ya se hace con el ranking en vivo.

### AC-04 · Identidad es el segundo contexto más grande

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Inferido · **Esfuerzo:** L (si se decide extraer)
- **Evidencia:** Identidad tiene 6.391 líneas y 106 archivos (28 % del backend), más del doble que Banco de Preguntas. Incluye `comisiones_router.py`, `materias_comisiones_router.py`, invitaciones grupales y la asignación de docentes.
- **Por qué importa:** comisión, materia de la comisión y asignación de docentes son conceptos de la estructura académica, no de identidad. Que vivan ahí explica por qué todos los contextos necesitan un `ComisionConsultaPort` (hay cuatro) y por qué Identidad termina dependiendo de Banco (AC-02).
- **Recomendación:** no extraer ahora. Registrar la observación en un ADR y usarla como criterio si Identidad sigue creciendo: "Estructura académica" es un candidato natural a contexto propio.

## Juicio

El aislamiento está bien resuelto del lado del consumidor y sin resolver del lado del proveedor. La regla escrita ("solo por puertos") es más estricta que la regla verificada ("solo desde `frameworks/adapters/`"). Cerrar esa distancia con una interfaz pública por contexto es la mejora estructural de mayor retorno de todo el informe.
