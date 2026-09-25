import type { ReactNode } from "react"

/** Barra de progreso + "Pregunta N de total" (§3.3), compartida por la espera y la pregunta. */
export function BarraPregunta({
  indice,
  cantidadPreguntas,
  extra,
}: {
  indice: number
  cantidadPreguntas: number
  extra?: ReactNode
}) {
  const progreso = cantidadPreguntas > 0 ? ((indice + 1) / cantidadPreguntas) * 100 : 0
  return (
    <div>
      <div className="mb-1.5 h-1.5 overflow-hidden rounded-full bg-border">
        <div className="h-full bg-accent" style={{ width: `${progreso}%` }} />
      </div>
      <div className="flex justify-between text-sm text-muted-foreground">
        <span>
          Pregunta {indice + 1} de {cantidadPreguntas}
        </span>
        {extra}
      </div>
    </div>
  )
}
