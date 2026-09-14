@US-ADJ-44
Feature: Docente consulta el desempeño de una Comisión completa (US-ADJ-44)
  Como Docente
  Quiero ver de un vistazo el % de aciertos acumulado y las actividades pendientes de cada
  estudiante de una Comisión, con acceso al detalle de una evaluación puntual
  Para priorizar a quién atender sin revisar comisión por comisión ni estudiante por
  estudiante (RF-20)

  @happy-path
  Scenario: Comisión con estudiantes en distinto estado
    Given una comisión con un estudiante con 2 Evaluacion finalizadas y otro sin ninguna
    And una actividad abierta ahora, visible a la comisión, que el segundo estudiante no rindió
    When un Docente hace GET /analytics/materias/X/comisiones/C1/desempeno
    Then recibe 200 con el primero mostrando su porcentaje acumulado y 0 pendientes
    And el segundo aparece con "Sin datos" (null) y 1 actividad pendiente

  @edge-case
  Scenario: Comisión sin ninguna evaluación finalizada
    Given una comisión cuyos estudiantes nunca finalizaron ninguna Evaluacion
    When un Docente consulta su desempeño
    Then recibe 200 con todos los estudiantes en "Sin datos"

  @error-case
  Scenario: Comisión que no pertenece a la materia
    Given una comisión de otra materia
    When un Docente hace GET /analytics/materias/X/comisiones/{esa comisión}/desempeno
    Then recibe 422

  @error-case
  Scenario: Sin autenticación
    Given una request sin JWT válido
    When hace GET /analytics/materias/X/comisiones/C1/desempeno
    Then recibe 401

  @error-case
  Scenario: Rol distinto de Docente
    Given un Estudiante autenticado
    When hace GET /analytics/materias/X/comisiones/C1/desempeno
    Then recibe 403

  @happy-path
  Scenario: Drill-down a la revisión de una evaluación ajena
    Given una Evaluacion Finalizada de un Estudiante que no es quien hace la request
    When un Docente hace GET /evaluaciones/{id}/revision
    Then recibe 200 con el detalle completo, igual que si la pidiera el propio Estudiante

  @error-case
  Scenario: Rol distinto de Docente ni Estudiante dueño pide la revisión ajena
    Given una Evaluacion Finalizada de un Estudiante
    When un Administrador hace GET /evaluaciones/{id}/revision
    Then recibe 403
