import { useEffect, useState } from "react"
import { Link, useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { listarActividades } from "@/lib/actividad-evaluativa-api"
import { obtenerDesempenoDeEstudiante, type DesempenoEstudianteResponse } from "@/lib/analytics-api"
import {
  armarFilas,
  DesempenoResumenDetalle,
  type FilaDesempeno,
} from "@/pages/analytics/DesempenoResumenDetalle"

/** Drill-down 1° de "Desempeño por comisión" (`#doc-desempeno-comision`, `US-ADJ-48`, RF-20). */
export function DesempenoPorComisionDetalleEstudiante() {
  const navigate = useNavigate()
  const { materiaId, comisionId, estudianteId } = useParams<{
    materiaId: string
    comisionId: string
    estudianteId: string
  }>()

  const [desempeno, setDesempeno] = useState<DesempenoEstudianteResponse | null>(null)
  const [filas, setFilas] = useState<FilaDesempeno[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!materiaId || !estudianteId) return undefined
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

  function verRevision(evaluacionId: string) {
    navigate(
      `/analytics/desempeno-por-comision/materias/${materiaId}/comisiones/${comisionId}/estudiantes/${estudianteId}/evaluaciones/${evaluacionId}/revision`,
    )
  }

  return (
    <div className="mx-auto max-w-2xl">
      <Breadcrumb
        items={[
          { label: "Reportes", to: "/analytics" },
          { label: "Desempeño por comisión", to: "/analytics/desempeno-por-comision" },
          { label: "Detalle del estudiante" },
        ]}
      />
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Detalle del estudiante</h1>
        <Link
          to={`/analytics/desempeno-por-comision/materias/${materiaId}/comisiones/${comisionId}/estudiantes/${estudianteId}/evolucion`}
          className="text-sm font-medium text-primary hover:underline"
        >
          Ver evolución temporal
        </Link>
      </div>

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
          onFilaClick={verRevision}
        />
      )}
    </div>
  )
}
