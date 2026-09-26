import { useCallback, useEffect, useRef, useState } from "react"
import { Link, useNavigate, useParams } from "react-router"

import { IndicadorConexion } from "@/components/IndicadorConexion"
import { ApiError } from "@/lib/api-client"
import type { MensajeSesionEnVivo } from "@/lib/canal-sesion-en-vivo"
import {
  avanzarPregunta,
  cerrarPregunta,
  finalizarSesion,
  mostrarOpciones,
  obtenerEstadoSesion,
  obtenerRankingSesion,
} from "@/lib/sesion-en-vivo-api"
import { useCanalSesionEnVivo } from "@/lib/use-canal-sesion-en-vivo"
import { StageFinal } from "./proyeccion/StageFinal"
import { StageHistograma } from "./proyeccion/StageHistograma"
import { StagePreguntaOpciones } from "./proyeccion/StagePreguntaOpciones"
import { StagePreguntaSola } from "./proyeccion/StagePreguntaSola"
import { StageRanking } from "./proyeccion/StageRanking"
import {
  aplicarMensaje,
  calcularVista,
  type EtapaProyeccion,
  type VistaProyeccion,
  verRanking,
} from "./proyeccion/vista-proyeccion"

const ESPERA_MENSAJE_MS = 2000

/**
 * Contenedor de la proyección del modo en vivo: calcula la etapa desde `GET estado` (al montar y
 * al reconectar) y la mantiene con los mensajes del canal. Pregunta sola/con opciones
 * (`US-6.3.6`); histograma, ranking y podio final (`US-6.3.7`).
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
      let nueva = calcularVista(estado)
      if (nueva === null) {
        void navigate(`/sesiones-en-vivo/${sesionId}/sala`)
        return
      }
      if (nueva.etapa === "finalizada") {
        const ranking = await obtenerRankingSesion(sesionId, controladorRef.current?.signal)
        nueva = { ...nueva, resultado: { respuestaCorrecta: null, distribucion: [], ranking } }
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

  const onVerRanking = useCallback(() => {
    setVista((actual) => (actual ? verRanking(actual) : actual))
  }, [])

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
      {/* Salir sin afectar la sesión (revisión manual 2026-09-26): se retoma desde "Sesiones en vivo
          activas". El podio final ya tiene su propio "Volver a la Comisión" (H7). */}
      {vista.etapa !== "finalizada" && (
        <Link
          to={`/actividad-evaluativa/comisiones/${vista.comisionId}`}
          className="absolute top-4 left-4 text-sm"
          style={{ color: "rgba(255,255,255,0.45)" }}
        >
          ‹ Salir
        </Link>
      )}
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
          onCerrarPregunta={() => void ejecutar(cerrarPregunta, "histograma")}
        />
      )}
      {vista.etapa === "histograma" && (
        <StageHistograma vista={vista} onVerRanking={onVerRanking} />
      )}
      {vista.etapa === "ranking" && (
        <StageRanking
          vista={vista}
          enviando={enviando}
          onSiguiente={() => void ejecutar(avanzarPregunta, "pregunta-sola")}
          onFinalizar={() => void ejecutar(finalizarSesion, "finalizada")}
        />
      )}
      {vista.etapa === "finalizada" && <StageFinal vista={vista} />}
      {errorAccion && (
        <p role="alert" className="fixed bottom-4 left-1/2 -translate-x-1/2 text-lg text-amber-300">
          No se pudo enviar el comando. Reintentá.
        </p>
      )}
    </div>
  )
}
