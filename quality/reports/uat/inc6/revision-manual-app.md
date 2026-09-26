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
