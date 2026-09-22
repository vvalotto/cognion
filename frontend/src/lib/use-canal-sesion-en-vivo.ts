import { useEffect, useRef, useState } from "react"
import {
  CanalSesionEnVivo,
  type EstadoCanal,
  type MensajeSesionEnVivo,
  type WebSocketFactory,
} from "@/lib/canal-sesion-en-vivo"

/**
 * Crea y cierra el canal WebSocket de una sesión en vivo dentro del ciclo de vida de React —
 * el socket se crea en `useEffect`, nunca en el render (lección `US-ADJ-20`: un recurso con
 * ciclo de vida creado en el render se rompe con el doble montaje de `StrictMode`, invisible a
 * Vitest, solo se verifica en `npm run dev` real).
 */
export function useCanalSesionEnVivo(
  sesionId: string,
  onMensaje: (mensaje: MensajeSesionEnVivo) => void,
  onReconectado: () => void,
  crearWebSocket?: WebSocketFactory,
): EstadoCanal {
  const [estado, setEstado] = useState<EstadoCanal>("desconectado")
  const onMensajeRef = useRef(onMensaje)
  const onReconectadoRef = useRef(onReconectado)
  onMensajeRef.current = onMensaje
  onReconectadoRef.current = onReconectado

  useEffect(() => {
    const canal = new CanalSesionEnVivo(
      sesionId,
      (mensaje) => onMensajeRef.current(mensaje),
      () => onReconectadoRef.current(),
      setEstado,
      crearWebSocket,
    )
    canal.conectar()

    return () => {
      canal.cerrar()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sesionId, crearWebSocket])

  return estado
}
