import { useEffect, useState } from "react"
import { useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { obtenerRevision, type RevisionEvaluacionResponse } from "@/lib/actividad-evaluativa-api"
import { RevisionEvaluacionContenido } from "@/pages/actividad-evaluativa/RevisionEvaluacionContenido"

/** Pantalla "Revisión al finalizar" del Estudiante (`#est-revision`, `US-3.4.7`). */
export function RevisionEvaluacion() {
  const { evaluacionId } = useParams<{ evaluacionId: string }>()
  const [revision, setRevision] = useState<RevisionEvaluacionResponse | null>(null)

  useEffect(() => {
    if (!evaluacionId) return undefined
    const controller = new AbortController()
    obtenerRevision(evaluacionId, controller.signal)
      .then((resultado) => setRevision(resultado))
      .catch(() => {})
    return () => controller.abort()
  }, [evaluacionId])

  if (revision === null) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  return (
    <div className="mx-auto max-w-2xl">
      <Breadcrumb
        items={[
          { label: "Mis materias", to: "/mis-actividades/materias" },
          { label: "Revisión" },
        ]}
      />
      <h1 className="text-lg font-semibold">Revisión completa</h1>

      <RevisionEvaluacionContenido revision={revision} etiquetaRespuestaPropia="Tu respuesta" />
    </div>
  )
}
