import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { iniciarEvaluacion, reanudarEvaluacion } from "@/lib/actividad-evaluativa-api"

/** Pantalla "Evaluación suspendida" del Estudiante (`#est-suspendida`, `US-3.4.6`). */
export function EvaluacionSuspendida() {
  const { actividadId } = useParams<{ actividadId: string }>()
  const navigate = useNavigate()

  const [evaluacionId, setEvaluacionId] = useState<string | null>(null)
  const [cantidadRespondidas, setCantidadRespondidas] = useState(0)

  useEffect(() => {
    if (!actividadId) return
    let cancelado = false

    iniciarEvaluacion(actividadId).then((resultado) => {
      if (cancelado) return
      setEvaluacionId(resultado.id)
      setCantidadRespondidas(resultado.preguntasRespondidas.length)
    })

    return () => {
      cancelado = true
    }
  }, [actividadId])

  async function continuar() {
    if (!evaluacionId) return
    await reanudarEvaluacion(evaluacionId)
    navigate(`/mis-actividades/actividades/${actividadId}/rendir`)
  }

  return (
    <div className="mx-auto max-w-md">
      <h1 className="text-lg font-semibold">Evaluación en pausa</h1>

      <Card className="mt-4 p-6 text-center">
        <p className="mb-2 text-3xl">⏸</p>
        <p className="text-sm text-muted-foreground">
          Guardamos tus {cantidadRespondidas} respuestas. Tocá "Continuar" para retomar desde
          donde quedaste — el resto del set no cambia.
        </p>
        <Button className="mt-5 w-full" disabled={!evaluacionId} onClick={() => void continuar()}>
          Continuar
        </Button>
      </Card>

      <div
        role="note"
        className="mt-4 rounded-lg border border-amber-400/40 bg-amber-400/10 px-3 py-2 text-sm"
      >
        <p className="font-medium">También pasa automáticamente</p>
        <p className="mt-1 text-muted-foreground">
          Si te quedás inactivo sin responder por un rato largo, el sistema pausa la evaluación
          por vos — no perdés nada, solo tenés que volver a tocar "Continuar".
        </p>
      </div>
    </div>
  )
}
