import { useEffect, useState } from "react"

import { Breadcrumb } from "@/components/Breadcrumb"
import { listarActividades } from "@/lib/actividad-evaluativa-api"
import { obtenerDesempenoDeEstudiante, type DesempenoEstudianteResponse } from "@/lib/analytics-api"
import { listarMaterias, type MateriaListItemResponse } from "@/lib/banco-preguntas-api"
import {
  listarComisionesPorMateria,
  listarEstudiantesDeComision,
  type ComisionResumenResponse,
  type EstudianteResumenResponse,
} from "@/lib/identidad-comisiones-api"
import {
  armarFilas,
  DesempenoResumenDetalle,
  type FilaDesempeno,
} from "@/pages/analytics/DesempenoResumenDetalle"

/** Pantalla "Desempeño por alumno" del Docente (`#doc-desempeno-alumno`, `US-4.2.5`, RF-16). */
export function DesempenoPorAlumno() {
  const [materias, setMaterias] = useState<MateriaListItemResponse[]>([])
  const [materiaId, setMateriaId] = useState<string>("")

  const [comisiones, setComisiones] = useState<ComisionResumenResponse[]>([])
  const [comisionId, setComisionId] = useState<string>("")

  const [estudiantes, setEstudiantes] = useState<EstudianteResumenResponse[]>([])
  const [estudianteId, setEstudianteId] = useState<string>("")

  const [desempeno, setDesempeno] = useState<DesempenoEstudianteResponse | null>(null)
  const [filas, setFilas] = useState<FilaDesempeno[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    listarMaterias(controller.signal)
      .then(setMaterias)
      .catch(() => {})
    return () => controller.abort()
  }, [])

  function elegirMateria(value: string) {
    setMateriaId(value)
    setComisionId("")
    setEstudiantes([])
    setEstudianteId("")
    setDesempeno(null)
    setFilas(null)
    setError(null)
  }

  function elegirComision(value: string) {
    setComisionId(value)
    setEstudianteId("")
    setDesempeno(null)
    setFilas(null)
    setError(null)
  }

  useEffect(() => {
    if (!materiaId) {
      setComisiones([])
      return undefined
    }
    const controller = new AbortController()
    listarComisionesPorMateria(materiaId, controller.signal)
      .then(setComisiones)
      .catch(() => {})
    return () => controller.abort()
  }, [materiaId])

  useEffect(() => {
    if (!comisionId) {
      setEstudiantes([])
      return undefined
    }
    const controller = new AbortController()
    listarEstudiantesDeComision(comisionId, controller.signal)
      .then(setEstudiantes)
      .catch(() => {})
    return () => controller.abort()
  }, [comisionId])

  useEffect(() => {
    if (!estudianteId) return undefined
    const controller = new AbortController()
    setError(null)
    setDesempeno(null)
    setFilas(null)
    Promise.all([
      obtenerDesempenoDeEstudiante(materiaId, estudianteId, controller.signal),
      listarActividades(materiaId, controller.signal),
    ])
      .then(([resultadoDesempeno, actividades]) => {
        const titulosPorActividad = new Map(actividades.map((a) => [a.id, a.titulo]))
        setDesempeno(resultadoDesempeno)
        setFilas(armarFilas(resultadoDesempeno, titulosPorActividad))
      })
      .catch((err) => {
        if (err instanceof DOMException && err.name === "AbortError") return
        setError("No se pudo cargar el desempeño de este estudiante. Intentá de nuevo más tarde.")
      })
    return () => controller.abort()
  }, [materiaId, estudianteId])

  return (
    <div className="mx-auto max-w-2xl">
      <Breadcrumb items={[{ label: "Analytics" }, { label: "Desempeño por alumno" }]} />
      <h1 className="text-lg font-semibold">Desempeño por alumno</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Elegí una materia, una comisión y un estudiante para ver su desempeño.
      </p>

      <div className="mt-4 grid grid-cols-3 gap-3">
        <div>
          <label htmlFor="materia" className="text-sm font-medium">
            Materia
          </label>
          <select
            id="materia"
            className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={materiaId}
            onChange={(e) => elegirMateria(e.target.value)}
          >
            <option value="">Elegí una materia</option>
            {materias.map((materia) => (
              <option key={materia.id} value={materia.id}>
                {materia.nombre}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="comision" className="text-sm font-medium">
            Comisión
          </label>
          <select
            id="comision"
            className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={comisionId}
            onChange={(e) => elegirComision(e.target.value)}
            disabled={!materiaId}
          >
            <option value="">Elegí una comisión</option>
            {comisiones.map((comision) => (
              <option key={comision.id} value={comision.id}>
                {comision.horario}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="estudiante" className="text-sm font-medium">
            Estudiante
          </label>
          <select
            id="estudiante"
            className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={estudianteId}
            onChange={(e) => setEstudianteId(e.target.value)}
            disabled={!comisionId}
          >
            <option value="">Elegí un estudiante</option>
            {estudiantes.map((estudiante) => (
              <option key={estudiante.id} value={estudiante.id}>
                {estudiante.nombre}
              </option>
            ))}
          </select>
        </div>
      </div>

      {!estudianteId && !error && (
        <p className="mt-4 text-sm text-muted-foreground">
          Elegí un estudiante para ver su desempeño.
        </p>
      )}

      {error && (
        <div
          role="alert"
          className="mt-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          <p className="font-medium">{error}</p>
        </div>
      )}

      {!error && desempeno !== null && filas !== null && (
        <DesempenoResumenDetalle
          desempeno={desempeno}
          filas={filas}
          mensajeVacio="Este estudiante todavía no finalizó ninguna evaluación de esta materia."
        />
      )}
    </div>
  )
}
