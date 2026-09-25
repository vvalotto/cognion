import { Card } from "@/components/ui/card"
import { Acumulado } from "./Acumulado"
import type { VistaEstudiante } from "./vista-estudiante"

/**
 * Resultado de la pregunta (`#est-resultado-pregunta`, §3.4): inmediato y sin ranking. Tras recargar el
 * servidor no devuelve el acierto de esa pregunta: se muestra solo el acumulado.
 */
export function ResultadoPregunta({ vista }: { vista: VistaEstudiante }) {
  const resultado = vista.resultado
  return (
    <Card className="mx-auto mt-10 max-w-md p-6 text-center">
      <div className="text-4xl" aria-hidden="true">
        {resultado === null ? "📝" : resultado.esCorrecta ? "✅" : "❌"}
      </div>
      <h1 className="mt-2 text-lg font-semibold">
        {resultado === null ? "Ya respondiste" : resultado.esCorrecta ? "¡Correcto!" : "Incorrecto"}
      </h1>
      {resultado !== null && (
        <p className="mt-1 text-sm text-muted-foreground">+ {resultado.puntaje} puntos en esta pregunta</p>
      )}
      <Acumulado puntaje={vista.puntajeAcumulado} />
    </Card>
  )
}
