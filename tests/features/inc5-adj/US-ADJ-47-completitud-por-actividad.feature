@US-ADJ-47
Feature: Docente consulta la completitud de una actividad puntual (US-ADJ-47)
  Como Docente
  Quiero ver, para una actividad puntual, el estado de cada estudiante del roster aplicable
  (sin iniciar, en curso, suspendida o finalizada)
  Para saber quién todavía no rindió antes de que cierre el período, sin revisar estudiante
  por estudiante (RF-23)

  @happy-path
  Scenario: Actividad restringida a una comisión, estados mixtos
    Given una actividad restringida a la comisión C1 con 4 estudiantes
    And 1 finalizó, 1 está en curso, 1 suspendió y 1 nunca inició
    When un Docente hace GET /analytics/actividades/X/completitud
    Then recibe 200 con resumen finalizadas 1, en_curso 1, suspendidas 1, sin_iniciar 1
    And el detalle lista los 4 estudiantes con su estado exacto

  @happy-path
  Scenario: Actividad sin restricción de comisión
    Given una actividad sin comisiones_ids visible a toda la materia con 2 comisiones
    When un Docente consulta su completitud
    Then el roster del detalle incluye los estudiantes de ambas comisiones

  @error-case
  Scenario: Actividad inexistente
    Given un actividad_id que no corresponde a ninguna actividad
    When un Docente consulta su completitud
    Then recibe 404

  @error-case
  Scenario: Rol distinto de Docente
    Given un Estudiante autenticado
    When hace GET /analytics/actividades/X/completitud
    Then recibe 403
