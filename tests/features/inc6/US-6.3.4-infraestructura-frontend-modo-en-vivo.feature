@US-6.3.4
Feature: Infraestructura de frontend del modo en vivo (US-6.3.4)
  Como Equipo de desarrollo
  Quiero el cliente API, el canal WebSocket y las rutas del modo en vivo montados en el frontend
  Para tener la base sobre la que se construyen las seis US de pantallas siguientes (US-6.3.5 a US-6.3.9)

  @infra @happy-path
  Scenario: El cliente API llama a los endpoints con JWT y mapea a camelCase
    Given una sesión guardada con token
    When se invoca cualquier función de sesion-en-vivo-api
    Then la request lleva el Authorization y la respuesta llega en camelCase

  @infra @happy-path
  Scenario: El canal recibe y tipa los mensajes
    Given un canal conectado a una sesión
    When llega un mensaje pregunta_cerrada
    Then el callback lo recibe tipado y en camelCase

  @infra @happy-path
  Scenario: El canal se reconecta y pide re-sincronizar
    Given un canal conectado que se cae
    When se restablece la conexión
    Then dispara onReconectado y el estado vuelve a conectado

  @infra @happy-path
  Scenario: El backoff es exponencial con tope
    Given una conexión que falla repetidamente
    When se reintenta
    Then los intervalos son 1, 2, 4, 8 y 10 segundos como máximo

  @infra @error-case
  Scenario: Token inválido corta la conexión
    Given un canal con un token vencido
    When el servidor cierra con 1008
    Then no reintenta, limpia la sesión y navega a /login

  @infra @error-case
  Scenario: Un mensaje desconocido no rompe
    Given un canal conectado
    When llega un mensaje con un tipo que el cliente no conoce
    Then se ignora y los siguientes se procesan

  @infra @happy-path
  Scenario: El cleanup cierra el socket
    Given un componente que usa el hook
    When se desmonta
    Then el socket queda cerrado y no reintenta

  @infra @happy-path
  Scenario: Las rutas están protegidas por rol
    Given un Estudiante
    When abre la ruta de proyección del Docente
    Then RequireRole lo rechaza

  @infra @happy-path
  Scenario: La proyección no usa el layout con menú
    Given la ruta de proyección
    When se renderiza
    Then usa StageLayout y no muestra el menú de navegación
