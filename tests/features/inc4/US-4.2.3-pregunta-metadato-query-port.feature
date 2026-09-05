@US-4.2.3
Feature: Consulta de metadatos de pregunta para Analytics (US-4.2.3)
  Como Equipo de desarrollo
  Quiero el puerto de consulta y el adapter que le permiten a Analytics conocer la unidad
  temática y el tema de cada pregunta respondida, sin importar código de Banco de Preguntas
  Para que US-4.2.4 pueda agregar la tasa de error por tema que pide el Docente (RF-17)

  @happy-path
  Scenario: Lote de preguntas existentes
    Given 3 preguntas con unidad_tematica/tema distintos
    When PreguntaMetadatoConsultaPort.obtener_metadatos([id1, id2, id3]) se invoca
    Then devuelve un dict con las 3 entradas, cada una con su unidad_tematica/tema correcto

  @edge-case
  Scenario: Lote con un id inexistente
    Given 2 preguntas existentes y 1 id que no corresponde a ninguna
    When se invoca obtener_metadatos con los 3 ids
    Then el dict resultado tiene 2 entradas, sin lanzar error por el id faltante

  @edge-case
  Scenario: Lote vacío
    When se invoca obtener_metadatos([])
    Then devuelve un dict vacío

  @edge-case
  Scenario: Pregunta eliminada (baja lógica) igual aparece en el resultado
    Given una pregunta con activa=false y sus metadatos de unidad_tematica/tema
    When se invoca obtener_metadatos incluyendo su id
    Then el dict resultado incluye esa entrada — el metadato no depende del estado activa
