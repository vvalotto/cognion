import { useCallback, useEffect, useRef, useState } from "react"
import { Link, useParams } from "react-router"

import { IndicadorConexion } from "@/components/IndicadorConexion"
import { Card } from "@/components/ui/card"
import { ApiError } from "@/lib/api-client"
import type { MensajeSesionEnVivo } from "@/lib/canal-sesion-en-vivo"
import {
  obtenerEstadoSesion,
  obtenerRankingSesion,
  responderPregunta,
  unirseASesion,
} from "@/lib/sesion-en-vivo-api"
import { obtenerUsuarioId } from "@/lib/session"
import { useCanalSesionEnVivo } from "@/lib/use-canal-sesion-en-vivo"
import { EsperaOpciones } from "./estudiante/EsperaOpciones"
import { PreguntaActiva } from "./estudiante/PreguntaActiva"
import { ResultadoFinal } from "./estudiante/ResultadoFinal"
import { ResultadoPregunta } from "./estudiante/ResultadoPregunta"
import { SalaEsperaEstudiante } from "./estudiante/SalaEsperaEstudiante"
import { SinRespuesta } from "./estudiante/SinRespuesta"
import {
  aplicarMensajeEstudiante,
  calcularVistaEstudiante,
  registrarRespuesta,
  sincronizarVistaEstudiante,
  type VistaEstudiante,
} from "./estudiante/vista-estudiante"

/**
 * Contenedor del modo en vivo del Estudiante: al abrirse se une (reunión idempotente, INV-AEV-06 —
 * recargar no necesita guardar nada en el cliente) y calcula la etapa con `GET estado`; después la
 * mantiene con el canal. Sala (`US-6.3.8`); pregunta, resultado y final (`US-6.3.9`).
 */
export function SesionEnVivoEstudiante() {
  const { sesionId } = useParams<{ sesionId: string }>()
  const [vista, setVista] = useState<VistaEstudiante | null>(null)
  const [noDisponible, setNoDisponible] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [errorRespuesta, setErrorRespuesta] = useState(false)
  const controladorRef = useRef<AbortController | null>(null)
  const enviandoRef = useRef(false)
  const vistaRef = useRef<VistaEstudiante | null>(null)
  vistaRef.current = vista

  const recalcular = useCallback(
    async (opciones: { trasRechazo?: boolean } = {}) => {
      if (!sesionId) return
      const signal = controladorRef.current?.signal
      try {
        const estado = await obtenerEstadoSesion(sesionId, signal)
        let nueva = calcularVistaEstudiante(estado, opciones)
        if (nueva.etapa === "finalizada") {
          nueva = { ...nueva, ranking: await obtenerRankingSesion(sesionId, signal) }
        }
        setVista((actual) => sincronizarVistaEstudiante(actual, nueva))
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) setNoDisponible(true)
      }
    },
    [sesionId],
  )

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

  const onMensaje = useCallback(
    (mensaje: MensajeSesionEnVivo) => {
      const actual = vistaRef.current
      if (!actual) return
      const siguiente = aplicarMensajeEstudiante(actual, mensaje)
      if (siguiente === "recalcular") {
        void recalcular()
        return
      }
      setVista(siguiente)
    },
    [recalcular],
  )

  const estadoCanal = useCanalSesionEnVivo(sesionId ?? "", onMensaje, () => void recalcular())

  async function responder(contenido: Record<string, unknown>) {
    const actual = vistaRef.current
    if (!sesionId || !actual || enviandoRef.current) return
    enviandoRef.current = true
    setEnviando(true)
    setErrorRespuesta(false)
    const signal = controladorRef.current?.signal
    try {
      const respuesta = await responderPregunta(sesionId, actual.preguntaId, contenido, signal)
      setVista((v) => (v ? registrarRespuesta(v, respuesta) : v))
    } catch (err) {
      if (signal?.aborted) return
      if (err instanceof ApiError && err.status === 422) {
        // TiempoAgotado / RespuestaYaRegistrada / PreguntaYaCerrada: el estado decide la pantalla.
        await recalcular({ trasRechazo: true })
      } else if (err instanceof ApiError && err.status === 404) {
        // Sin participación: se vuelve a unir (idempotente) y se recalcula.
        await unirseASesion(sesionId, signal).catch(() => undefined)
        await recalcular()
      } else {
        setErrorRespuesta(true)
      }
    } finally {
      enviandoRef.current = false
      setEnviando(false)
    }
  }

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
      {vista.etapa === "espera-opciones" && <EsperaOpciones vista={vista} />}
      {vista.etapa === "pregunta" && (
        <PreguntaActiva vista={vista} enviando={enviando} onResponder={(c) => void responder(c)} />
      )}
      {vista.etapa === "resultado" && <ResultadoPregunta vista={vista} />}
      {vista.etapa === "sin-respuesta" && <SinRespuesta vista={vista} />}
      {vista.etapa === "finalizada" && (
        <ResultadoFinal ranking={vista.ranking ?? []} estudianteId={obtenerUsuarioId()} />
      )}
      {errorRespuesta && (
        <p role="alert" className="mt-4 text-center text-sm text-destructive">
          No se pudo enviar la respuesta. Tocá de nuevo.
        </p>
      )}
    </div>
  )
}
