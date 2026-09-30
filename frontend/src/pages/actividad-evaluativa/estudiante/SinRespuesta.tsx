import { Card } from "@/components/ui/card"
import { Acumulado } from "./Acumulado"
import type { VistaEstudiante } from "./vista-estudiante"

/** Sin respuesta (`#est-sin-respuesta`): pregunta cerrada (H4) o tiempo agotado al tocar (H5). */
export function SinRespuesta({ vista }: { vista: VistaEstudiante }) {
  const porTiempo = vista.motivoSinRespuesta === "tiempo"
  return (
    <Card className="mx-auto mt-10 max-w-md p-6 text-center">
      <div className="text-4xl" aria-hidden="true">
        ⏱️
      </div>
      <h1 className="mt-2 text-lg font-semibold">
        {porTiempo ? "Se acabó el tiempo" : "Se cerró la pregunta"}
      </h1>
      <p className="mt-1 text-sm text-muted-foreground">
        {porTiempo ? "Se acabó el tiempo antes de tu respuesta (+0)" : "No respondiste (+0)"}
      </p>
      <Acumulado puntaje={vista.puntajeAcumulado} />
    </Card>
  )
}
