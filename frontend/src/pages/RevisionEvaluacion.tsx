import { useEffect, useState } from "react"
import { useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import {
  obtenerRevision,
  type DetallePreguntaRevisionResponse,
  type RevisionEvaluacionResponse,
} from "@/lib/actividad-evaluativa-api"

function textoDeContenido(
  contenido: Record<string, unknown> | null,
  opciones: string[] | null,
): string {
  if (contenido === null) return "Sin responder"
  if (opciones !== null) {
    const indice = contenido["opcion_indice"]
    return typeof indice === "number" ? (opciones[indice] ?? "—") : "—"
  }
  return contenido["valor"] === true ? "Verdadero" : "Falso"
}

function ordenarDetalle(revision: RevisionEvaluacionResponse) {
  return [...revision.detalle].sort((a, b) => a.orden - b.orden)
}

function FilaRevision({ fila }: { fila: DetallePreguntaRevisionResponse }) {
  return (
    <Card className="p-4">
      <div className="flex items-start justify-between gap-3">
        <p className="font-medium">
          {fila.orden}. {fila.texto}
        </p>
        <Badge variant={fila.esCorrecta ? "revision-correcta" : "revision-incorrecta"}>
          {fila.esCorrecta ? "Correcta" : "Incorrecta"}
        </Badge>
      </div>
      <p
        className={`mt-2 text-sm ${fila.esCorrecta ? "text-emerald-700" : "text-destructive"}`}
      >
        Tu respuesta: {textoDeContenido(fila.contenidoPropio, fila.opciones)}
      </p>
      {!fila.esCorrecta && (
        <p className="mt-1 text-sm text-muted-foreground">
          Respuesta correcta: {textoDeContenido(fila.contenidoCorrecto, fila.opciones)}
        </p>
      )}
    </Card>
  )
}

/** Pantalla "Revisión al finalizar" del Estudiante (`#est-revision`, `US-3.4.7`). */
export function RevisionEvaluacion() {
  const { evaluacionId } = useParams<{ evaluacionId: string }>()
  const [revision, setRevision] = useState<RevisionEvaluacionResponse | null>(null)

  useEffect(() => {
    if (!evaluacionId) return
    let cancelado = false
    obtenerRevision(evaluacionId).then((resultado) => {
      if (!cancelado) setRevision(resultado)
    })
    return () => {
      cancelado = true
    }
  }, [evaluacionId])

  if (revision === null) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  const detalle = ordenarDetalle(revision)

  return (
    <div className="mx-auto max-w-2xl">
      <Breadcrumb
        items={[
          { label: "Mis materias", to: "/mis-actividades/materias" },
          { label: "Revisión" },
        ]}
      />
      <h1 className="text-lg font-semibold">Revisión completa</h1>

      <div className="mt-4 grid grid-cols-3 gap-3 text-center">
        <Card className="p-4">
          <p className="text-2xl font-semibold text-emerald-700">
            {revision.cantidadCorrectas}
          </p>
          <p className="text-xs text-muted-foreground">Correctas</p>
        </Card>
        <Card className="p-4">
          <p className="text-2xl font-semibold text-destructive">
            {revision.cantidadIncorrectas}
          </p>
          <p className="text-xs text-muted-foreground">Incorrectas</p>
        </Card>
        <Card className="p-4">
          <p className="text-2xl font-semibold">{revision.cantidadPreguntas}</p>
          <p className="text-xs text-muted-foreground">Total</p>
        </Card>
      </div>

      <div className="mt-4 flex flex-col gap-3">
        {detalle.map((fila) => (
          <FilaRevision key={fila.preguntaId} fila={fila} />
        ))}
      </div>
    </div>
  )
}
