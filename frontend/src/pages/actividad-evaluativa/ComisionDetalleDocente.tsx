import { useEffect, useRef, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ApiError } from "@/lib/api-client"
import {
  generarInvitacion,
  listarEstudiantesDeComision,
  obtenerComision,
  type ComisionDetalleResponse,
  type EstudianteResumenResponse,
} from "@/lib/identidad-comisiones-api"
import { obtenerUsuarioId } from "@/lib/session"

/**
 * Detalle de Comisión — vista Docente, generar invitación (§3.4 `wireframes-portal-entrada.md`,
 * `US-ADJ-26`). Consume `GET /comisiones/{id}` (`US-ADJ-25`) y
 * `POST /comisiones/{id}/invitaciones` sin `email_destinatario` — el backend solo devuelve el
 * `token`, sin enviar email.
 */
export function ComisionDetalleDocente() {
  const { comisionId } = useParams<{ comisionId: string }>()
  const navigate = useNavigate()

  const [comision, setComision] = useState<ComisionDetalleResponse | null>(null)
  const [estudiantes, setEstudiantes] = useState<EstudianteResumenResponse[] | null>(null)
  const [link, setLink] = useState<string | null>(null)
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

    return () => controller.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [comisionId])

  async function handleGenerar() {
    const docenteId = obtenerUsuarioId()
    if (!comisionId || !docenteId) return
    setError(null)
    setGenerando(true)
    setCopiado(false)
    try {
      const invitacion = await generarInvitacion(
        comisionId,
        docenteId,
        controladorSubmitRef.current?.signal,
      )
      setLink(`${window.location.origin}/registro?token=${invitacion.token}`)
    } catch (err) {
      if (controladorSubmitRef.current?.signal.aborted) return
      if (err instanceof ApiError && err.status === 422) {
        setError("No estás asignado a esta comisión, no podés generar su link de invitación.")
        return
      }
      throw err
    } finally {
      setGenerando(false)
    }
  }

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
        <Button variant="outline" onClick={() => navigate(-1)}>
          ‹ Volver
        </Button>
      </div>

      <Card className="mt-4 p-4">
        <h2 className="text-sm font-semibold">Invitación</h2>

        {error && (
          <div
            role="alert"
            className="mt-2 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
          >
            {error}
          </div>
        )}

        {link && (
          <div className="mt-2 rounded-lg border border-border bg-muted px-3 py-2">
            <p className="break-all font-mono text-sm">{link}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Válido por 7 días desde su generación, un solo uso.
            </p>
          </div>
        )}

        <div className="mt-3 flex items-center gap-2">
          <Button type="button" disabled={generando} onClick={() => void handleGenerar()}>
            {generando ? "Generando…" : link ? "Generar un link nuevo" : "Generar link de invitación"}
          </Button>
          {link && (
            <Button type="button" variant="outline" onClick={() => void handleCopiar()}>
              {copiado ? "Copiado ✓" : "Copiar"}
            </Button>
          )}
        </div>
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
