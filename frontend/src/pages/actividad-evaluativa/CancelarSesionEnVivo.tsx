import { useEffect, useRef, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ApiError } from "@/lib/api-client"
import { obtenerComision, type ComisionDetalleResponse } from "@/lib/identidad-comisiones-api"
import {
  cancelarSesion,
  listarParticipantes,
  obtenerEstadoSesion,
  type EstadoSesionEnVivoResponse,
} from "@/lib/sesion-en-vivo-api"
import { useNombreMateria } from "@/pages/identidad/useNombreMateria"

/**
 * Confirmación de cancelar una sesión en vivo que todavía no se inició (`#doc-cancelar-sesion`, §8.2,
 * `US-ADJ-58`). Al confirmar vuelve al detalle de la Comisión; la sesión deja de figurar como activa.
 */
export function CancelarSesionEnVivo() {
  const { sesionId } = useParams<{ sesionId: string }>()
  const navigate = useNavigate()

  const [estado, setEstado] = useState<EstadoSesionEnVivoResponse | null>(null)
  const [comision, setComision] = useState<ComisionDetalleResponse | null>(null)
  const [cantidadParticipantes, setCantidadParticipantes] = useState<number | null>(null)
  const [cancelando, setCancelando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const nombreMateria = useNombreMateria(comision?.materiaId)
  const controladorSubmitRef = useRef<AbortController | null>(null)

  useEffect(() => {
    if (!sesionId) return undefined
    const controller = new AbortController()
    obtenerEstadoSesion(sesionId, controller.signal).then(setEstado).catch(() => {})
    listarParticipantes(sesionId, controller.signal)
      .then((participantes) => setCantidadParticipantes(participantes.length))
      .catch(() => {})
    return () => controller.abort()
  }, [sesionId])

  useEffect(() => {
    if (!estado) return undefined
    const controller = new AbortController()
    obtenerComision(estado.comisionId, controller.signal).then(setComision).catch(() => {})
    return () => controller.abort()
  }, [estado])

  useEffect(() => {
    const controller = new AbortController()
    controladorSubmitRef.current = controller
    return () => controller.abort()
  }, [])

  const rutaSala = `/sesiones-en-vivo/${sesionId}/sala`

  async function handleCancelar() {
    if (!sesionId || !comision || cancelando) return
    setCancelando(true)
    setError(null)
    const signal = controladorSubmitRef.current?.signal
    try {
      await cancelarSesion(sesionId, signal)
    } catch (err) {
      if (signal?.aborted) return
      setCancelando(false)
      if (err instanceof ApiError && err.status === 422) {
        setError("La sesión ya no se puede cancelar: ya se inició o ya estaba cancelada.")
        return
      }
      throw err
    }
    void navigate(`/actividad-evaluativa/comisiones/${comision.id}`)
  }

  if (estado === null || comision === null) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Mis materias", to: "/actividad-evaluativa/materias" },
          {
            label: nombreMateria ?? "…",
            to: `/actividad-evaluativa/materias/${comision.materiaId}/comisiones`,
          },
          { label: comision.horario, to: `/actividad-evaluativa/comisiones/${comision.id}` },
          { label: "Sala de espera", to: rutaSala },
          { label: "Cancelar sesión" },
        ]}
      />
      <h1 className="text-lg font-semibold">¿Cancelar esta sesión?</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        La sesión todavía no empezó. Si la cancelás, deja de figurar como activa y no se puede
        retomar.
      </p>

      <Card className="mt-4 p-4 text-sm">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Preguntas</span>
          <span className="font-medium">
            {estado.cantidadPreguntas}
            {nombreMateria ? ` · ${nombreMateria}` : ""}
          </span>
        </div>
        <div className="mt-2 flex justify-between">
          <span className="text-muted-foreground">Participantes en la sala</span>
          <span className="font-medium">{cantidadParticipantes ?? "…"}</span>
        </div>
      </Card>

      <div
        role="note"
        className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800"
      >
        Los estudiantes en la sala ven que la sesión se canceló y vuelven a sus actividades.
      </div>

      {error && (
        <p role="alert" className="mt-4 text-sm text-destructive">
          {error}
        </p>
      )}

      <div className="mt-4 flex gap-2">
        <Button variant="outline" onClick={() => void navigate(rutaSala)}>
          Volver a la sala
        </Button>
        <Button variant="destructive-solid" disabled={cancelando} onClick={() => void handleCancelar()}>
          {cancelando ? "Cancelando…" : "Cancelar sesión"}
        </Button>
      </div>
    </div>
  )
}
