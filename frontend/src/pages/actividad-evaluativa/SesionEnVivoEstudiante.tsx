import { useCallback, useEffect, useRef, useState } from "react"
import { Link, useParams } from "react-router"

import { IndicadorConexion } from "@/components/IndicadorConexion"
import { Card } from "@/components/ui/card"
import { ApiError } from "@/lib/api-client"
import type { MensajeSesionEnVivo } from "@/lib/canal-sesion-en-vivo"
import { obtenerEstadoSesion, unirseASesion } from "@/lib/sesion-en-vivo-api"
import { useCanalSesionEnVivo } from "@/lib/use-canal-sesion-en-vivo"
import { SalaEsperaEstudiante } from "./estudiante/SalaEsperaEstudiante"
import {
  aplicarMensajeEstudiante,
  calcularVistaEstudiante,
  type VistaEstudiante,
} from "./estudiante/vista-estudiante"

/**
 * Contenedor del modo en vivo del Estudiante (`US-6.3.8`): al abrirse se une (reunión idempotente,
 * INV-AEV-06 — recargar no necesita guardar nada en el cliente) y calcula la etapa con `GET estado`;
 * después la mantiene con el canal. `US-6.3.9` agrega la pregunta, el resultado y el final.
 */
export function SesionEnVivoEstudiante() {
  const { sesionId } = useParams<{ sesionId: string }>()
  const [vista, setVista] = useState<VistaEstudiante | null>(null)
  const [noDisponible, setNoDisponible] = useState(false)
  const controladorRef = useRef<AbortController | null>(null)

  const recalcular = useCallback(async () => {
    if (!sesionId) return
    try {
      const estado = await obtenerEstadoSesion(sesionId, controladorRef.current?.signal)
      setVista(calcularVistaEstudiante(estado))
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) setNoDisponible(true)
    }
  }, [sesionId])

  useEffect(() => {
    if (!sesionId) return undefined
    const controller = new AbortController()
    controladorRef.current = controller
    async function unirseYCargar(id: string) {
      try {
        await unirseASesion(id, controller.signal)
      } catch (err) {
        if (controller.signal.aborted) return
        if (err instanceof ApiError && err.status === 404) {
          setNoDisponible(true)
          return
        }
        // 422 (sesión ya finalizada): no corta — el estado decide la etapa.
      }
      await recalcular()
    }
    void unirseYCargar(sesionId)
    return () => controller.abort()
  }, [sesionId, recalcular])

  const onMensaje = useCallback((mensaje: MensajeSesionEnVivo) => {
    setVista((actual) => (actual ? aplicarMensajeEstudiante(actual, mensaje) : actual))
  }, [])

  const estadoCanal = useCanalSesionEnVivo(sesionId ?? "", onMensaje, () => void recalcular())

  if (noDisponible) {
    return (
      <Card className="mx-auto mt-10 max-w-md p-6 text-center">
        <p role="alert" className="text-sm">
          Esta sesión ya no está disponible.
        </p>
        <Link to="/mis-actividades/materias" className="mt-3 inline-block text-sm text-primary">
          ‹ Volver a mis materias
        </Link>
      </Card>
    )
  }

  if (vista === null) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  return (
    <div>
      <div className="flex justify-end">
        <IndicadorConexion estado={estadoCanal} />
      </div>
      {vista.etapa === "sala" && (
        <SalaEsperaEstudiante totalParticipantes={vista.totalParticipantes} />
      )}
      {vista.etapa === "pregunta" && (
        <p className="mt-10 text-center text-sm text-muted-foreground">
          La sesión está en curso — pantalla de la pregunta pendiente (US-6.3.9)
        </p>
      )}
      {vista.etapa === "finalizada" && (
        <p className="mt-10 text-center text-sm text-muted-foreground">
          La sesión finalizó — resultado final pendiente (US-6.3.9)
        </p>
      )}
    </div>
  )
}
