# Hipótesis de Ensayo: IA, Ingeniería de Software y Human-in-the-Loop

## 1. Propósito

Este documento formula una hipótesis conceptual del ensayo que subyace al
experimento AtaraxiaDive y resume qué parte de esa hipótesis cuenta ya con
evidencia empírica inicial.

La tesis no es que la IA "resuelve" la Ingeniería de Software, sino que
reconfigura dónde está el trabajo de mayor valor y vuelve más visible la
necesidad de rigor en especificación, arquitectura, calidad constructiva y
capitalización del aprendizaje.

---

## 2. Hipótesis central

**Hipótesis del ensayo**

> La IA potencia a la Ingeniería de Software en múltiples dimensiones, pero no
> sustituye al ingeniero ni vuelve prescindible el juicio humano. Cuanto mayor
> es la capacidad de automatización de la implementación, mayor es la necesidad
> de intervención humana en la comprensión del dominio, la especificación del
> comportamiento, la evaluación de trade-offs, el control de calidad
> constructiva y la transformación del trabajo realizado en conocimiento
> reusable.

En esta formulación:

- la IA aumenta productividad en artefactos micro;
- la ingeniería aporta estructura, criterio y validación;
- el `human-in-the-loop` sigue siendo esencial;
- el valor diferencial no está solo en producir código, sino en producir
  sistemas más correctos, mantenibles, útiles y enseñables.

---

## 3. Desarrollo conceptual de la hipótesis

### 3.1 La IA desplaza el cuello de botella

Si parte de la implementación puede derivarse desde especificaciones, entonces
la dificultad principal deja de estar en "escribir código" y se concentra aún
más en:

- entender el dominio;
- modelar correctamente sus conceptos y fronteras;
- explicitar invariantes, precondiciones y postcondiciones;
- verificar que la arquitectura y el código preserven esas decisiones.

La IA no elimina estos problemas. Los vuelve más determinantes.

### 3.2 La calidad relevante cambia de centro

En un contexto con IA, la calidad de uso sigue siendo importante, pero cobra
mayor centralidad la **calidad constructiva**, porque:

- una mala especificación puede amplificarse rápidamente en muchos artefactos;
- una mala decisión arquitectónica puede replicarse a gran escala;
- una inconsistencia documental puede contaminar código, tests y reportes;
- una deuda técnica no explicitada puede crecer silenciosamente detrás de una
  apariencia de productividad.

### 3.3 La automatización sin memoria no alcanza

La productividad local no equivale a capacidad de ingeniería. Para que la IA
produzca valor sostenible, el proceso debe dejar memoria explícita:

- decisiones;
- trazabilidad;
- criterios de calidad;
- retrospección;
- aprendizajes formalizados.

Sin esa memoria, la IA acelera producción; con esa memoria, puede acelerar
aprendizaje.

### 3.4 El human-in-the-loop no es un parche

En esta visión, el `human-in-the-loop` no aparece solo para corregir errores del
modelo, sino como componente estructural del sistema de trabajo. Su papel es
irreductible, al menos por ahora, en funciones como:

- reformular el problema;
- arbitrar ambigüedades semánticas;
- decidir entre alternativas con trade-offs no locales;
- detectar inconsistencias entre artefactos;
- interpretar el valor real de una métrica;
- convertir experiencia de proyecto en conocimiento transferible.

---

## 4. Diseño experimental implícito

AtaraxiaDive funciona como laboratorio para contrastar esta hipótesis mediante
un entorno compuesto por cuatro piezas coordinadas:

- **IEDD** como marco para la cadena dominio → modelo → especificación →
  arquitectura → implementación.
- **Claude Dev Kit** como mecanismo de implementación táctica por historia.
- **Software Limpio** como sistema de verificación programática.
- **CM / gestión de configuración** como memoria viva de la evolución del
  proyecto y del experimento.

La hipótesis no se evalúa preguntando si la IA "genera buen código", sino si el
conjunto metodología + herramientas + intervención humana permite:

- sostener coherencia entre artefactos;
- controlar la deuda técnica;
- producir aprendizaje acumulable;
- mejorar la calidad de las decisiones de ingeniería;
- mantener al humano como agente de gobierno del proceso.

---

## 5. Qué se ha demostrado hasta el momento

La evidencia acumulada en AtaraxiaDive a lo largo de SP1–SP7 (32 HITOs, 22 ADRs,
6 baselines, 10 SP-ADJ, UAT completo de SP6 y despliegue en Fly.io) no cierra
toda la hipótesis, pero permite afirmar resultados parciales con solidez creciente.

### 5.1 Se confirmó que la automatización requiere calibración humana continua

En SP1–SP2 fue necesario adaptar el Dev Kit a la arquitectura hexagonal BC-first,
corregir paths, quality gates y criterios del flujo. La evidencia de SP3–SP7
profundiza y amplía este resultado:

- **HITO-17 (SP3):** un dataset real de la BA 2025 reveló inconsistencias del
  dominio —orden de grilla, algoritmo FAAS, empates— que ningún test formal
  detectó. Los datos reales actúan como oráculo empírico no sustituible.
- **HITO-27 (SP5):** la deriva documental emerge silenciosamente cuando
  especificación e implementación avanzan en paralelo; solo se detectó con gates
  de consistencia y revisión humana explícita.
- **HITO-30, 31, 32 (SP6):** los tests unitarios, de integración y BDD derivan
  silenciosamente cuando no se ejecutan en cada PR de un proyecto LLM. La suite
  acumuló deuda que requirió una sesión completa de saneamiento humano para
  llegar a 1140/1140 pasando.
- **SP-ADJ-03 a SP-ADJ-11:** diez iteraciones de ajuste técnico post-baseline
  demuestran que la calibración no es un evento puntual de inicio sino una
  actividad recurrente del ciclo.
- **UAT SP6:** hallazgos en los flows F-08 y F-09 —corrección del algoritmo FAAS
  por categoría+género, corrección del callback `on_finalizada` en el router HTTP—
  no eran detectables por ningún test automatizado existente.

La IA y sus herramientas no operan solas en un proyecto real: requieren diseño y
gobierno humano del entorno en cada baseline.

### 5.2 Se confirmó que la productividad no elimina la necesidad de ingeniería

Los HITOs de SP1 y SP2 ya mostraban fricción BDD + Event Sourcing, artefactos
faltantes por compresión de contexto, y decisiones arquitectónicas emergentes.
SP3–SP7 consolidan y extienden este resultado:

- **HITO-15 (SP3):** las proyecciones CQRS emergen como consecuencia estructural
  inevitable del Event Sourcing, no como elección libre. El ingeniero debe
  reconocer el patrón y decidir cuándo materializarlo.
- **HITO-19 (SP4):** el cierre de incremento es la unidad correcta para leer
  deuda estructural acumulada; sin esa lectura, la deuda queda distribuida e
  invisible.
- **HITO-20 (SP4):** invariantes correctos pueden ser incompletos ante variantes
  no anticipadas del dominio (SPE_2X50, SPE_4X50, etc.). El UAT fue el único
  oráculo que lo detectó.
- **HITO-26 (SP5):** la cobertura asimétrica del Event Storming —realizado solo
  para BC Competencia— dejó BCs de soporte subrepresentados, generando
  especificaciones incompletas que emergieron como deuda en SP5 y SP6.
- **HITO-29 (SP5):** especificar después de implementar (spec-validatoria)
  introduce sesgos invisibles en la cobertura de casos; anti-patrón identificado
  formalmente.
- **HITO-32 (SP6):** el nivel BDD es el de mayor deriva semántica en proyectos
  IEDD+LLM; la IA genera con frecuencia tests con invariantes incorrectos que
  pasan pero no verifican lo que deberían.
- **ArchitectAnalyst BL-001→BL-006:** la distancia al Main Sequence del BC
  Competencia bajó de D=0.61 a D=0.46 a lo largo del proyecto —mejora medible
  atribuible a decisiones de ingeniería explícitas, no a generación automática.

La productividad táctica es real y sostenida. La ingeniería de interpretación,
corrección y consolidación es igualmente real y no decreció.

### 5.3 Se confirmó que la calidad constructiva necesita instrumentación explícita

La experiencia acumulada de SP1 a SP7 confirma que los quality gates no son un
adorno operativo sino dispositivos de gobierno del proceso:

- **HITO-11 (SP2):** un quality gate (DesignReviewer) catalizó la decisión
  arquitectónica de separar BC Competencia, documentada en ADR-012. Sin la
  métrica, la decisión no tenía palanca.
- **HITO-22 (SP4):** el Event Store puede sostener integridad criptográfica
  (hash SHA-256) con la misma traza, sin persistencia adicional. Evidencia
  de que la arquitectura de calidad sale de las decisiones de dominio.
- **HITO-23, 24 (SP4):** la auditoría solo se vuelve operable cuando puede
  navegarse desde read models y UI; la exportación como read model portable
  elimina la necesidad de persistencia paralela.
- **HITO-25 (SP4):** la restricción técnica offline-first produjo mejor
  arquitectura que si hubiera sido una decisión ad-hoc; las restricciones
  forzadas derivan en abstracciones más limpias.
- **SP6 cierre:** DesignReviewer BL-006 — 0 CRITICAL, 287 WARNING. La suite
  1140/1140 pasando. Métricas medibles y comparables entre baselines.

El sistema de quality gates es condición necesaria, no suficiente: detecta
problemas, pero su interpretación y resolución son trabajo de ingeniería.

### 5.4 Se confirmó que el experimento produce conocimiento formalizable y acumulable

A lo largo de SP1–SP7, el proyecto generó:

- **32 HITOs** con hipótesis explícitas, observaciones y relaciones entre
  decisiones, fricciones y resultados.
- **22 ADRs** que documentan decisiones arquitectónicas con contexto, opciones
  consideradas y consecuencias.
- **6 baselines** (BL-001 a BL-006) con reportes de ArchitectAnalyst comparables
  entre sí.
- **Metodología IEDD formalizada:** marco conceptual, hipótesis, template de US,
  política de UAT — reusables fuera del proyecto.
- **Plan de métricas estructurales:** radon CC/MI/Halstead/raw sobre `src/` como
  punto de partida para análisis cuantitativo.
- **Piloto de trazabilidad navegable:** cadena RF → US → código → test en grafo
  D3 interactivo — evidencia de que la trazabilidad puede materializarse sin
  herramientas externas.

El proceso capitaliza aprendizaje de forma sostenida y no solo produce software.

### 5.5 Se confirmó, con mayor solidez, la necesidad estructural del human-in-the-loop

La intervención humana fue indispensable en cada subproyecto para:

- encuadrar el problema y definir el valor del experimento;
- decidir cuándo abrir un SP-ADJ y qué priorizar dentro de él;
- arbitrar waivers del UAT (F-09/F-10 de SP6) con criterio que ningun
  test automatizado puede ejercer;
- reinterpretar métricas del ArchitectAnalyst cuando las tendencias contradicen
  la intuición del dominio;
- detectar deriva documental (HITO-27) antes de que contamine implementación;
- convertir experiencia de proyecto en HITOs, ADRs y material de docencia.

**HITO-28 (SP5)** agrega un hallazgo nuevo: el testing exploratorio (vibe
coding) complementa el pipeline formal y detecta clases de defectos que los
tests estructurados no cubren. El humano como oráculo de calidad final es
irreductible, al menos en la escala actual del proyecto.

No apareció evidencia de que el entorno pudiera sostener la misma calidad sin
esa intervención. Por el contrario, los HITOs de SP6 demuestran que, sin
ejecución continua y revisión humana, los tests derivan silenciosamente hacia
una apariencia de cobertura sin validez semántica real.

---

## 6. Qué todavía no está demostrado

La hipótesis general sigue abierta en puntos estructurales:

- **Costo comparativo:** no está demostrado que este enfoque reduzca el costo
  total del ciclo de vida frente a alternativas más convencionales. No existe
  proyecto de control.
- **Calidad en operación sostenida:** v1.0.0 fue desplegado en Fly.io (SP7),
  pero no hay todavía evidencia de uso real por usuarios finales en condiciones
  de torneo.
- **Reusabilidad cuantificada:** el conocimiento producido (HITOs, ADRs,
  metodología) tiene potencial de reutilización, pero no está medido cuánto
  retrabajo requiere aplicarlo en un segundo proyecto.
- **Aislamiento empírico de causas:** no está aislado qué parte del resultado
  se debe a IEDD, cuál a las herramientas (Dev Kit, quality gates), cuál al
  perfil del humano experto y cuál a la capacidad del modelo LLM.
- **Reducción de dependencia humana:** no está demostrado que la dependencia
  del human-in-the-loop disminuya a medida que el entorno se especializa, ni
  que deba hacerlo.

Lo alcanzado hasta SP7 es una **validación de factibilidad, coherencia y
sostenibilidad en escala de proyecto individual**, no una demostración final
de superioridad ni de generalización.

---

## 7. Tesis provisional del experimento

Con la evidencia reunida hasta SP7, la tesis provisional puede formularse así:

> La IA no reemplaza la Ingeniería de Software; la desplaza hacia actividades de
> mayor nivel y vuelve más valiosas la especificación rigurosa, la verificación
> arquitectónica, la memoria del proceso y la producción deliberada de
> aprendizaje. En ese contexto, el `human-in-the-loop` no es una concesión
> transitoria, sino la condición actual para que la automatización sea útil,
> controlable y epistemológicamente fértil.

Esta tesis se sostiene y se fortaleció con la evidencia de SP3–SP7: el proyecto
llegó a `v1.0.0` con UAT completo (10/10 flows), 0 CRITICAL en DesignReviewer,
1140 tests pasando y despliegue en producción — sin reducir la dependencia de
ingeniería humana, sino reorganizándola hacia actividades de mayor valor.

---

## 8. Preguntas abiertas para la siguiente contrastación empírica

Las preguntas de SP2 sobre sostenibilidad, full-stack y consistencia entre
artefactos fueron parcialmente respondidas en SP3–SP7. Las preguntas que
permanecen abiertas o emergen nuevas son:

- **Operación real:** ¿qué hallazgos produce el uso del sistema en un torneo
  real con usuarios no técnicos? ¿Qué clase de defectos solo emergen en
  producción sostenida?
- **Reusabilidad del conocimiento:** ¿cuánto de la metodología IEDD, los ADRs y
  los HITOs puede transferirse a un segundo proyecto sin retrabajo significativo?
- **Segundo proyecto como control:** ¿el enfoque produce resultados comparables
  o mejores en un dominio diferente, con otro desarrollador o con menor nivel
  de expertise previo?
- **Reducción de fricción del ecosistema:** ¿el overhead de ~18 min por US
  (HITO-5) puede reducirse con un entorno más especializado, o es un piso
  estructural?
- **Deriva en horizontes largos:** ¿la consistencia documental y arquitectónica
  se sostiene más allá de 7 subproyectos, o requiere revisiones periódicas
  formales?

---

## 9. Conclusión

La hipótesis del ensayo no sostiene que la IA haga innecesaria la ingeniería,
sino lo contrario: cuanto más capaz es la IA de producir implementación, más
importante se vuelve la disciplina que define qué construir, cómo verificarlo,
cómo mantener coherencia entre decisiones y cómo convertir experiencia en
conocimiento acumulable.

AtaraxiaDive ofrece, al cierre de SP7, evidencia empírica sostenida a favor de
esta visión: 32 HITOs, 22 ADRs, 6 baselines comparables, un sistema en
producción (v1.0.0) y una metodología formalizada. La parte aún abierta es
contrastar si ese resultado se generaliza más allá de un proyecto individual,
un dominio específico y un desarrollador con expertise previo en el área.
