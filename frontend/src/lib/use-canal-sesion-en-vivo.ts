import { useEffect, useRef, useState } from "react"
import {
  CanalSesionEnVivo,
  type EstadoCanal,
  type MensajeSesionEnVivo,
  type WebSocketFactory,
} from "@/lib/canal-sesion-en-vivo"

/** Cada cuánto se resincroniza con el servidor mientras la pantalla está visible (hallazgo #7). */
export const RESINCRONIZAR_CADA_MS = 10_000
/** Evita rearmar la conexión varias veces seguidas (vuelven juntos `visibilitychange`, `pageshow`…). */
const MINIMO_ENTRE_RECONEXIONES_MS = 2_000

/**
 * Crea y cierra el canal WebSocket de una sesión en vivo dentro del ciclo de vida de React —
 * el socket se crea en `useEffect`, nunca en el render (lección `US-ADJ-20`: un recurso con
 * ciclo de vida creado en el render se rompe con el doble montaje de `StrictMode`, invisible a
 * Vitest, solo se verifica en `npm run dev` real).
 *
 * Además resincroniza (hallazgo #7 de la revisión manual, Safari en iOS congela el WebSocket al
 * bloquearse la pantalla): al volver la página a primer plano o recuperar la red rearma la conexión
 * (`onReconectado` se dispara al abrir), y cada `RESINCRONIZAR_CADA_MS` con la pantalla visible llama
 * a `onReconectado` como red de seguridad. `onReconectado` debe recalcular con el estado del servidor
 * sin retroceder la pantalla.
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

    let ultimaReconexion = 0
    function alVolver() {
      if (document.visibilityState === "hidden") return
      const ahora = Date.now()
      if (ahora - ultimaReconexion < MINIMO_ENTRE_RECONEXIONES_MS) return
      ultimaReconexion = ahora
      canal.reconectarAhora()
    }
    document.addEventListener("visibilitychange", alVolver)
    window.addEventListener("pageshow", alVolver)
    window.addEventListener("online", alVolver)
    const intervalo = setInterval(() => {
      if (document.visibilityState !== "hidden") onReconectadoRef.current()
    }, RESINCRONIZAR_CADA_MS)

    return () => {
      document.removeEventListener("visibilitychange", alVolver)
      window.removeEventListener("pageshow", alVolver)
      window.removeEventListener("online", alVolver)
      clearInterval(intervalo)
      canal.cerrar()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sesionId, crearWebSocket])

  return estado
}
