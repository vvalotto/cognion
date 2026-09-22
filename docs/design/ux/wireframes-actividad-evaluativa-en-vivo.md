# BC Actividad Evaluativa — Wireframes: Sesión en Vivo

> Estado documental: **vigente — aprobado por Víctor 2026-09-17 en el comentario de cierre del
> Issue #380 (US-6.0.2, Iteración 0, Incremento 6), tras seis rondas de ajuste.**
> Alcance: exclusivamente el modo **en vivo** (RF-08, RF-09, RF-10). El modo período abierto
> ya está cubierto por `wireframes-actividad-evaluativa.md`.
>
> Fuente: `docs/rf/RF_v1.md` (RF-08, RF-09, RF-10), `docs/rf/RNF_v1.md` (Rendimiento, Escenario
> 1 — ranking en vivo ≤100ms server-side, hasta 60 alumnos; Usabilidad — criterios de
> legibilidad en proyección, ítem abierto de `CLAUDE.md` resuelto en este documento, §1.1),
> `docs/design/domain/BC-actividad-evaluativa-modelo.md` §§10-18 (comandos, eventos,
> invariantes INV-AEV-01 a 09, §17 hot spots resueltos con Víctor 2026-09-17, seis rondas),
> `docs/plans/inc6/inc6-candidatas.md` §Spike RF-10 (fórmula de puntaje).
>
> Prototipo: `docs/design/ux/prototipos/actividad-evaluativa-en-vivo.html` — navegable,
> 12 pantallas aprobadas (7 Docente/proyección, 5 Estudiante) + 7 pantallas/variantes
> agregadas por `US-6.3.0` (§6, huecos H1 a H9). Seis rondas con Víctor (2026-09-17):
> (1) el cierre de cada pregunta se separa en histograma de respuestas + ranking, no un único
> paso combinado; (2) presentar la pregunta y mostrar sus opciones son dos pasos manuales
> separados — el temporizador arranca recién al mostrar las opciones, que se ven como cajas de
> **color sólido** sin ícono de forma; (3) **corrige la (2):** el celular del Estudiante
> también usa tarjetas grandes de color sólido, táctiles, mismo color que la proyección — tocar
> una tarjeta responde al instante, sin botón de confirmación aparte; (4) el resultado personal
> (acierto + puntaje propio, sin ranking) se muestra apenas el Estudiante responde, sin esperar
> a que el Docente cierre la pregunta — elimina la pantalla intermedia `#est-esperando`; el
> ranking completo queda reservado para el resultado final de la sesión; (5) la sesión se
> restringe a Comisiones puntuales (`comisiones_ids`, igual que período abierto); (6)
> **corrige la (5):** no es una lista opcional — la sesión se crea desde el detalle de **una**
> Comisión puntual (`comision_id` única y obligatoria, resuelta por contexto de navegación,
> nunca "todas las Comisiones de la Materia").

---

## 1. Identidad visual

Misma paleta y tipografía que `wireframes-actividad-evaluativa.md` §1 (azul institucional
`#1D75B5`, verde de acento `#53AA74`, Roboto). Primitivas reutilizadas de ese documento: `Card`,
`Badge`, `Breadcrumb`, `progress-bar`, `opcion-row`. Primitivas **nuevas** de este documento:
- La pantalla de **proyección** (`.stage-*`), pensada para un dispositivo distinto al resto del
  sistema — no una laptop/celular en la mano, sino un proyector de aula visto desde varios
  metros de distancia, con luz ambiente (criterios de legibilidad, §1.1).
- **Cajas de opción a color sólido** (`.stage-option.color-a/b/c/d` — rojo/azul/amarillo/verde),
  en la proyección (§2.4) — el texto completo de la opción entra dentro de la caja, sin ícono
  de forma aparte.
- **Tarjetas táctiles** (`.tap-card.color-a/b/c/d`, grilla 2×2) — mismos 4 colores que las
  cajas de opción de la proyección, pensadas para tocar con el pulgar en un celular; tocar
  responde al instante, sin botón de confirmación (§3.3, tercera ronda — reemplaza el uso de
  `.opcion-row` en esta pantalla puntual, que sigue vigente para el examen de período abierto).
- **Histograma de respuestas** (`.stage-histograma`, barras horizontales por opción) — §2.5.

### 1.1 Criterios de legibilidad en proyección (resuelve el ítem abierto de `RNF_v1.md`/`CLAUDE.md`)

| Criterio | Valor | Justificación |
|---|---|---|
| Tamaño de fuente — pregunta | ≥ 40px (2.5rem) a 1080p | Legible a ~10-12m de distancia (regla práctica de proyección: ~1px de altura de línea por cada 25-30px de distancia en pantallas de 1080p) — el aula tipo de FIUNER para 30-60 alumnos no supera esa distancia |
| Tamaño de fuente — temporizador y opciones | ≥ 26px | Segundo elemento en jerarquía visual, sigue siendo legible desde el fondo |
| Tamaño de fuente — eyebrow/contexto ("Pregunta 3 de 10") | ≥ 18-20px, mayúsculas, letter-spacing | Información secundaria, no crítica para responder |
| Contraste | Fondo oscuro (`#0F1B24`) + texto claro (`#FFFFFF`/`#6FE39A`) — ratio ≥ 7:1 (WCAG AAA) | Más estricto que el AA general del resto del sistema (RNF Usabilidad, escenario general) porque acá no hay control de brillo/ángulo de lectura como en una pantalla personal — reduce el deslumbramiento en aulas con luz natural |
| Layout | Una sola columna centrada, sin scroll, máximo 3-4 elementos por pantalla (pregunta, timer, una acción) | Un proyector no se "recorre" como una pantalla personal — todo lo relevante debe entrar en el primer vistazo |
| Paleta de proyección | Tokens propios (`--stage-*`), no los mismos que el resto del sistema (`--card`/`--background` claros) | El resto del sistema prioriza legibilidad de cerca en pantalla propia; la proyección prioriza contraste a distancia — son necesidades distintas, mismo criterio que un dashboard vs. un formulario |

Estos criterios aplican únicamente a las pantallas `stage-*` (Docente, vista de proyección,
§2.3-2.7) — las pantallas del Estudiante (§3) y la de creación/sala de espera del Docente (§2.1,
§2.2) siguen la identidad visual estándar del resto del sistema, se ven en el dispositivo
propio del usuario, no en el proyector.

---

## 2. Pantallas — Docente

### 2.1 Nueva sesión en vivo (`#doc-nueva-sesion`)

**Actor:** Docente.
**Comando:** `CrearSesionEnVivo(comision_id, unidad_tematica?, tema?, cantidad_preguntas, tiempo_limite_por_pregunta_segundos)`.

**Punto de entrada (corregido con Víctor — reemplaza la versión anterior de esta sección, que
proponía entrar desde "Actividades"/Materia):** la sesión en vivo se crea **desde el detalle de
una Comisión puntual** (`ComisionDetalleDocente.tsx`, pantalla ya existente y aprobada,
`US-ADJ-26`) — ahí aparece un botón nuevo "+ Nueva sesión en vivo". La pantalla "Actividades"
(período abierto, `wireframes-actividad-evaluativa.md` §2.1) **no cambia** — sigue siendo
exclusivamente el listado de período abierto, sin un segundo botón. Distinto de la primera
corrección de esta ronda: a diferencia de `ActividadEvaluativaPeriodoAbierto`, que sí tiene
sentido crear para "todas las Comisiones de la Materia" (examen asíncrono), una sesión en vivo
se da en el momento, en la clase de una Comisión concreta — no existe la opción "todas".

| Elemento | Detalle |
|---|---|
| Contexto | Breadcrumb "Actividad evaluativa › {Materia} › {Comisión, ej. Lunes 18-20hs} › Nueva sesión en vivo" |
| Campos | Unidad temática (opcional), Tema (opcional), Cantidad de preguntas, Tiempo límite por pregunta en segundos — **sin valor por defecto** (spike RF-10, confirmado con Víctor). **Sin selector de Comisión** — ya es el contexto de la pantalla, no un campo del formulario |
| Validación de cliente | Cantidad de preguntas ≥ 1; tiempo límite > 0 (INV-AEV-02, espejo del lado servidor) |
| Hint | Aclara que el puntaje combina velocidad, dificultad e importancia (spike RF-10) — se ve en el ranking tras cada pregunta |
| Comisión / Materia | Ambas implícitas por el contexto de navegación — `comision_id` viene de la ruta, `materia_id` se resuelve internamente a partir de esa Comisión (`ComisionConsultaPort` nuevo, ver modelo §14) |
| Acción | "Crear sesión" → pasa a la sala de espera (`#doc-sala-espera`), estado `EnEspera` |
| Error server-side (a especificar en la spec de implementación) | 422/404 con `ComisionNoExiste`, `PreguntasInsuficientes` (INV-AEV-01), `TiempoLimiteInvalido` (INV-AEV-02) |

### 2.2 Sala de espera (`#doc-sala-espera`)

**Actor:** Docente.
**Comando:** `IniciarSesionEnVivo(sesion_id)`.
**Query:** `ListarParticipantesDeSesion(sesion_id)` (read model `participantes_por_sesion`).

| Elemento | Detalle |
|---|---|
| Datos de la sesión | Cantidad de preguntas, materia, tiempo límite por pregunta |
| Participantes | Chips con nombre de cada estudiante unido (`EstudianteUnido`), actualizados en vivo vía WebSocket a medida que se van uniendo — mismo canal que el resto de la dinámica (§16 del modelo) |
| Hint | Aclara que se puede seguir sumando gente después de iniciar (unión tardía, hot spot 2 confirmado) |
| Acción | "Iniciar sesión" → `IniciarSesionEnVivo` → pasa a la vista de proyección de la primera pregunta (`#stage-pregunta-sola`) |
| Proyección | Este es el momento en que el Docente comparte la pantalla del proyector con el aula — el prototipo no incluye una pantalla de espera *en el proyector* separada de esta (se asume que el Docente ve esta misma pantalla en su propio dispositivo mientras conecta el proyector; la primera vista realmente proyectada es la pregunta 1) |

### 2.3 Proyección — pregunta sola (`#stage-pregunta-sola`)

**Actor:** Docente (comando), toda el aula (observa).
**Comando:** `MostrarOpcionesDeLaPregunta(sesion_id)`.

| Elemento | Detalle |
|---|---|
| Enunciado | Texto completo de la pregunta actual, tipografía grande (§1.1) — **sin opciones todavía**, corrección de la primera ronda de este documento (que las mostraba juntas) |
| Acción | "Mostrar opciones" → `MostrarOpcionesDeLaPregunta` → pasa a `#stage-pregunta-opciones`, recién ahí arranca el temporizador (INV-AEV-08 se mide desde acá, no desde que se presentó el enunciado) |
| Por qué dos pasos, no uno | Le da al Docente margen para leer la pregunta en voz alta o dejar que el aula la lea antes de que empiece a correr el tiempo — decisión de Víctor en la segunda ronda de esta spec, § modelo de dominio §17 punto 7 |

### 2.4 Proyección — pregunta con opciones (`#stage-pregunta-opciones`)

**Actor:** Docente (comando), toda el aula (observa).
**Comando:** `CerrarPreguntaActual(sesion_id)`.
**Datos en vivo:** conteo de respuestas recibidas — read model derivado de `ParticipacionEnVivo` con `RespuestaEnVivo` para la pregunta actual, actualizado por WebSocket sin recargar.

| Elemento | Detalle |
|---|---|
| Enunciado | Se mantiene visible, en un tamaño menor que en `#stage-pregunta-sola` para dejar lugar a las opciones |
| Opciones | Las 4 opciones como **cajas de color sólido** (rojo/azul/amarillo/verde), texto completo dentro de cada caja — **sin ícono de forma** (corrige la primera ronda, que proponía `▲◆●■`); **sin indicar todavía cuál es la correcta** |
| Temporizador | Cuenta regresiva visual hasta `tiempo_limite_por_pregunta_segundos`, arranca al entrar a esta pantalla — **valor informativo para el aula**, el corte real de aceptación de respuestas es server-side (INV-AEV-08), no depende de que este reloj visual esté sincronizado al milisegundo |
| Barra de progreso | Refuerza visualmente el tiempo restante junto al número |
| Conteo de respuestas | "`N` / `total` ya respondieron" — usa `participantes_por_sesion` (denominador) y la cantidad de `RespuestaEnVivo` de la pregunta actual (numerador). **Solo el total** — sin desglose por opción todavía (eso es el histograma, §2.5, recién visible al cerrar) |
| Acción | "Cerrar pregunta" (destructiva, deliberada) → `CerrarPreguntaActual` → pasa a `#stage-histograma` |

### 2.5 Proyección — histograma de respuestas (`#stage-histograma`)

**Actor:** toda el aula (observa) — sin acción de Docente requerida para avanzar.
**Query:** `ObtenerDistribucionDeRespuestas(sesion_id)` (read model `distribucion_por_pregunta`, §15 del modelo — agregado en la primera ronda de wireframing).

| Elemento | Detalle |
|---|---|
| Barras | Una por opción, cantidad de estudiantes que la eligieron — mismo color sólido que su caja en `#stage-pregunta-opciones` (sin ícono), la correcta remarcada con un borde blanco y `✓` |
| Transición a ranking | **Automática, a los pocos segundos** (confirmado con Víctor) — no es una acción del Docente ni un comando de dominio nuevo: el mismo payload de `PreguntaEnVivoCerrada` ya trae el histograma y el ranking juntos (§16 del modelo), el paso de una vista a otra es puramente de presentación, con un temporizador local en el cliente de proyección |
| Botón "Ver ranking ahora" | Adelanta la espera manualmente, para el Docente que no quiere esperar el timer — no cambia el resultado, solo la vista |

### 2.6 Proyección — ranking (`#stage-ranking`)

**Actor:** Docente (comando).
**Comando:** `AvanzarSiguientePregunta(sesion_id)` o `FinalizarSesionEnVivo(sesion_id)`.
**Query:** `ObtenerRankingDeSesion(sesion_id)` (read model `ranking_por_sesion`, §15 del modelo).

| Elemento | Detalle |
|---|---|
| Ranking | Top 3 (o top 5/10 según la cantidad de participantes — a definir en la spec de implementación), nombre + puntaje acumulado, orden descendente |
| Acción "Siguiente pregunta" | Visible si quedan preguntas — `AvanzarSiguientePregunta` → vuelve a `#stage-pregunta-sola` con la pregunta siguiente, mismos dos pasos (sola → opciones) que la anterior (hot spot 4 confirmado: dos pasos separados entre cerrar y avanzar; el histograma intermedio, §2.5, es presentación, no dominio) |
| Acción "Finalizar sesión" | Visible siempre — normalmente se usa tras la última pregunta, pero nada impide terminar antes si el Docente lo decide (mismo criterio de "medida opcional del docente" que `CerrarActividad` en período abierto, aunque acá no hay INV que lo restrinja — a diferencia de período abierto, no hay estudiantes con evaluaciones en curso que proteger) |

### 2.7 Proyección — resultado final (`#stage-final`)

**Actor:** toda el aula (observa).
**Evento:** `SesionEnVivoFinalizada`.

| Elemento | Detalle |
|---|---|
| Podio | Top 3 con el formato visual clásico (1°/2°/3°, alturas distintas) — refuerzo motivacional, no dato nuevo (ya visible en el ranking de cada cierre de pregunta) |
| Mensaje de cierre | "¡Gracias por participar!" o equivalente — sin acción, pantalla terminal |
| Fuera de alcance de este prototipo | Compartir/exportar el resultado, comparación histórica entre sesiones — no pedido por RF-08/09/10; el detalle histórico por estudiante es responsabilidad de Analytics (RF-15 a RF-23), no de este BC |

---

## 3. Pantallas — Estudiante

### 3.1 Sesiones disponibles (`#est-sesiones`)

**Actor:** Estudiante.
**Query:** sesiones en vivo en estado `EnEspera` o `EnCurso` de la Comisión donde está
inscripto (`comision_id`, §14 del modelo, corregido en la sexta ronda — cada sesión pertenece
a una única Comisión, no a "todas las de la Materia").

**Punto de entrada (confirmado con Víctor):** en la misma pantalla donde el Estudiante ya ve
las actividades de período abierto de su materia (`wireframes-actividad-evaluativa.md` §3),
las sesiones en vivo disponibles aparecen junto a esas actividades — un solo lugar donde
mirar, no una pantalla ni un ítem de menú aparte.

| Elemento | Detalle |
|---|---|
| Contexto | Mismo listado de "Actividades" de la materia que período abierto — las sesiones en vivo se distinguen por su propio `Badge` de estado |
| Tarjetas | Una por sesión visible: materia, cantidad de preguntas, `Badge` de estado (`En espera` / `En curso`) |
| Navegación | Tarjeta en `En espera` → `UnirseASesionEnVivo` → sala de espera (`#est-sala-espera`). Tarjeta en `En curso` → mismo comando, unión tardía (hot spot 2 confirmado) → entra directo a la pregunta activa si hay una abierta, o a una pantalla de espera si está entre preguntas |
| Fuera de alcance | Sesiones `Finalizada` no aparecen en este listado — no hay pantalla de "sesiones pasadas" en el modo en vivo (a diferencia de período abierto, que sí tiene revisión post-facto, RF-13); el detalle histórico de desempeño es responsabilidad de Analytics |

### 3.2 Sala de espera (`#est-sala-espera`)

**Actor:** Estudiante.
**Evento esperado:** `SesionEnVivoIniciada` (vía WebSocket) — dispara la transición automática a `#est-pregunta`.

| Elemento | Detalle |
|---|---|
| Confirmación | "¡Te uniste!" — feedback inmediato de `EstudianteUnido` |
| Conteo | Cantidad de participantes en la sala, mismo dato que ve el Docente (§2.2) |
| Mensaje | Indica mirar la proyección del aula — el Estudiante no controla el inicio, solo espera |
| Transición | Automática al recibir `SesionEnVivoIniciada` por WebSocket — sin botón, a diferencia del prototipo estático (que usa un botón deshabilitado como placeholder de esa espera) |

### 3.3 Pregunta activa (`#est-pregunta`)

**Actor:** Estudiante.
**Comando:** `ResponderPreguntaEnVivo(sesion_id, estudiante_id, pregunta_id, respuesta)`.

| Elemento | Detalle |
|---|---|
| Progreso | Barra + "Pregunta N de total", mismo patrón visual que el examen de período abierto (`wireframes-actividad-evaluativa.md` §3, `.progress-bar`) |
| Temporizador | Cuenta regresiva personal — mismo valor que ve la proyección, referencia visual del corte de aceptación (INV-AEV-08) |
| Opciones | **Tercera ronda (2026-09-17), corrige la segunda:** 4 tarjetas grandes en grilla 2×2 (`.tap-card`), pensadas para tocar con el pulgar — no la lista tipo `.opcion-row` de período abierto. **Mismo color sólido que ve la proyección** en `#stage-pregunta-opciones` (rojo/azul/amarillo/verde) — se revierte la decisión de la segunda ronda ("todo es para el docente"): el color sí se comparte entre proyección y celular, con el texto completo de la opción visible dentro de cada tarjeta en las dos pantallas |
| Interacción | **Tocar la tarjeta responde al instante** — no hay paso de selección + botón "Confirmar" separado; el toque dispara `ResponderPreguntaEnVivo` directamente y navega a `#est-resultado-pregunta`, sin pasar por ninguna pantalla de espera intermedia (**cuarta ronda**: elimina `#est-esperando`, que existía en la ronda anterior — el resultado personal no depende de que el Docente cierre la pregunta, ver §3.4). Coherente con INV-AEV-07 (un solo intento): no hay nada que reconsiderar antes de confirmar, porque no hay confirmación aparte |
| Hint | "Tocá una tarjeta para responder — un solo intento, no se puede cambiar después" (INV-AEV-07, hot spot 3 confirmado) |
| Error server-side (a especificar en la spec de implementación) | 422 con `TiempoAgotado` (INV-AEV-08, si el timer local se desincronizó y el estudiante tocó tarde), `RespuestaYaRegistrada`, `PreguntaYaCerrada` — sin cambio de comportamiento respecto de rondas anteriores, el comando `ResponderPreguntaEnVivo` no cambió, solo el gesto de UI que lo dispara |

### 3.4 Resultado de la pregunta (`#est-resultado-pregunta`)

**Actor:** Estudiante.
**Cuarta ronda (2026-09-17), confirmado con Víctor:** el resultado se muestra **de inmediato**
al tocar la tarjeta (no espera a que el Docente cierre la pregunta) y **sin ranking** — el
ranking de la sesión queda reservado exclusivamente para `#est-resultado-final` (§3.5). Esta
pantalla reemplaza tanto a `#est-esperando` como al contenido con ranking de la ronda anterior.

| Elemento | Detalle |
|---|---|
| Acierto/error | Ícono + mensaje grande ("¡Correcto!" / "Incorrecto") — resultado de `ResponderPreguntaEnVivo`, devuelto de forma síncrona por el propio comando (`BC-actividad-evaluativa-modelo.md` §13, nota bajo la tabla de comandos) — a diferencia de período abierto, que no da feedback inmediato (`BC-actividad-evaluativa-modelo.md` §5 "Sin feedback inmediato"); acá sí, es parte central de la dinámica Kahoot (RF-09) |
| Puntaje de esta pregunta | "+N puntos en esta pregunta" — resultado de la fórmula del spike RF-10 |
| Puntaje acumulado (propio) | "Llevás acumulados: X pts" — suma de todas las respuestas correctas de este Estudiante en la sesión hasta ahora (`puntaje_acumulado`, mismo dato que alimenta `ranking_por_sesion`, pero mostrado individualmente) |
| **Sin ranking** | No se muestra la posición del Estudiante respecto de sus compañeros ni el top de la sesión — corrige la ronda anterior, que sí lo mostraba acá. El Estudiante no sabe cómo va el resto hasta el final |
| Transición | Automática al recibir `SiguientePreguntaPresentada` (vuelve a `#est-pregunta`) o `SesionEnVivoFinalizada` (va a `#est-resultado-final`) — el prototipo usa dos botones como placeholder de esa espera |

### 3.5 Resultado final (`#est-resultado-final`)

**Actor:** Estudiante.
**Evento:** `SesionEnVivoFinalizada`.

| Elemento | Detalle |
|---|---|
| Posición final | "Quedaste N° con X puntos" — destacado |
| Ranking completo | Mismo top 3 (o más) que la proyección, fila propia resaltada |
| Fuera de alcance | Sin pantalla de revisión pregunta por pregunta (a diferencia de RF-13 en período abierto) — RF-08/09/10 no lo piden; si se necesitara en el futuro, es una ampliación de alcance a decidir con Víctor, no algo que este documento asuma |

---

## 4. Fuera de alcance de este prototipo (todas las pantallas)

- Sonidos, música o animaciones de celebración estilo Kahoot real — no pedido por ningún RF,
  puro polish sin requerimiento detrás.
- Modo espectador (alguien mirando la sesión sin poder responder) — no pedido.
- Códigos de acceso tipo PIN para unirse — descartado en el modelo (§10 del modelo de dominio):
  el Estudiante ya está autenticado y ve la sesión directamente en su portal, no hace falta un
  código adicional (a diferencia de Kahoot real, pensado para participantes anónimos).
- Pantalla de espera *en el proyector* separada de la sala de espera del Docente (§2.2) — se
  asume que el Docente conecta el proyector recién al iniciar, mostrando ya la primera pregunta.
  Si en la práctica hace falta una vista de proyección durante la espera (para mostrar el
  conteo de participantes en pantalla grande), es un ajuste menor a evaluar tras el primer uso
  real, no bloqueante para esta Iteración 0.

---

## 6. Ampliaciones de la Iteración 3 (`US-6.3.0`)

> Sección agregada por `US-6.3.0` (`docs/specs/inc6/US-6.3.0.md`, Issue #422). Cierra los
> huecos H1 a H9 detectados al especificar el frontend del modo en vivo contra el backend real
> (`US-6.1.x`/`US-6.2.x`) — casos que el backend admite y que §1 a §5 (aprobadas el 2026-09-17)
> no resolvían. No reabre ninguna de las seis rondas de decisión de la Iteración 0 — todas las
> pantallas de §1 a §5 quedan sin cambios, salvo el agregado puntual de H7 sobre `#stage-final`.

### 6.1 H1 — Preguntas Verdadero/Falso

**Actor:** Docente (proyección), Estudiante (celular).
**Contexto:** pregunta con `tipo = verdadero_falso` (`opciones = null`, respuesta `{valor: bool}`)
— 5 de las 36 preguntas reales del banco de "Ingeniería de Software".

| Elemento | Detalle |
|---|---|
| Proyección (variante de `#stage-pregunta-opciones`) | 2 cajas grandes "Verdadero" / "Falso" en vez de 4 — colores `b` (azul) y `c` (amarillo), **no** rojo/verde, para no sugerir cuál es la correcta antes de cerrar la pregunta |
| Estudiante (variante de `#est-pregunta`) | 2 tarjetas táctiles, mismos colores `b`/`c` que la proyección — mismo criterio de §3.3 (color compartido entre proyección y celular) |
| Histograma (variante de `#stage-histograma`) | 2 barras en vez de 4, misma paleta |
| Transiciones | Idénticas al flujo estándar (`MostrarOpcionesDeLaPregunta` → responder → `CerrarPreguntaActual` → histograma → ranking) — sin comando ni evento nuevo |
| Errores | Los mismos de §3.3 (`TiempoAgotado`, `RespuestaYaRegistrada`, `PreguntaYaCerrada`) — el tipo de pregunta no cambia el comando `ResponderPreguntaEnVivo`, solo la forma de la respuesta enviada |

### 6.2 H2 — Preguntas con 3 opciones (y con más de 4, caso no presente en los datos reales)

**Actor:** Docente (proyección), Estudiante (celular).
**Contexto:** el backend exige ≥ 2 opciones y no fija un máximo — 10 de las 36 preguntas reales
tienen 3.

| Elemento | Detalle |
|---|---|
| Grilla de 3 | Toma los colores `a`, `b`, `c` en orden; la tercera ocupa el ancho completo de la grilla (en vez de quedar una celda vacía) |
| Grilla de más de 4 | Los colores se repiten cíclicamente (`a, b, c, d, a, b, …`) — caso no presente en `preguntas_gestion.json`, se documenta para no dejarlo indefinido si aparece en el futuro |
| Transiciones / errores | Idénticos a §2.4/§3.3 — sin cambio de comando |

### 6.3 H3 — Pantalla del Estudiante entre "pregunta presentada" y "opciones mostradas"

**Pantalla nueva:** `#est-espera-opciones`.
**Actor:** Estudiante.
**Evento esperado:** el equivalente de `MostrarOpcionesDeLaPregunta` visto por el Estudiante
(vía WebSocket) — dispara la transición automática a `#est-pregunta`.

| Elemento | Detalle |
|---|---|
| Contenido | "Pregunta N de total" + el enunciado completo (mismo texto que el Docente ya ve en `#stage-pregunta-sola`) + mensaje "Esperá a que el Docente muestre las opciones" |
| Por qué hace falta | §3.1 mencionaba "una pantalla de espera si está entre preguntas" sin dibujarla — el Docente tiene dos pasos manuales (§2.3) entre mostrar la pregunta y mostrar las opciones; durante esa ventana el Estudiante no tenía ninguna pantalla definida |
| Transición | Automática, sin botón — mismo criterio que `#est-sala-espera` (§3.2) |
| Errores | Ninguno propio — pantalla puramente de espera, no dispara comandos |

### 6.4 H4 — Estudiante que no respondió y la pregunta se cerró

**Pantalla nueva:** `#est-sin-respuesta` (variante "cierre").
**Actor:** Estudiante.

| Elemento | Detalle |
|---|---|
| Mensaje | "Se cerró la pregunta — no respondiste (+0)" |
| Puntaje acumulado | "Llevás acumulados: X pts" — mismo dato que `#est-resultado-pregunta` (§3.4), sin cambio (no suma ni resta nada) |
| Por qué hace falta | Desde la cuarta ronda de la Iteración 0, `#est-esperando` fue eliminada (el resultado ahora es inmediato al responder) — pero eso dejó sin pantalla al Estudiante que **no** llega a responder antes de `CerrarPreguntaActual` |
| Transición | Automática a `#est-espera-opciones`/`#est-pregunta` (siguiente pregunta) o `#est-resultado-final` (fin de sesión) — mismo patrón que `#est-resultado-pregunta` |
| Errores | Ninguno propio |

### 6.5 H5 — Tiempo agotado al tocar

**Misma pantalla que H4** (`#est-sin-respuesta`, variante "tiempo"), mensaje distinto.
**Actor:** Estudiante.

| Elemento | Detalle |
|---|---|
| Mensaje | "Se acabó el tiempo antes de tu respuesta (+0)" |
| Por qué hace falta | §3.3 menciona el 422 `TiempoAgotado` (INV-AEV-08, cuando el timer local del Estudiante se desincronizó y tocó tarde) sin pantalla que lo muestre |
| Diferencia con H4 | H4 es el Docente cerrando la pregunta antes de que el Estudiante toque; H5 es el propio toque del Estudiante llegando tarde al servidor — mismo resultado visual, origen distinto |
| Transiciones / errores | Iguales a H4 — esta pantalla **es** la reacción al error 422, no genera uno nuevo |

### 6.6 H6 — Recuperar una sesión ya creada (Docente)

**Bloque nuevo**, dentro de `ComisionDetalleDocente.tsx` (pantalla existente y aprobada,
`US-ADJ-26`, wireframe propio en `wireframes-portal-entrada.md`) — no una pantalla nueva de
este documento. Este prototipo agrega una muestra del bloque (`#doc-comision-sesiones`), sin
repetir la pantalla completa de detalle de Comisión.

| Elemento | Detalle |
|---|---|
| Actor | Docente |
| Query | Listado de sesiones en vivo de la Comisión en estado `EnEspera`/`EnCurso` (`US-6.3.2`, `GET /sesiones-en-vivo`) |
| Contenido | Bloque "Sesiones en vivo activas": una fila por sesión (fecha/hora de creación, cantidad de preguntas, `Badge` de estado) + botón "Continuar" |
| Por qué hace falta | La sesión solo se llega a ver justo después de crearla (`#doc-sala-espera` → proyección); si el Docente cierra la pestaña o se cae el navegador no hay forma de volver |
| Transición | "Continuar" navega a `#doc-sala-espera` si `EnEspera`, o a la proyección de la pregunta actual si `EnCurso` (recupera el estado completo con `US-6.3.3`) — mismas pantallas de siempre, sin comando nuevo |
| Errores | Sesiones `Finalizada` no aparecen en el bloque — mismo criterio que `#est-sesiones` (§3.1) |

### 6.7 H7 — Salida de la pantalla terminal

**Elemento agregado a `#stage-final`** (única modificación sobre una pantalla ya aprobada,
explícitamente permitida por esta US).

| Elemento | Detalle |
|---|---|
| Actor | Docente |
| Contenido | Enlace discreto "‹ Volver a la Comisión" — tipografía chica, esquina superior, fuera del foco visual central (contraste bajo deliberado: no compite con el podio ni forma parte de lo que ve el aula) |
| Por qué hace falta | §2.7 decía "sin acción, pantalla terminal" — el Docente quedaba sin forma de salir de la proyección salvo cerrar la pestaña |
| Transición | Navega a `ComisionDetalleDocente` (mismo destino que "Continuar" en H6) |
| Errores | Ninguno |

### 6.8 H8 — Estado de conexión

**Elemento transversal** — no una pantalla nueva, un indicador que aplica a toda pantalla que
depende del canal WebSocket.

| Elemento | Detalle |
|---|---|
| Actor | Docente y Estudiante |
| Alcance | Docente: sala de espera y las 5 pantallas `stage-*`. Estudiante: sala de espera, espera de opciones, pregunta activa, sin respuesta, resultado de pregunta |
| Contenido | Chip discreto "Reconectando…" (esquina superior) |
| Comportamiento | Aparece al perder la conexión, desaparece al recuperarla — **nunca bloquea la pantalla ni oculta contenido** (no es un modal, no interrumpe la dinámica del aula) |
| Por qué hace falta | Ninguna pantalla de §1 a §5 decía qué ve el usuario si se cae el WebSocket |
| Demostración en el prototipo | Sobre 2 pantallas representativas (`#stage-pregunta-opciones`, `#est-pregunta`) con un botón que alterna el estado — no se duplica en las 12 pantallas restantes, la regla es la misma |

### 6.9 H9 — Sin participantes / menos de 3

**Elemento** — variante de contenido de `#stage-ranking`, `#stage-final` y
`#est-resultado-final` (§2.6, §2.7, §3.5), no una pantalla nueva de flujo distinto.

| Elemento | Detalle |
|---|---|
| Actor | toda el aula (observa) |
| Contenido | Se muestran tantos puestos como participantes haya (1 o 2, no se fuerzan 3 filas vacías) |
| Caso 0 participantes | "Nadie participó" — caso límite (sesión finalizada sin que nadie respondiera nunca) |
| Por qué hace falta | §2.6/§2.7 asumían un Top 3 completo — una sesión con pocos Estudiantes unidos (grupo chico, prueba, primeras respuestas de una sesión recién iniciada) rompía ese supuesto |
| Demostración en el prototipo | Variante navegable del ranking (`#stage-ranking-pocos`, 2 participantes) — no se duplica en cada pantalla de ranking, la regla es la misma en las tres |

---

## 7. Próximo paso

Prototipo navegable (§0, HTML) y esta spec listos para la revisión de Víctor — pasa a
aprobación explícita en el comentario de cierre del Issue #380 (DoD tipo `UX`,
`WORKFLOW-DESARROLLO.md` §2). Una vez aprobado, junto con el modelo de dominio ya aprobado
(`BC-actividad-evaluativa-modelo.md` §§10-18, Issue #379), es el input completo de las specs
US-IEDD de las Iteraciones 1 y 2 (`docs/plans/inc6/inc6-candidatas.md`) — y cierra la
Iteración 0 del Incremento 6.

**Ampliación de la Iteración 3 (`US-6.3.0`, §6):** pasa a aprobación explícita de Víctor en el
comentario de cierre del Issue #422, incluida la validación de legibilidad en el dispositivo
real (celular y proyector) que exige el gate de diseño para este escenario (`CLAUDE.md`
§"Gate de diseño UX"). Una vez aprobada, es el input completo de `US-6.3.5` a `US-6.3.9`.

**Decisión de Víctor (2026-09-22):** la validación en dispositivo real de §6 se difiere al
momento de implementar `US-6.3.5` a `US-6.3.9` (frontend real, no el prototipo estático) — no
bloquea el arranque del backend (`US-6.3.1` a `US-6.3.3`) ni el resto de la Iteración 3. La
aprobación explícita en el Issue #422 sigue pendiente hasta ese momento.
