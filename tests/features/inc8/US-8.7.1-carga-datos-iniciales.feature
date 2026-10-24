@US-8.7.1
Feature: Carga de datos iniciales desde archivos JSON o Markdown (US-8.7.1)
  Como docente que instala Cognión en su equipo
  Quiero cargar mis materias y mis preguntas desde mis archivos con un solo comando
  Para que la versión de producción nazca con mi contenido sin cargarlo desde la pantalla

  @carga @happy-path
  Scenario: Base sin la materia
    Given una base sin la materia "Ingeniería de Software"
    And un archivo JSON con esa materia y 2 preguntas válidas
    When se ejecuta el comando de carga sobre el archivo
    Then existen la materia, su banco y las 2 preguntas
    And el resumen informa 2 cargadas, 0 omitidas y 0 con error
    And la salida es 0

  @idempotencia
  Scenario: Segunda ejecución con el mismo archivo
    Given el archivo ya fue cargado una vez
    When se ejecuta de nuevo el comando de carga sobre el mismo archivo
    Then no se agrega ninguna pregunta
    And el resumen informa 0 cargadas y 2 omitidas por duplicadas
    And la salida es 0

  @validacion @invariante
  Scenario: Pregunta de opción múltiple sin opción correcta
    Given un archivo JSON con 3 preguntas y la segunda no tiene ninguna opción correcta
    When se ejecuta el comando de carga sobre el archivo
    Then no se carga ninguna pregunta de ese archivo
    And el mensaje indica la posición 2 y el motivo
    And la salida es distinta de cero

  @carpeta @aislamiento
  Scenario: Carpeta con dos archivos y uno con error
    Given una carpeta con un archivo válido y un archivo con una pregunta inválida
    When se ejecuta el comando de carga sobre la carpeta
    Then el archivo válido se carga completo
    And el archivo inválido no carga nada
    And la salida es distinta de cero

  @simular
  Scenario: Modo simular
    Given un archivo JSON válido
    When se ejecuta el comando de carga con --simular
    Then se informa lo que se cargaría
    And la base queda idéntica

  @materia-existente
  Scenario: Materia ya creada desde la pantalla
    Given una materia "Gestión de Proyectos" creada previamente con una pregunta
    When se carga un archivo con esa materia y una pregunta nueva
    Then se reutiliza la materia y su banco
    And el banco queda con 2 preguntas

  @errores-entrada
  Scenario Outline: Entrada inválida
    Given <entrada>
    When se ejecuta el comando de carga
    Then se muestra un mensaje claro sin traza
    And la salida es distinta de cero

    Examples:
      | entrada                          |
      | un archivo con JSON malformado   |
      | una ruta que no existe           |

  @markdown
  Scenario: Cuestionario Markdown con materia indicada
    Given un cuestionario Markdown "Riesgos - Cuestionario.md" de 20 preguntas con unidad "09 – Incertidumbre"
    When se ejecuta el comando de carga con --materia "Gestión de Proyectos"
    Then se cargan 20 preguntas en la materia "Gestión de Proyectos"
    And la unidad temática es "09 – Incertidumbre" y el tema es "Riesgos"
    And la dificultad "Fácil", "Medio" y "Difícil" queda como bajo, medio y alto
    And la importancia es la misma que la dificultad

  @markdown @carpeta
  Scenario: Carpeta con los 17 cuestionarios
    Given una carpeta con los 17 cuestionarios y otros archivos Markdown que no son cuestionarios
    When se ejecuta el comando de carga con --materia "Gestión de Proyectos"
    Then se cargan 340 preguntas en una única materia
    And los archivos que no terminan en " - Cuestionario.md" se ignoran
    And una segunda ejecución omite las 340

  @markdown @errores-entrada
  Scenario: Markdown sin --materia
    Given un cuestionario Markdown válido
    When se ejecuta el comando de carga sin --materia
    Then se muestra un error claro antes de leer el archivo
    And la salida es distinta de cero

  @markdown @validacion
  Scenario Outline: Cuestionario Markdown con datos inválidos
    Given un cuestionario Markdown con <defecto>
    When se ejecuta el comando de carga con --materia "Gestión de Proyectos"
    Then ese archivo no carga nada y el mensaje indica la pregunta
    And la salida es distinta de cero

    Examples:
      | defecto                                        |
      | un Nivel desconocido                           |
      | una respuesta correcta que no está en opciones |
      | una pregunta sin Nivel                         |
