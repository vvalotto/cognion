@US-4.1.3
Feature: Estudiante ve "Mi desempeño" (US-4.1.3)
  Como Estudiante
  Quiero ver mi desempeño en una materia elegida, con resumen acumulado y detalle por
  evaluación
  Para saber cómo me está yendo en la cursada sin pedírselo al docente (RF-15)

  @frontend @happy-path
  Scenario: Estudiante con una sola materia y evaluaciones finalizadas
    Given un Estudiante autenticado que cursa una sola materia, con evaluaciones finalizadas
    When entra a /analytics/mi-desempeno
    Then ve el resumen acumulado y el detalle por evaluación de esa materia, sin selector

  @frontend @happy-path
  Scenario: Estudiante con más de una materia
    Given un Estudiante autenticado que cursa dos materias
    When entra a /analytics/mi-desempeno y cambia la materia seleccionada
    Then el resumen y el detalle se actualizan para la materia recién elegida

  @frontend @edge-case
  Scenario: Materia sin evaluaciones finalizadas
    Given un Estudiante autenticado sin evaluaciones finalizadas en la materia elegida
    When ve la pantalla
    Then ve el mensaje de estado vacío, sin resumen ni lista

  @frontend @security
  Scenario: Acceso sin rol Estudiante
    Given un Docente autenticado
    When intenta entrar a /analytics/mi-desempeno
    Then es redirigido (RequireRole), no ve la pantalla
