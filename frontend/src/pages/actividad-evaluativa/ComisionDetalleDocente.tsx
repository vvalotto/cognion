import { useEffect, useRef, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ApiError } from "@/lib/api-client"
import {
  desactivarInvitacionGrupal,
  DURACION_INVITACION_GRUPAL_POR_DEFECTO,
  DURACIONES_INVITACION_GRUPAL,
  generarInvitacionGrupal,
  listarEstudiantesDeComision,
  obtenerComision,
  obtenerUltimaInvitacionGrupal,
  type ComisionDetalleResponse,
  type EstudianteResumenResponse,
  type InvitacionGrupalEstado,
} from "@/lib/identidad-comisiones-api"
import {
  listarSesionesEnVivo,
  type EstadoSesionEnVivo,
  type SesionEnVivoResumenResponse,
} from "@/lib/sesion-en-vivo-api"

const ETIQUETA_ESTADO_SESION: Record<EstadoSesionEnVivo, string> = {
  en_espera: "En espera",
  en_curso: "En curso",
  finalizada: "Finalizada",
  cancelada: "Cancelada",
}

const VARIANTE_ESTADO_SESION: Record<EstadoSesionEnVivo, "estado-en-espera" | "estado-en-curso" | "estado-cerrada"> = {
  en_espera: "estado-en-espera",
  en_curso: "estado-en-curso",
  finalizada: "estado-cerrada",
  cancelada: "estado-cerrada",
}

const REFRESCO_REGISTRADOS_MS = 15_000

/** "59 min", "2 h 5 min" o "1 día" según lo que falta hasta `expiraEn`. */
function formatearRestante(milisegundos: number): string {
  const minutos = Math.max(0, Math.ceil(milisegundos / 60_000))
  if (minutos < 60) return `${minutos} min`
  if (minutos < 1440) {
    const resto = minutos % 60
    return resto === 0 ? `${Math.floor(minutos / 60)} h` : `${Math.floor(minutos / 60)} h ${resto} min`
  }
  return minutos < 2880 ? "1 día" : `${Math.floor(minutos / 1440)} días`
}

function textoRegistrados(usos: number): string {
  if (usos === 0) return "Todavía nadie se registró con este link"
  return usos === 1
    ? "1 estudiante se registró con este link"
    : `${usos} estudiantes se registraron con este link`
}

/**
 * Detalle de Comisión — vista Docente, link de invitación grupal (§3.4 `wireframes-portal-entrada.md`,
 * `US-ADJ-26` y `US-ADJ-67`). Consume `GET /comisiones/{id}` (`US-ADJ-25`) y los endpoints de
 * `/comisiones/{id}/invitaciones-grupales`: un solo link vigente por comisión, con duración elegible,
 * contador de registrados y botón para desactivarlo.
 */
export function ComisionDetalleDocente() {
  const { comisionId } = useParams<{ comisionId: string }>()
  const navigate = useNavigate()

  const [comision, setComision] = useState<ComisionDetalleResponse | null>(null)
  const [estudiantes, setEstudiantes] = useState<EstudianteResumenResponse[] | null>(null)
  const [sesionesActivas, setSesionesActivas] = useState<SesionEnVivoResumenResponse[] | null>(
    null,
  )
  const [invitacion, setInvitacion] = useState<InvitacionGrupalEstado | null>(null)
  const [duracion, setDuracion] = useState(DURACION_INVITACION_GRUPAL_POR_DEFECTO)
  const [ahora, setAhora] = useState(() => Date.now())
  const [generando, setGenerando] = useState(false)
  const [copiado, setCopiado] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const controladorSubmitRef = useRef<AbortController | null>(null)
  if (!controladorSubmitRef.current) controladorSubmitRef.current = new AbortController()

  useEffect(() => {
    if (!comisionId) return
    // Mismo patrón que ComisionDetalle.tsx (US-ADJ-25): un controller nuevo por montaje real,
    // para que el doble montaje de StrictMode en dev no aborte el submit siguiente.
    const controller = new AbortController()
    controladorSubmitRef.current = controller

    obtenerComision(comisionId, controller.signal).then(setComision).catch(() => {})
    listarEstudiantesDeComision(comisionId, controller.signal)
      .then(setEstudiantes)
      .catch(() => {})
    listarSesionesEnVivo(comisionId, controller.signal)
      .then((sesiones) => setSesionesActivas(sesiones.filter((s) => s.estado !== "finalizada")))
      .catch(() => {})
    obtenerUltimaInvitacionGrupal(comisionId, controller.signal)
      .then(setInvitacion)
      .catch(() => {})

    return () => controller.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [comisionId])

  // Con un link vigente: el reloj avanza y se refresca el contador de registrados mientras la clase se anota.
  const vigente = invitacion?.estado === "vigente"
  useEffect(() => {
    if (!comisionId || !vigente) return
    const reloj = setInterval(() => setAhora(Date.now()), 1000 * 15)
    const refresco = setInterval(() => {
      obtenerUltimaInvitacionGrupal(comisionId).then(setInvitacion).catch(() => {})
    }, REFRESCO_REGISTRADOS_MS)
    return () => {
      clearInterval(reloj)
      clearInterval(refresco)
    }
  }, [comisionId, vigente])

  async function handleGenerar() {
    if (!comisionId) return
    setError(null)
    setGenerando(true)
    setCopiado(false)
    try {
      setInvitacion(
        await generarInvitacionGrupal(comisionId, duracion, controladorSubmitRef.current?.signal),
      )
      setAhora(Date.now())
    } catch (err) {
      if (controladorSubmitRef.current?.signal.aborted) return
      if (err instanceof ApiError && err.status === 403) {
        setError("No estás asignado a esta comisión, no podés generar su link de invitación.")
        return
      }
      throw err
    } finally {
      setGenerando(false)
    }
  }

  async function handleDesactivar() {
    if (!comisionId || !invitacion) return
    setError(null)
    try {
      await desactivarInvitacionGrupal(
        comisionId,
        invitacion.id,
        controladorSubmitRef.current?.signal,
      )
      setInvitacion({ ...invitacion, estado: "revocada", token: null })
    } catch (err) {
      if (controladorSubmitRef.current?.signal.aborted) return
      throw err
    }
  }

  const link =
    invitacion?.estado === "vigente" && invitacion.token
      ? `${window.location.origin}/registro?token=${invitacion.token}`
      : null
  const venceEn = invitacion ? new Date(invitacion.expiraEn).getTime() - ahora : 0
  // El servidor decide el estado, pero si el link venció mientras la pantalla estaba abierta se muestra ya vencido.
  const estadoVisible = invitacion?.estado === "vigente" && venceEn <= 0 ? "vencida" : invitacion?.estado

  async function handleCopiar() {
    if (!link) return
    await navigator.clipboard.writeText(link)
    setCopiado(true)
  }

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Mis materias", to: "/actividad-evaluativa/materias" },
          { label: "Comisiones" },
          { label: comision?.horario ?? "…" },
        ]}
      />
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">{comision?.horario ?? "Cargando…"}</h1>
        <div className="flex gap-2">
          <Button
            type="button"
            onClick={() => navigate(`/sesiones-en-vivo/comisiones/${comisionId}/nueva`)}
          >
            + Nueva sesión en vivo
          </Button>
          <Button variant="outline" onClick={() => navigate(-1)}>
            ‹ Volver
          </Button>
        </div>
      </div>

      {sesionesActivas !== null && sesionesActivas.length > 0 && (
        <Card className="mt-4 p-4">
          <h2 className="text-sm font-semibold">Sesiones en vivo activas</h2>
          <div className="mt-2 flex flex-col gap-2">
            {sesionesActivas.map((sesion) => (
              <div
                key={sesion.id}
                className="flex items-center justify-between rounded-lg border border-border px-3 py-2"
              >
                <div className="flex items-center gap-3">
                  <Badge variant={VARIANTE_ESTADO_SESION[sesion.estado]}>
                    {ETIQUETA_ESTADO_SESION[sesion.estado]}
                  </Badge>
                  <span className="text-sm">
                    {sesion.cantidadPreguntas} preguntas —{" "}
                    {new Date(sesion.creadaEn).toLocaleString()}
                  </span>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() =>
                    navigate(
                      sesion.estado === "en_curso"
                        ? `/sesiones-en-vivo/${sesion.id}/proyeccion`
                        : `/sesiones-en-vivo/${sesion.id}/sala`,
                    )
                  }
                >
                  Continuar
                </Button>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card className="mt-4 p-4">
        <h2 className="text-sm font-semibold">Link de invitación para la clase</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          Compartilo por pantalla o por chat: vale para toda la clase hasta que venza o lo desactives.
        </p>

        {error && (
          <div
            role="alert"
            className="mt-2 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
          >
            {error}
          </div>
        )}

        <div className="mt-3 flex flex-wrap items-end gap-2">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="duracion-invitacion" className="text-sm font-medium">
              Duración del link
            </label>
            <select
              id="duracion-invitacion"
              className="h-9 rounded-lg border border-border bg-background px-2 text-sm"
              value={duracion}
              onChange={(event) => setDuracion(Number(event.target.value))}
            >
              {DURACIONES_INVITACION_GRUPAL.map((d) => (
                <option key={d.minutos} value={d.minutos}>
                  {d.etiqueta}
                </option>
              ))}
            </select>
          </div>
          <Button type="button" disabled={generando} onClick={() => void handleGenerar()}>
            {generando ? "Generando…" : invitacion ? "Generar un link nuevo" : "Generar link grupal"}
          </Button>
        </div>
        {estadoVisible === "vigente" && (
          <p className="mt-1 text-xs text-muted-foreground">
            Si generás un link nuevo, el anterior se desactiva.
          </p>
        )}

        {invitacion && estadoVisible === "vigente" && link && (
          <div className="mt-3">
            <div className="flex items-center gap-2 rounded-lg border border-border bg-muted px-3 py-2">
              <p className="min-w-0 flex-1 break-all font-mono text-sm">{link}</p>
              <Button type="button" variant="outline" onClick={() => void handleCopiar()}>
                {copiado ? "Copiado ✓" : "Copiar"}
              </Button>
            </div>
            <p className="mt-2 text-sm">
              <Badge variant="estado-en-curso">Vigente</Badge>{" "}
              Vence en <strong>{formatearRestante(venceEn)}</strong> (a las{" "}
              {new Date(invitacion.expiraEn).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
              ) · {textoRegistrados(invitacion.usos)}
            </p>
            <Button
              type="button"
              variant="outline"
              className="mt-2"
              onClick={() => void handleDesactivar()}
            >
              Desactivar link
            </Button>
          </div>
        )}

        {invitacion && estadoVisible === "vencida" && (
          <div className="mt-3 rounded-lg border border-border bg-muted px-3 py-2 text-sm">
            <Badge variant="estado-cerrada">Venció</Badge> El link venció. {textoRegistrados(invitacion.usos)}.
            Generá uno nuevo si falta alguien.
          </div>
        )}

        {invitacion && estadoVisible === "revocada" && (
          <div className="mt-3 rounded-lg border border-border bg-muted px-3 py-2 text-sm">
            <Badge variant="estado-en-espera">Desactivado</Badge> Desactivaste el link: quien lo abra
            verá que ya no es válido. {textoRegistrados(invitacion.usos)}.
          </div>
        )}
      </Card>

      <Card className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border bg-muted text-[11px] font-bold tracking-wide text-muted-foreground uppercase">
              <th className="py-2 pr-4 pl-4">Estudiantes inscriptos</th>
            </tr>
          </thead>
          <tbody>
            {estudiantes === null ? (
              <tr>
                <td className="py-4 pl-4 text-muted-foreground">Cargando…</td>
              </tr>
            ) : estudiantes.length === 0 ? (
              <tr>
                <td className="py-6 pl-4 text-center text-muted-foreground">
                  Esta comisión todavía no tiene estudiantes inscriptos.
                </td>
              </tr>
            ) : (
              estudiantes.map((estudiante) => (
                <tr key={estudiante.id} className="border-b border-border last:border-0">
                  <td className="py-3 pl-4">{estudiante.nombre}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </Card>
    </div>
  )
}
