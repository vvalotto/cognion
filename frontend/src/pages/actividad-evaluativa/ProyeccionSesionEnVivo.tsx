import { useCallback, useEffect, useRef, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { IndicadorConexion } from "@/components/IndicadorConexion"
import { ApiError } from "@/lib/api-client"
import type { MensajeSesionEnVivo } from "@/lib/canal-sesion-en-vivo"
import {
  cerrarPregunta,
  mostrarOpciones,
  obtenerEstadoSesion,
} from "@/lib/sesion-en-vivo-api"
import { useCanalSesionEnVivo } from "@/lib/use-canal-sesion-en-vivo"
import { StagePreguntaOpciones } from "./proyeccion/StagePreguntaOpciones"
import { StagePreguntaSola } from "./proyeccion/StagePreguntaSola"
import {
  aplicarMensaje,
  calcularVista,
  type EtapaProyeccion,
  type VistaProyeccion,
} from "./proyeccion/vista-proyeccion"

const ESPERA_MENSAJE_MS = 2000

/**
 * Contenedor de la proyección del modo en vivo (`US-6.3.6`): calcula la etapa desde `GET estado`
 * (al montar y al reconectar) y la mantiene con los mensajes del canal. `US-6.3.7` agrega las
 * etapas de resultado sobre este mismo contenedor.
 */
export function ProyeccionSesionEnVivo() {
  const { sesionId } = useParams<{ sesionId: string }>()
  const navigate = useNavigate()

  const [vista, setVista] = useState<VistaProyeccion | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [errorAccion, setErrorAccion] = useState(false)

  const controladorRef = useRef<AbortController | null>(null)
  const etapaRef = useRef<EtapaProyeccion | null>(null)
  const recalculoRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const enviandoRef = useRef(false)
  const vistaRef = useRef<VistaProyeccion | null>(null)
  vistaRef.current = vista
  etapaRef.current = vista?.etapa ?? null

  const cancelarRecalculo = useCallback(() => {
    if (recalculoRef.current) {
      clearTimeout(recalculoRef.current)
      recalculoRef.current = null
    }
  }, [])

  const recalcular = useCallback(async () => {
    if (!sesionId) return
    try {
      const estado = await obtenerEstadoSesion(sesionId, controladorRef.current?.signal)
      const nueva = calcularVista(estado)
      if (nueva === null) {
        void navigate(`/sesiones-en-vivo/${sesionId}/sala`)
        return
      }
      setVista(nueva)
    } catch {
      // Sin estado no hay nada que recalcular; el próximo mensaje o reconexión reintenta.
    }
  }, [sesionId, navigate])

  useEffect(() => {
    const controller = new AbortController()
    controladorRef.current = controller
    void recalcular()
    return () => {
      controller.abort()
      cancelarRecalculo()
    }
  }, [recalcular, cancelarRecalculo])

  const onMensaje = useCallback(
    (mensaje: MensajeSesionEnVivo) => {
      const actual = vistaRef.current
      if (!actual) return
      const siguiente = aplicarMensaje(actual, mensaje, Date.now())
      if (siguiente === "recalcular") {
        void recalcular()
        return
      }
      cancelarRecalculo()
      setVista(siguiente)
    },
    [recalcular, cancelarRecalculo],
  )

  const estadoCanal = useCanalSesionEnVivo(sesionId ?? "", onMensaje, () => void recalcular())

  async function ejecutar(accion: typeof mostrarOpciones, etapaEsperada: EtapaProyeccion) {
    if (!sesionId || enviandoRef.current) return
    enviandoRef.current = true
    setEnviando(true)
    setErrorAccion(false)
    try {
      await accion(sesionId, controladorRef.current?.signal)
      // La etapa siguiente llega por el canal; si no llega, se recalcula con el estado.
      cancelarRecalculo()
      recalculoRef.current = setTimeout(() => {
        if (etapaRef.current !== etapaEsperada) void recalcular()
      }, ESPERA_MENSAJE_MS)
    } catch (err) {
      if (controladorRef.current?.signal.aborted) return
      if (err instanceof ApiError && err.status === 422) {
        await recalcular()
      } else {
        setErrorAccion(true)
      }
    } finally {
      enviandoRef.current = false
      setEnviando(false)
    }
  }

  if (vista === null) {
    return (
      <p className="p-8 text-xl" style={{ color: "var(--stage-muted)" }}>
        Cargando…
      </p>
    )
  }

  return (
    <div className="relative">
      <div className="absolute top-4 right-4">
        <IndicadorConexion estado={estadoCanal} />
      </div>
      {vista.etapa === "pregunta-sola" && (
        <StagePreguntaSola
          vista={vista}
          enviando={enviando}
          onMostrarOpciones={() => void ejecutar(mostrarOpciones, "pregunta-opciones")}
        />
      )}
      {vista.etapa === "pregunta-opciones" && (
        <StagePreguntaOpciones
          vista={vista}
          enviando={enviando}
          onCerrarPregunta={() => void ejecutar(cerrarPregunta, "cerrada")}
        />
      )}
      {(vista.etapa === "cerrada" || vista.etapa === "finalizada") && (
        <p className="p-8 text-xl" style={{ color: "var(--stage-muted)" }}>
          Resultado — pendiente de la etapa de resultado (US-6.3.7)
        </p>
      )}
      {errorAccion && (
        <p role="alert" className="fixed bottom-4 left-1/2 -translate-x-1/2 text-lg text-amber-300">
          No se pudo enviar el comando. Reintentá.
        </p>
      )}
    </div>
  )
}
