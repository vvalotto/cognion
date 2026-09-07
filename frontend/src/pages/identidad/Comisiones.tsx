import { useEffect, useState } from "react"
import { useNavigate } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { listarMaterias, type MateriaListItemResponse } from "@/lib/banco-preguntas-api"
import { listarCuentas, type CuentaResponse } from "@/lib/cuentas-api"
import {
  listarComisionesPorMateria,
  listarEstudiantesDeComision,
  type ComisionResumenResponse,
} from "@/lib/identidad-comisiones-api"

/**
 * Pantalla de Comisiones del Administrador (§3.1 `wireframes-portal-entrada.md`) — consume
 * `GET /materias/{id}/comisiones` y `GET /comisiones/{id}/estudiantes` (`US-ADJ-23`).
 */
export function Comisiones() {
  const navigate = useNavigate()

  const [materias, setMaterias] = useState<MateriaListItemResponse[] | null>(null)
  const [materiaId, setMateriaId] = useState<string>("")
  const [comisiones, setComisiones] = useState<ComisionResumenResponse[] | null>(null)
  const [docentes, setDocentes] = useState<CuentaResponse[]>([])
  const [conteoEstudiantes, setConteoEstudiantes] = useState<Record<string, number>>({})

  useEffect(() => {
    const controller = new AbortController()
    listarMaterias(controller.signal)
      .then((resultado) => {
        setMaterias(resultado)
        if (resultado.length > 0) setMateriaId((actual) => actual || resultado[0].id)
      })
      .catch(() => {})
    listarCuentas({ rol: "docente" }, { pagina: 1, tamanioPagina: 100 }, controller.signal)
      .then((resultado) => setDocentes(resultado.cuentas))
      .catch(() => {})
    return () => controller.abort()
  }, [])

  useEffect(() => {
    if (!materiaId) return
    const controller = new AbortController()
    setComisiones(null)
    listarComisionesPorMateria(materiaId, controller.signal)
      .then(async (resultado) => {
        setComisiones(resultado)
        const conteos = await Promise.all(
          resultado.map((comision) =>
            listarEstudiantesDeComision(comision.id, controller.signal).then(
              (estudiantes) => [comision.id, estudiantes.length] as const,
            ),
          ),
        )
        setConteoEstudiantes(Object.fromEntries(conteos))
      })
      .catch(() => {})
    return () => controller.abort()
  }, [materiaId])

  function nombreDocente(docenteId: string): string {
    return docentes.find((docente) => docente.id === docenteId)?.nombre ?? docenteId
  }

  return (
    <div>
      <Breadcrumb items={[{ label: "Comisiones" }]} />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Comisiones</h1>
          <p className="text-sm text-muted-foreground">
            Horario, docentes asignados y estudiantes inscriptos por comisión.
          </p>
        </div>
        <Button onClick={() => navigate("/comisiones/nueva")}>+ Nueva Comisión</Button>
      </div>

      <div className="mt-4">
        <label
          htmlFor="filtro-materia"
          className="text-[11px] font-bold tracking-wide text-muted-foreground uppercase"
        >
          Materia
        </label>
        <select
          id="filtro-materia"
          value={materiaId}
          onChange={(e) => setMateriaId(e.target.value)}
          className="mt-1 block rounded-md border border-border px-2 py-1 text-sm"
        >
          {materias === null ? (
            <option>Cargando…</option>
          ) : (
            materias.map((materia) => (
              <option key={materia.id} value={materia.id}>
                {materia.nombre}
              </option>
            ))
          )}
        </select>
      </div>

      <Card className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border bg-muted text-[11px] font-bold tracking-wide text-muted-foreground uppercase">
              <th className="py-2 pr-4 pl-4">Horario</th>
              <th className="py-2 pr-4">Docentes asignados</th>
              <th className="py-2 pr-4">Estudiantes</th>
              <th className="py-2 pr-4"></th>
            </tr>
          </thead>
          <tbody>
            {comisiones === null ? (
              <tr>
                <td colSpan={4} className="py-4 pl-4 text-muted-foreground">
                  Cargando…
                </td>
              </tr>
            ) : comisiones.length === 0 ? (
              <tr>
                <td colSpan={4} className="py-6 pl-4 text-center text-muted-foreground">
                  Esta materia todavía no tiene comisiones.
                </td>
              </tr>
            ) : (
              comisiones.map((comision) => (
                <tr key={comision.id} className="border-b border-border last:border-0">
                  <td className="py-3 pr-4 pl-4">{comision.horario}</td>
                  <td className="py-3 pr-4">
                    {comision.docentesAsignados.length === 0 ? (
                      <Badge variant="docente-sin-asignar">Sin docente asignado</Badge>
                    ) : (
                      comision.docentesAsignados.map((docenteId) => (
                        <Badge key={docenteId} variant="docente-asignado" className="mr-1">
                          {nombreDocente(docenteId)}
                        </Badge>
                      ))
                    )}
                  </td>
                  <td className="py-3 pr-4">{conteoEstudiantes[comision.id] ?? "…"}</td>
                  <td className="py-3 pr-4">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => navigate(`/comisiones/${comision.id}`)}
                    >
                      Ver detalle
                    </Button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </Card>
    </div>
  )
}
