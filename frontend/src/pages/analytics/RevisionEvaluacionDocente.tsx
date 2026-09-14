import { useEffect, useState } from "react"
import { useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { obtenerRevision, type RevisionEvaluacionResponse } from "@/lib/actividad-evaluativa-api"
import { RevisionEvaluacionContenido } from "@/pages/actividad-evaluativa/RevisionEvaluacionContenido"

/** Drill-down 2° de "Desempeño por comisión" — revisión completa vista por el Docente (`US-ADJ-48`, RF-20). */
export function RevisionEvaluacionDocente() {
  const { materiaId, comisionId, estudianteId, evaluacionId } = useParams<{
    materiaId: string
    comisionId: string
    estudianteId: string
    evaluacionId: string
  }>()

  const [revision, setRevision] = useState<RevisionEvaluacionResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!evaluacionId) return undefined
    const controller = new AbortController()
    setError(null)
    setRevision(null)
    obtenerRevision(evaluacionId, controller.signal)
      .then(setRevision)
      .catch((err) => {
        if (err instanceof DOMException && err.name === "AbortError") return
        setError("No se pudo cargar la revisión de esta evaluación. Intentá de nuevo más tarde.")
      })
    return () => controller.abort()
  }, [evaluacionId])

  return (
    <div className="mx-auto max-w-2xl">
      <Breadcrumb
        items={[
          { label: "Analytics" },
          { label: "Desempeño por comisión", to: "/analytics/desempeno-por-comision" },
          {
            label: "Detalle del estudiante",
            to: `/analytics/desempeno-por-comision/materias/${materiaId}/comisiones/${comisionId}/estudiantes/${estudianteId}`,
          },
          { label: "Revisión" },
        ]}
      />
      <h1 className="text-lg font-semibold">Revisión completa</h1>

      {error && (
        <div
          role="alert"
          className="mt-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          <p className="font-medium">{error}</p>
        </div>
      )}

      {!error && revision !== null && (
        <RevisionEvaluacionContenido
          revision={revision}
          etiquetaRespuestaPropia="Respuesta del estudiante"
        />
      )}
    </div>
  )
}
