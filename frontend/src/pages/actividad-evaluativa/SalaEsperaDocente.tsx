import { useCallback, useEffect, useRef, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { IndicadorConexion } from "@/components/IndicadorConexion"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ApiError } from "@/lib/api-client"
import { obtenerComision, type ComisionDetalleResponse } from "@/lib/identidad-comisiones-api"
import { listarMaterias, type MateriaListItemResponse } from "@/lib/banco-preguntas-api"
import {
  iniciarSesion,
  listarParticipantes,
  obtenerEstadoSesion,
  type EstadoSesionEnVivoResponse,
  type ParticipanteResponse,
} from "@/lib/sesion-en-vivo-api"
import type { MensajeSesionEnVivo } from "@/lib/canal-sesion-en-vivo"
import { useCanalSesionEnVivo } from "@/lib/use-canal-sesion-en-vivo"

/** Sala de espera de una sesión en vivo (`#doc-sala-espera`, US-6.3.5). */
export function SalaEsperaDocente() {
  const { sesionId } = useParams<{ sesionId: string }>()
  const navigate = useNavigate()

  const [estado, setEstado] = useState<EstadoSesionEnVivoResponse | null>(null)
  const [comision, setComision] = useState<ComisionDetalleResponse | null>(null)
  const [materia, setMateria] = useState<MateriaListItemResponse | null>(null)
  const [participantes, setParticipantes] = useState<ParticipanteResponse[]>([])
  const [iniciando, setIniciando] = useState(false)
  const [redirigido, setRedirigido] = useState(false)

  const controladorSubmitRef = useRef<AbortController | null>(null)
  if (!controladorSubmitRef.current) controladorSubmitRef.current = new AbortController()

  useEffect(() => {
    if (!sesionId) return undefined
    const controller = new AbortController()
    obtenerEstadoSesion(sesionId, controller.signal).then(setEstado).catch(() => {})
    return () => controller.abort()
  }, [sesionId])

  useEffect(() => {
    if (!sesionId) return undefined
    const controller = new AbortController()
    listarParticipantes(sesionId, controller.signal).then(setParticipantes).catch(() => {})
    return () => controller.abort()
  }, [sesionId])

  useEffect(() => {
    if (!estado) return undefined
    const controller = new AbortController()
    obtenerComision(estado.comisionId, controller.signal).then(setComision).catch(() => {})
    return () => controller.abort()
  }, [estado])

  useEffect(() => {
    if (!comision) return undefined
    const controller = new AbortController()
    listarMaterias(controller.signal)
      .then((materias) => setMateria(materias.find((m) => m.id === comision.materiaId) ?? null))
      .catch(() => {})
    return () => controller.abort()
  }, [comision])

  useEffect(() => {
    if (!estado || !comision || redirigido) return
    if (estado.estado === "en_curso") {
      setRedirigido(true)
      void navigate(`/sesiones-en-vivo/${sesionId}/proyeccion`)
    } else if (estado.estado === "finalizada") {
      setRedirigido(true)
      void navigate(`/actividad-evaluativa/comisiones/${comision.id}`)
    }
  }, [estado, comision, redirigido, navigate, sesionId])

  const onMensaje = useCallback((mensaje: MensajeSesionEnVivo) => {
    if (mensaje.tipo === "participantes_actualizados") {
      setParticipantes(
        mensaje.participantes.map((p) => ({
          estudianteId: p.estudianteId,
          nombre: p.nombre,
          unidoEn: p.unidoEn,
        })),
      )
    }
  }, [])

  const onReconectado = useCallback(() => {
    if (!sesionId) return
    listarParticipantes(sesionId).then(setParticipantes).catch(() => {})
  }, [sesionId])

  const estadoCanal = useCanalSesionEnVivo(sesionId ?? "", onMensaje, onReconectado)

  useEffect(() => {
    const controller = new AbortController()
    controladorSubmitRef.current = controller
    return () => controller.abort()
  }, [])

  async function handleIniciar() {
    if (!sesionId || iniciando) return
    setIniciando(true)
    try {
      await iniciarSesion(sesionId, controladorSubmitRef.current?.signal)
    } catch (err) {
      if (controladorSubmitRef.current?.signal.aborted) return
      if (err instanceof ApiError && err.status === 422) {
        void navigate(`/sesiones-en-vivo/${sesionId}/proyeccion`)
        return
      }
      setIniciando(false)
      throw err
    }
    void navigate(`/sesiones-en-vivo/${sesionId}/proyeccion`)
  }

  if (estado === null || comision === null || materia === null) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Mis materias", to: "/actividad-evaluativa/materias" },
          {
            label: materia.nombre,
            to: `/actividad-evaluativa/materias/${materia.id}/comisiones`,
          },
          {
            label: comision.horario,
            to: `/actividad-evaluativa/comisiones/${comision.id}`,
          },
          { label: "Sala de espera" },
        ]}
      />
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Sala de espera</h1>
        <IndicadorConexion estado={estadoCanal} />
      </div>
      <p className="mt-1 text-sm text-muted-foreground">
        Materia: {materia.nombre} — {estado.cantidadPreguntas} preguntas —{" "}
        {estado.tiempoLimitePorPreguntaSegundos}s por pregunta
      </p>

      <Card className="mt-4 p-4">
        <h2 className="text-sm font-semibold">Participantes ({participantes.length})</h2>
        {participantes.length === 0 ? (
          <p className="mt-2 text-sm text-muted-foreground">Todavía no se unió nadie.</p>
        ) : (
          <div className="mt-2 flex flex-wrap gap-2">
            {participantes.map((p) => (
              <span
                key={p.estudianteId}
                className="rounded-full bg-muted px-3 py-1 text-sm font-medium"
              >
                {p.nombre}
              </span>
            ))}
          </div>
        )}
        <p className="mt-3 text-xs text-muted-foreground">
          Se puede seguir sumando gente después de iniciar la sesión.
        </p>
      </Card>

      {participantes.length === 0 && (
        <p role="alert" className="mt-4 text-sm text-amber-800">
          Todavía no se unió nadie — podés iniciar igual.
        </p>
      )}

      <div className="mt-4">
        <Button type="button" disabled={iniciando} onClick={() => void handleIniciar()}>
          {iniciando ? "Iniciando…" : "Iniciar sesión"}
        </Button>
      </div>
    </div>
  )
}
