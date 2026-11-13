# Auditoría de `docs/design/domain/` contra el código (Incremento 10.1, Fase 3b)

> 2026-11-12 — versión `1.0.0`. Alcance: los cinco modelos por BC. **No** se auditaron `portal-entrada-modelo.md` ni los 8 archivos HTML (event storming y diagramas), ver "No auditado".

## Método
Para cada modelo se extrajeron los identificadores que cita y se buscaron en `src/` y `tests/`:
1. **Eventos de dominio** (clases de `entities/eventos*.py`) contra los nombres de evento del texto, en ambos sentidos.
2. **Puertos** (`class *Port`) contra los citados en el texto, en ambos sentidos.
3. **Invariantes** (`INV-<BC>-NN`) del texto contra las que figuran en `src/` o `tests/`.
4. Lectura puntual de los pasajes donde una diferencia apareció (firmas, valores).

Limitación: es una comparación de **nombres y valores**; no verifica que cada regla descripta se cumpla en el código. Esa verificación la dan los tests.

## Resultado

| Modelo | Eventos | Invariantes | Puertos y firmas | Veredicto |
|---|---|---|---|---|
| Identidad | 15 en código, ninguno sin documentar | 23 en el texto; 6 sin cita en código ni tests (`02`, `06`, `07`, `15`, `22`, `23`) | 11 puertos no listados; hash asíncrono no mencionado | Vigente, con nota |
| Banco de Preguntas | 5 en código, ninguno sin documentar | 5, todas con cita | Falta `ComisionConsultaPort` (Banco → Identidad) | Vigente, con nota |
| Actividad Evaluativa | 18 en código (9 + 9 del modo en vivo), ninguno sin documentar | 22, todas con cita | Faltan los puertos de consulta CQRS agregados después | Vigente, con nota |
| Analytics | Sin eventos (BC de solo lectura) | Sin invariantes | Falta `EstudianteConsultaPort`; no refleja `ADR-026` | Vigente, con nota |
| Notificaciones | Sin eventos propios | Sin invariantes | **`CanalEnvioPort.enviar` tiene un parámetro más** (`materia_id`, `ADR-023`) | Corregido y con nota |

## Diferencias y qué se hizo

| # | Dónde | Diferencia | Acción |
|---|---|---|---|
| 1 | Notificaciones | La firma documentada de `CanalEnvioPort.enviar` no tiene `materia_id` (cuenta SMTP por materia, `ADR-023`) | **Corregida en el texto** y anotada |
| 2 | Analytics | No refleja `ADR-026` (lectura de modelos ORM ajenos) ni lista `EstudianteConsultaPort`; cita como "puertos nuevos" lo que ya existe | Nota de vigencia al inicio |
| 3 | Identidad | No menciona el hash asíncrono (`US-ADJ-63`), ni los 11 puertos, ni que desde `BL-015` no lee modelos ORM de otro BC | Nota de vigencia |
| 4 | Banco | Falta el puerto `ComisionConsultaPort` | Nota de vigencia |
| 5 | Actividad Evaluativa | Los nombres `SesionCreada`, `SesionCerrada` e `IntentoRespuestaRegistrado` aparecen en notas históricas; faltan los puertos CQRS posteriores | Nota de vigencia con la equivalencia de nombres |
| 6 | Identidad | Seis invariantes sin cita en código ni tests | **Verificadas a mano**: `EXPIRACION_DIAS = 7`, `DURACIONES_GRUPALES_MINUTOS = (15, 60, 1440)` y el resto son comportamiento sin identificador; no se agregó nada |

Los falsos positivos del primer cruce (errores de dominio como `ActividadYaCerrada` o `SesionYaIniciada`, que el texto menciona y que son excepciones, no eventos) se descartaron al buscar cada nombre en todo `src/`.

## No auditado
- ⚠ **`portal-entrada-modelo.md`:** modelo transversal de la pantalla de entrada; no se contrastó.
- ⚠ **Los 8 HTML** (`*-event-storming.html` y `*-diagramas.html`): son artefactos de sesión de modelado; no se contrastaron con el código ni se tocaron.
- ⚠ **Contenido de reglas:** que cada invariante se cumpla tal como el texto la describe.
- ⚠ **Los modelos no se reescribieron:** las diferencias quedaron como notas de vigencia al inicio de cada uno, con una sola corrección de texto (#1). Reescribirlos es una decisión aparte.

## Cómo repetir esta auditoría
Extraer del texto los nombres entre acentos graves con forma `CamelCase`, `*Port` e `INV-XX-NN` y buscarlos en `src/` y `tests/` (`grep -rn <nombre> src tests`); comparar además la lista de `class` de `entities/eventos*.py` y de `entities/ports/` con la del texto.
