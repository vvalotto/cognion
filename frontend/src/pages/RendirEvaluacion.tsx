import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import {
  finalizarEvaluacion,
  iniciarEvaluacion,
  registrarRespuesta,
  suspenderEvaluacion,
  type EvaluacionResponse,
} from "@/lib/actividad-evaluativa-api"
import { ApiError } from "@/lib/api-client"

type Seleccion = { tipo: "opcion"; indice: number } | { tipo: "vf"; valor: boolean }

function ordenarPreguntas(evaluacion: EvaluacionResponse) {
  return [...evaluacion.preguntasAsignadas].sort((a, b) => a.orden - b.orden)
}

function primerIndicePendiente(evaluacion: EvaluacionResponse): number {
  const preguntas = ordenarPreguntas(evaluacion)
  const respondidas = new Set(evaluacion.preguntasRespondidas)
  const indice = preguntas.findIndex((p) => !respondidas.has(p.preguntaId))
  return indice === -1 ? preguntas.length - 1 : indice
}

/** Traduce el `contenido` de una `Respuesta` confirmada de vuelta a `Seleccion` (`US-ADJ-12`). */
function seleccionDeContenido(contenido: Record<string, unknown>): Seleccion | null {
  if (typeof contenido.opcion_indice === "number") {
    return { tipo: "opcion", indice: contenido.opcion_indice }
  }
  if (typeof contenido.valor === "boolean") {
    return { tipo: "vf", valor: contenido.valor }
  }
  return null
}

function contenidoDeSeleccion(seleccion: Seleccion): Record<string, unknown> {
  return seleccion.tipo === "opcion"
    ? { opcion_indice: seleccion.indice }
    : { valor: seleccion.valor }
}

function mapaDeRespuestasConfirmadas(evaluacion: EvaluacionResponse): Map<string, Seleccion> {
  const mapa = new Map<string, Seleccion>()
  for (const respuesta of evaluacion.respuestasConfirmadas) {
    const seleccion = seleccionDeContenido(respuesta.contenido)
    if (seleccion) mapa.set(respuesta.preguntaId, seleccion)
  }
  return mapa
}

/** Pantalla "Rendir evaluación" del Estudiante (`#est-rendir`, `US-3.4.6`). */
export function RendirEvaluacion() {
  const { actividadId } = useParams<{ actividadId: string }>()
  const navigate = useNavigate()

  const [evaluacion, setEvaluacion] = useState<EvaluacionResponse | null>(null)
  const [respondidas, setRespondidas] = useState<Set<string>>(new Set())
  const [respuestasConfirmadas, setRespuestasConfirmadas] = useState<Map<string, Seleccion>>(
    new Map(),
  )
  const [indiceActual, setIndiceActual] = useState(0)
  const [seleccion, setSeleccion] = useState<Seleccion | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!actividadId) return undefined
    const controller = new AbortController()

    iniciarEvaluacion(actividadId, controller.signal)
      .then((resultado) => {
        if (resultado.estado === "Suspendida") {
          navigate(`/mis-actividades/actividades/${actividadId}/suspendida`, { replace: true })
          return
        }
        const mapa = mapaDeRespuestasConfirmadas(resultado)
        const indice = primerIndicePendiente(resultado)
        const preguntaId = ordenarPreguntas(resultado)[indice]?.preguntaId
        setEvaluacion(resultado)
        setRespondidas(new Set(resultado.preguntasRespondidas))
        setRespuestasConfirmadas(mapa)
        setIndiceActual(indice)
        setSeleccion(preguntaId ? (mapa.get(preguntaId) ?? null) : null)
      })
      .catch((err) => {
        if (controller.signal.aborted) return
        if (err instanceof ApiError && err.status === 422) {
          navigate(`/mis-actividades/${actividadId}/fuera-de-periodo`, { replace: true })
          return
        }
        throw err
      })

    return () => controller.abort()
  }, [actividadId, navigate])

  if (evaluacion === null) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  const preguntas = ordenarPreguntas(evaluacion)
  const preguntaActual = preguntas[indiceActual]
  const cantidad = preguntas.length
  const progresoPorcentaje = Math.round((respondidas.size / cantidad) * 100)

  async function pausarYSalir() {
    await suspenderEvaluacion(evaluacion!.id)
    navigate(`/mis-actividades/actividades/${actividadId}/suspendida`)
  }

  const esUltimaPregunta = indiceActual === cantidad - 1
  const preguntaYaRespondida = respondidas.has(preguntaActual.preguntaId)

  function irA(indice: number) {
    const pregunta = preguntas[indice]
    setSeleccion(pregunta ? (respuestasConfirmadas.get(pregunta.preguntaId) ?? null) : null)
    setError(null)
    setIndiceActual(indice)
  }

  async function confirmarYSiguiente() {
    if (!seleccion) return
    setError(null)
    setEnviando(true)
    try {
      const contenido = contenidoDeSeleccion(seleccion)
      await registrarRespuesta(evaluacion!.id, preguntaActual.preguntaId, contenido)
      setRespondidas((prev) => new Set(prev).add(preguntaActual.preguntaId))
      setRespuestasConfirmadas((prev) =>
        new Map(prev).set(preguntaActual.preguntaId, seleccion),
      )
      if (esUltimaPregunta) {
        await finalizarEvaluacion(evaluacion!.id)
        navigate(`/mis-actividades/evaluaciones/${evaluacion!.id}/revision`)
        return
      }
      irA(indiceActual + 1)
    } catch (err) {
      if (err instanceof ApiError && err.status === 422) {
        setError(err.message)
        return
      }
      throw err
    } finally {
      setEnviando(false)
    }
  }

  /** Sobre una pregunta ya respondida el botón solo navega — nunca reintenta registrar
   * (INV-AE-07/08 rechazaría con `IntentosAgotados`, `US-ADJ-12`). */
  async function avanzarSinConfirmar() {
    if (esUltimaPregunta) {
      setError(null)
      setEnviando(true)
      try {
        await finalizarEvaluacion(evaluacion!.id)
        navigate(`/mis-actividades/evaluaciones/${evaluacion!.id}/revision`)
      } finally {
        setEnviando(false)
      }
      return
    }
    irA(indiceActual + 1)
  }

  return (
    <div className="mx-auto max-w-xl">
      <div className="flex items-start justify-between gap-3">
        <h1 className="text-lg font-semibold">Rendir evaluación</h1>
        <Button variant="outline" size="sm" onClick={() => void pausarYSalir()}>
          Pausar y salir
        </Button>
      </div>
      <p className="mt-1 text-sm text-muted-foreground">
        Pregunta {indiceActual + 1} de {cantidad}
      </p>

      <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary transition-all"
          style={{ width: `${progresoPorcentaje}%` }}
        />
      </div>
      <p className="mt-1 text-xs text-muted-foreground">{respondidas.size} respondidas</p>

      {error && (
        <div
          role="alert"
          className="mt-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          <p className="font-medium">{error}</p>
        </div>
      )}

      <Card className="mt-4 p-5">
        <p className="font-medium">{preguntaActual.enunciado}</p>

        <div className="mt-3 flex flex-col gap-2">
          {preguntaActual.opciones !== null ? (
            preguntaActual.opciones.map((texto, indice) => (
              <label
                key={indice}
                className={`flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm ${
                  seleccion?.tipo === "opcion" && seleccion.indice === indice
                    ? "border-primary bg-primary/5"
                    : "border-input"
                }`}
              >
                <input
                  type="radio"
                  name={`pregunta-${preguntaActual.preguntaId}`}
                  checked={seleccion?.tipo === "opcion" && seleccion.indice === indice}
                  disabled={preguntaYaRespondida}
                  onChange={() => setSeleccion({ tipo: "opcion", indice })}
                />
                {texto}
              </label>
            ))
          ) : (
            <>
              <label
                className={`flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm ${
                  seleccion?.tipo === "vf" && seleccion.valor === true
                    ? "border-primary bg-primary/5"
                    : "border-input"
                }`}
              >
                <input
                  type="radio"
                  name={`pregunta-${preguntaActual.preguntaId}`}
                  checked={seleccion?.tipo === "vf" && seleccion.valor === true}
                  disabled={preguntaYaRespondida}
                  onChange={() => setSeleccion({ tipo: "vf", valor: true })}
                />
                Verdadero
              </label>
              <label
                className={`flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm ${
                  seleccion?.tipo === "vf" && seleccion.valor === false
                    ? "border-primary bg-primary/5"
                    : "border-input"
                }`}
              >
                <input
                  type="radio"
                  name={`pregunta-${preguntaActual.preguntaId}`}
                  checked={seleccion?.tipo === "vf" && seleccion.valor === false}
                  disabled={preguntaYaRespondida}
                  onChange={() => setSeleccion({ tipo: "vf", valor: false })}
                />
                Falso
              </label>
            </>
          )}
        </div>
      </Card>

      <div className="mt-4 flex justify-center gap-1.5">
        {preguntas.map((p, indice) => {
          const estado =
            indice === indiceActual
              ? "bg-primary text-primary-foreground"
              : respondidas.has(p.preguntaId)
                ? "bg-emerald-600 text-white"
                : "bg-muted text-muted-foreground"
          return (
            <button
              key={p.preguntaId}
              type="button"
              onClick={() => irA(indice)}
              className={`flex size-7 items-center justify-center rounded-full text-xs font-medium ${estado}`}
            >
              {indice + 1}
            </button>
          )
        })}
      </div>

      <div className="mt-4 flex justify-between gap-3">
        <Button
          variant="outline"
          disabled={indiceActual === 0}
          onClick={() => irA(indiceActual - 1)}
        >
          Anterior
        </Button>
        <Button
          disabled={(!preguntaYaRespondida && !seleccion) || enviando}
          onClick={() =>
            void (preguntaYaRespondida ? avanzarSinConfirmar() : confirmarYSiguiente())
          }
        >
          {preguntaYaRespondida
            ? esUltimaPregunta
              ? "Finalizar"
              : "Siguiente"
            : esUltimaPregunta
              ? "Confirmar y finalizar"
              : "Confirmar y siguiente"}
        </Button>
      </div>
      <p className="mt-3 text-center text-xs text-muted-foreground">
        Cada respuesta se guarda apenas la confirmás — si se corta la conexión, no perdés lo ya
        respondido.
      </p>
    </div>
  )
}
