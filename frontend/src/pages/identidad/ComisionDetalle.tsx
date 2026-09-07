import { useEffect, useRef, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { listarCuentas, type CuentaResponse } from "@/lib/cuentas-api"
import {
  asignarDocente,
  listarEstudiantesDeComision,
  obtenerComision,
  type ComisionDetalleResponse,
  type EstudianteResumenResponse,
} from "@/lib/identidad-comisiones-api"

/**
 * Detalle de Comisión — vista Administrador (§3.3 `wireframes-portal-entrada.md`) — consume
 * `GET /comisiones/{id}` y `POST /comisiones/{id}/docentes` (`US-ADJ-25`).
 */
export function ComisionDetalle() {
  const { comisionId } = useParams<{ comisionId: string }>()
  const navigate = useNavigate()

  const [comision, setComision] = useState<ComisionDetalleResponse | null>(null)
  const [docentes, setDocentes] = useState<CuentaResponse[]>([])
  const [docenteSeleccionado, setDocenteSeleccionado] = useState("")
  const [estudiantes, setEstudiantes] = useState<EstudianteResumenResponse[] | null>(null)

  const controladorSubmitRef = useRef<AbortController | null>(null)
  if (!controladorSubmitRef.current) controladorSubmitRef.current = new AbortController()

  useEffect(() => {
    if (!comisionId) return
    // Mismo patrón que NuevaComision.tsx (US-ADJ-24): un controller nuevo por montaje real,
    // para que el doble montaje de StrictMode en dev no aborte el submit siguiente.
    const controller = new AbortController()
    controladorSubmitRef.current = controller

    obtenerComision(comisionId, controller.signal).then(setComision).catch(() => {})
    listarCuentas({ rol: "docente" }, { pagina: 1, tamanioPagina: 100 }, controller.signal)
      .then((resultado) => setDocentes(resultado.cuentas))
      .catch(() => {})
    listarEstudiantesDeComision(comisionId, controller.signal)
      .then(setEstudiantes)
      .catch(() => {})

    return () => controller.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [comisionId])

  function nombreDocente(docenteId: string): string {
    return docentes.find((docente) => docente.id === docenteId)?.nombre ?? docenteId
  }

  async function handleAsignar() {
    if (!comisionId || !docenteSeleccionado) return
    try {
      const actualizada = await asignarDocente(
        comisionId,
        docenteSeleccionado,
        controladorSubmitRef.current?.signal,
      )
      setComision(actualizada)
      setDocenteSeleccionado("")
    } catch (err) {
      if (controladorSubmitRef.current?.signal.aborted) return
      throw err
    }
  }

  const docentesDisponibles = docentes.filter(
    (docente) => !comision?.docentesAsignados.includes(docente.id),
  )

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Comisiones", to: "/comisiones" },
          { label: comision?.horario ?? "…" },
        ]}
      />
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">{comision?.horario ?? "Cargando…"}</h1>
        <Button variant="outline" onClick={() => navigate("/comisiones")}>
          ‹ Volver a Comisiones
        </Button>
      </div>

      {comision !== null && comision.docentesAsignados.length === 0 && (
        <div
          role="alert"
          className="mt-4 rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-sm text-amber-800"
        >
          Hasta que se asigne un Docente, esta Comisión no puede generar link de invitación
          para estudiantes.
        </div>
      )}

      <Card className="mt-4 p-4">
        <h2 className="text-sm font-semibold">Docentes asignados</h2>
        <div className="mt-2 flex flex-wrap gap-1">
          {comision === null ? (
            <span className="text-sm text-muted-foreground">Cargando…</span>
          ) : comision.docentesAsignados.length === 0 ? (
            <Badge variant="docente-sin-asignar">Sin docente asignado</Badge>
          ) : (
            comision.docentesAsignados.map((docenteId) => (
              <Badge key={docenteId} variant="docente-asignado">
                {nombreDocente(docenteId)}
              </Badge>
            ))
          )}
        </div>

        <div className="mt-4 flex items-end gap-2">
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="asignar-docente-select"
              className="text-[11px] font-bold tracking-wide text-muted-foreground uppercase"
            >
              Asignar Docente
            </label>
            <select
              id="asignar-docente-select"
              value={docenteSeleccionado}
              onChange={(e) => setDocenteSeleccionado(e.target.value)}
              className="rounded-md border border-border px-2 py-1.5 text-sm"
            >
              <option value="">Elegir…</option>
              {docentesDisponibles.map((docente) => (
                <option key={docente.id} value={docente.id}>
                  {docente.nombre}
                </option>
              ))}
            </select>
          </div>
          <Button type="button" disabled={!docenteSeleccionado} onClick={() => void handleAsignar()}>
            Asignar
          </Button>
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
