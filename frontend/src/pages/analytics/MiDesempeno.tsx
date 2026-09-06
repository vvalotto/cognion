import { useEffect, useState } from "react"

import { Breadcrumb } from "@/components/Breadcrumb"
import { obtenerMiDesempeno, type DesempenoEstudianteResponse } from "@/lib/analytics-api"
import { listarActividadesVisibles } from "@/lib/actividad-evaluativa-api"
import { listarMisMaterias, type MateriaEstudianteResponse } from "@/lib/identidad-estudiante-api"
import {
  armarFilas,
  DesempenoResumenDetalle,
  type FilaDesempeno,
} from "@/pages/analytics/DesempenoResumenDetalle"

/** Pantalla "Mi desempeño" del Estudiante (`#est-desempeno`, `US-4.1.3`). */
export function MiDesempeno() {
  const [materias, setMaterias] = useState<MateriaEstudianteResponse[] | null>(null)
  const [materiaId, setMateriaId] = useState<string | null>(null)
  const [desempeno, setDesempeno] = useState<DesempenoEstudianteResponse | null>(null)
  const [filas, setFilas] = useState<FilaDesempeno[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    listarMisMaterias(controller.signal)
      .then((resultado) => {
        setMaterias(resultado)
        if (resultado.length > 0) {
          setMateriaId(resultado[0].id)
        }
      })
      .catch(() => {})
    return () => controller.abort()
  }, [])

  useEffect(() => {
    if (!materiaId) return undefined
    const controller = new AbortController()
    setError(null)
    setDesempeno(null)
    setFilas(null)
    Promise.all([
      obtenerMiDesempeno(materiaId, controller.signal),
      listarActividadesVisibles(materiaId, controller.signal),
    ])
      .then(([resultadoDesempeno, actividades]) => {
        const titulosPorActividad = new Map(actividades.map((a) => [a.id, a.titulo]))
        setDesempeno(resultadoDesempeno)
        setFilas(armarFilas(resultadoDesempeno, titulosPorActividad))
      })
      .catch((err) => {
        if (err instanceof DOMException && err.name === "AbortError") return
        setError("No se pudo cargar tu desempeño. Intentá de nuevo más tarde.")
      })
    return () => controller.abort()
  }, [materiaId])

  return (
    <div className="mx-auto max-w-2xl">
      <Breadcrumb items={[{ label: "Analytics" }, { label: "Mi desempeño" }]} />
      <h1 className="text-lg font-semibold">Mi desempeño</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Historial de tus evaluaciones de período abierto en la materia elegida.
      </p>

      {materias !== null && materias.length > 1 && (
        <div className="mt-4">
          <label htmlFor="materia" className="text-sm font-medium">
            Materia
          </label>
          <select
            id="materia"
            className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={materiaId ?? ""}
            onChange={(e) => setMateriaId(e.target.value)}
          >
            {materias.map((materia) => (
              <option key={materia.id} value={materia.id}>
                {materia.nombre}
              </option>
            ))}
          </select>
        </div>
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
          mensajeVacio="Todavía no finalizaste ninguna evaluación de esta materia."
        />
      )}
    </div>
  )
}
