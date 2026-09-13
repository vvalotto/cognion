# language: es
@US-ADJ-43
Característica: Selectores públicos de Materia/Comisión para autoregistro

  Como un Estudiante sin cuenta, autoregistrándome desde la pantalla de autoregistro
  quiero que el selector de Materia→Comisión se pueble sin necesitar un JWT
  para poder elegir mi comisión antes de tener cuenta

  Nota: las pantallas en sí (`AutoregistroPerfil`/`Docente`/`Estudiante`/`Exito`) son
  frontend puro — sin comportamiento backend propio distinto del ya cubierto por
  `US-ADJ-41`/`42` — cubiertas por tests de integración de Vitest con el router real
  (`frontend/src/router.test.tsx`, bloque "Autoregistro (US-ADJ-43)"), mismo criterio que
  `US-ADJ-40`. Este feature cubre el único comportamiento backend nuevo de esta US: los dos
  endpoints públicos de consulta para el selector.

  Antecedentes:
    Dado que existe una Materia con al menos una Comisión activa

  Escenario: Listar materias sin JWT
    Cuando se hace GET /identidad/autoregistro/materias sin Authorization
    Entonces la respuesta es 200 OK
    Y la lista incluye la materia con solo los campos id y nombre

  Escenario: Listar comisiones de una materia sin JWT
    Cuando se hace GET /identidad/autoregistro/materias/{materia_id}/comisiones sin Authorization
    Entonces la respuesta es 200 OK
    Y la lista incluye la comisión con solo los campos id y horario

  Escenario: Materia sin comisiones devuelve lista vacía
    Dado que existe una Materia sin ninguna Comisión
    Cuando se hace GET /identidad/autoregistro/materias/{materia_id}/comisiones sin Authorization
    Entonces la respuesta es 200 OK
    Y la lista está vacía

  Escenario: Materia inexistente devuelve lista vacía, sin distinguir el caso
    Cuando se hace GET /identidad/autoregistro/materias/{materia_id}/comisiones con un id que no existe
    Entonces la respuesta es 200 OK
    Y la lista está vacía
