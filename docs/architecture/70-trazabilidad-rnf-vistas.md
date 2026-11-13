# 70 Trazabilidad de los atributos de calidad a las vistas

> Contrastada con el código y la evidencia de la versión `1.0.0` (Incremento 10.1, Fase 5). Plantilla: `_plantilla-vista.md`. La fuente de los escenarios es `docs/rf/RNF_v1.md` (no se modifica).

## Propósito
Decir, para cada escenario de calidad, **qué mecanismo lo cumple, en qué vista se describe, qué evidencia existe y si se cumple tal como está escrito**. Es la vista que une los requerimientos de calidad con la arquitectura.

## Interesados
**Mantenedor** (qué se prometió y qué no se cumple), **instalador** (qué esperar de la operación) y **materia** (cómo se trazan los atributos de calidad hasta el código).

## Para leer esta vista
La columna **Estado** es lo importante. *Cumple* significa que hay un mecanismo implementado **y** evidencia. *Parcial* y *No cumple* describen una distancia real entre lo escrito en `RNF_v1.md` y lo que hace la `1.0.0`; no son errores de este documento. Cada fila apunta a la vista donde se explica.

## Escenarios

| Atributo y escenario | Mecanismo en la `1.0.0` | Vista | Evidencia | Estado |
|---|---|---|---|---|
| **Rendimiento.** Ranking en sesión en vivo: servidor ≤ 100 ms con 60 alumnos | El ranking se actualiza al responder (read model en la misma transacción); cerrar la pregunta solo lee lo acumulado | `30` (flujo 5), `12` | `quality/reports/uat/inc6/rendimiento-cierre.json`: p95 de 79 ms (caso de uso) y 124 ms (HTTP), 60 conexiones **simuladas**, en una Mac | **Cumple**, medido en entorno de desarrollo, no en un servidor |
| **Disponibilidad 1.** Caída durante una sesión en vivo: healthcheck y ventana de 5 minutos | `GET /api/health` y `/api/health/ready` sin autenticación; en Docker, `restart: unless-stopped` y `healthcheck`; el cliente reconecta y consulta el estado por HTTP | `40` (§4), `60`, `02` | Tests de salud (`tests/integration/inc9/test_us_8_3_3_observabilidad_integration.py`); la recuperación automática no se ensayó | **Parcial**: el healthcheck existe; la reanudación tras una caída real no se probó |
| **Disponibilidad 2.** Caída en período abierto: extender el plazo (RF-11b) | `PATCH /actividades/{id}/periodo` | `12`, `30` (flujo 4) | `tests/features/inc3/US-3.3.1-modificar-periodo-disponibilidad.feature` | **Cumple** |
| **Confiabilidad.** Interrupción de un alumno en período abierto: cero pérdida y set fijo | Cada respuesta es un evento guardado al confirmarse; el set de preguntas se fija al iniciar; iniciar de nuevo retoma la evaluación en curso | `30` (flujo 4), `12`, `24c` | `tests/features/inc3/US-3.1.3-iniciar-evaluacion.feature` (retoma sin generar un set nuevo) | **Cumple** |
| **Seguridad.** Control de acceso por rol | `require_rol` en cada ruta, más la asignación del docente a la comisión o a la materia | `40` (§1), `10`, `11`, `12`, `13` | Tablas de rutas y roles de las vistas de componentes; tests de roles por US | **Cumple** (verificable por revisión de la API, como pide el escenario) |
| **Usabilidad 1.** Dispositivos y navegadores | Frontend responsive (Tailwind, shadcn/ui) | `40` (§7), `docs/design/ux/` | Verificado con un viewport emulado de 375 px; un celular real solo abrió el login | **Parcial**: sin prueba en celulares ni en los cuatro navegadores |
| **Usabilidad 2.** Legibilidad de la proyección en el aula | Criterios de tamaño y contraste definidos en el diseño de UX (fuente de la pregunta ≥ 40 px a 1080p) | `40` (§7), `docs/design/ux/wireframes-actividad-evaluativa-en-vivo.md` §1.1 | El criterio quedó definido; no hay medición en un aula real | **Parcial**: definido, no verificado en el aula |
| **Mantenibilidad.** Nuevo tipo de pregunta en ≤ 1 día sin tocar sesiones, puntaje ni analytics | Hay dos tipos hoy (verdadero/falso y opción múltiple) como clases distintas de `PreguntaPlantilla` | `11`, `12` | Ninguna: el ítem sigue abierto en `RNF_v1.md` | **No verificado**: el adaptador de preguntas de Actividad Evaluativa conoce las clases concretas, así que un tipo nuevo probablemente lo toque |
| **Observabilidad.** Diagnóstico post-incidente: errores, conexiones y actividad como eventos | Los eventos de Actividad Evaluativa se guardan en `events`; logs con formato `json` opcional y tokens enmascarados; salud sin autenticación | `40` (§3, §4), `12`, `24c` | Tests de logging y de salud | **Parcial**: la actividad queda como eventos y los errores en el log; **los inicios de sesión (`SesionIniciada`) y las conexiones no se registran** (el caso de uso devuelve el evento y el router lo descarta) |
| **Administrabilidad 1.** Un push a `main` despliega solo | El CD construye la imagen en cada push a `main` y publica imagen y Release solo con un tag; **no despliega a ningún servidor** | `50` (§5), `60` | `.github/workflows/cd.yml` | **No cumple como está escrito**: instalar o actualizar es una acción del operador (`cognion.sh desplegar`); el despliegue automático quedó pendiente de la decisión de infraestructura |
| **Administrabilidad 2.** Backup automático mensual con retención de 12 meses | `respaldar.sh`: `pg_dump` verificado, `sha256`, rotación de 30 copias; el operador lo programa y lo copia fuera del servidor | `60` (respaldo), `ADR-022` | `tests/unit/inc10/test_us_10_2_2_respaldo.py` | **No cumple como está escrito**: no hay automatización ni retención de 12 meses garantizadas por la herramienta |

## Restricciones técnicas del `RNF_v1.md`

| Restricción | Estado en la `1.0.0` |
|---|---|
| Solo online | Se mantiene; sin PWA (`01`, `02`) |
| Autenticación JWT stateless | Se cumple, sin refresh (`ADR-013`, `40`) |
| CI/CD obligatorio | CI completo en cada PR de código; el CD construye y publica, no despliega (`50`) |
| Event sourcing como mecanismo de registro | Aplicado solo a Actividad Evaluativa (`ADR-002`, `12`) |
| Infraestructura pendiente de decisión | Sigue pendiente; hay tres variantes de instalación (`60`) |

## Resumen
De 11 escenarios: **4 cumplen** (rendimiento, período abierto, confiabilidad y seguridad), **4 son parciales** (caída en vivo, dispositivos, proyección y observabilidad), **1 no está verificado** (mantenibilidad) y **2 no cumplen como están escritos** (despliegue automático y backup mensual). Estas dos últimas están acompañadas por una decisión de infraestructura que sigue abierta.

## Cómo verificar esta vista contra el código
Cada fila nombra su evidencia. Para repetirla: `GET /api/health` en una instalación, `quality/reports/uat/inc6/rendimiento-cierre.json`, los features de `tests/features/inc3/`, y `.github/workflows/cd.yml`.

## Cuándo hay que actualizarla
Un escenario de `RNF_v1.md` nuevo o modificado; una decisión de infraestructura (despliegue automático, respaldo mensual); una medición nueva (carga, celular real, aula).

## Sin verificar
- ⚠ Las filas "Parcial" y "No verificado" indican lo que falta probar; no se ejecutó ninguna prueba nueva en esta fase.
- ⚠ El estado se evaluó contra el texto de `RNF_v1.md`; los escenarios no se renegociaron.
