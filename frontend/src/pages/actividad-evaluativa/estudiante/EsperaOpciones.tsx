import { Card } from "@/components/ui/card"
import { BarraPregunta } from "./BarraPregunta"
import type { VistaEstudiante } from "./vista-estudiante"

/** Pregunta presentada, opciones todavía ocultas (`#est-espera-opciones`, H3): sin botón. */
export function EsperaOpciones({ vista }: { vista: VistaEstudiante }) {
  return (
    <div className="mx-auto max-w-md">
      <BarraPregunta indice={vista.indice} cantidadPreguntas={vista.cantidadPreguntas} />
      <h1 className="mt-2 mb-5 text-[17px] font-semibold">{vista.enunciado}</h1>
      <Card className="p-6 text-center">
        <div className="text-4xl" aria-hidden="true">
          ⏳
        </div>
        <p role="status" className="mt-2 text-sm text-muted-foreground">
          Esperá a que el Docente muestre las opciones.
        </p>
      </Card>
    </div>
  )
}
