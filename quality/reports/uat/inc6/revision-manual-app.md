# Revisión manual de la app — hallazgos (2026-09-26)

Revisión/validación completa de Víctor sobre `develop` (rama `fix/revision-manual-app`), con datos reales
(`tests/uat/datos-reales/sembrar.py`) y de prueba (`valid-*`), desde la Mac, iPhone y iPad.

**Criterio acordado:** hallazgo chico (visual, texto, navegación, bug acotado sin impacto funcional relevante) →
se resuelve directo, un commit por hallazgo; si toca `src/` se avisa. Hallazgo con impacto importante en el
backend o cambio funcional relevante → US de ajuste (`US-ADJ-58` en adelante) con spec e Issue.

| # | Rol / pantalla | Hallazgo | Tipo | Resolución |
|---|---|---|---|---|
| 1 | Administrador / Materias → detalle | Al seleccionar una materia, mostrar junto al estado la lista de sus Comisiones | Mejora frontend | `VerMateria.tsx`: fila "Comisiones" con horario (link al detalle), cantidad de Docentes asignados y estado; incluye inactivas (`GET /materias/{id}/comisiones?incluir_inactivas=true`) |
| 2 | Administrador / Materias → detalle | La presentación del #1 no convence: hacerla más elegante | Mejora frontend | `VerMateria.tsx` rediseñado con el lenguaje de las demás pantallas: título con estado, tres tarjetas de resumen (preguntas activas, comisiones activas "N de M", estudiantes inscriptos) y tabla de Comisiones (horario, Docentes por nombre, estudiantes, estado, ver detalle; fila clickeable) |
| 3 | Administrador / Materias → detalle y menú | Dar de alta las Comisiones desde el detalle de la Materia y quitar "Comisiones" del menú del Administrador | Cambio de navegación, frontend | `VerMateria.tsx`: "+ Nueva Comisión" y acciones por fila (ver, editar, eliminar, activar). Sale "Comisiones" del menú y de la home del Administrador; se borra la pantalla `Comisiones.tsx` y su ruta `/comisiones`. Las pantallas de una Comisión (detalle, nueva, editar, eliminar) cuelgan de la Materia: breadcrumb "Materias › {materia} › …" (`useNombreMateria`), "Volver a la materia", y crear/eliminar vuelven al detalle de la Materia. "Materias" queda resaltado en el menú dentro de `/comisiones/*`. Helper de test `fetchConMaterias` |
| 4 | Docente / sesión en vivo — sala y proyección | (a) No se puede iniciar la sesión sin estudiantes unidos; (b) falta una opción para cancelar o salir de la sesión | (a) frontend + regla de backend; (b) "Salir" frontend, "Cancelar" funcional | **Resuelto en frontend:** "Iniciar sesión" deshabilitado con 0 participantes ("Esperá a que se una al menos un estudiante…", reemplaza el "podés iniciar igual" de H9) y "‹ Salir" en la sala y en la proyección (vuelve a la Comisión sin tocar la sesión; se retoma con "Continuar"). Circuito E2E 7 reescrito, 10/10. **A US de ajuste — `US-ADJ-58` (Issue #445):** comando "Cancelar sesión en vivo" (descartar una sesión no iniciada) + invariante de backend de no iniciar sin participantes |
