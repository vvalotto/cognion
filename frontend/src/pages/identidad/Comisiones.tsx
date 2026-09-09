import { Eye, Pencil, RotateCcw, Trash2 } from "lucide-react"
import { useEffect, useState } from "react"
import { useNavigate } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { RowActionButton } from "@/components/ui/row-action-button"
import {
  Table,
  TableBody,
  TableCell,
  TableEmptyRow,
  TableHeader,
  TableHeaderCell,
  TableRow,
} from "@/components/ui/table"
import { listarMaterias, type MateriaListItemResponse } from "@/lib/banco-preguntas-api"
import { listarCuentas, type CuentaResponse } from "@/lib/cuentas-api"
import {
  activarComision,
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
    listarComisionesPorMateria(materiaId, controller.signal, true)
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

  async function handleActivar(comisionId: string) {
    await activarComision(comisionId)
    setComisiones(
      (actual) =>
        actual?.map((c) => (c.id === comisionId ? { ...c, activa: true } : c)) ?? actual,
    )
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
        <Button onClick={() => navigate(`/comisiones/nueva?materiaId=${materiaId}`)}>
          + Nueva Comisión
        </Button>
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

      <Card className="mt-4 overflow-x-auto py-0">
        <Table>
          <TableHeader>
            <tr>
              <TableHeaderCell>Horario</TableHeaderCell>
              <TableHeaderCell>Docentes asignados</TableHeaderCell>
              <TableHeaderCell>Estudiantes</TableHeaderCell>
              <TableHeaderCell>Estado</TableHeaderCell>
              <TableHeaderCell></TableHeaderCell>
            </tr>
          </TableHeader>
          <TableBody>
            {comisiones === null ? (
              <TableEmptyRow colSpan={5}>Cargando…</TableEmptyRow>
            ) : comisiones.length === 0 ? (
              <TableEmptyRow colSpan={5}>Esta materia todavía no tiene comisiones.</TableEmptyRow>
            ) : (
              comisiones.map((comision) => (
                <TableRow key={comision.id}>
                  <TableCell className="font-medium">{comision.horario}</TableCell>
                  <TableCell>
                    {comision.docentesAsignados.length === 0 ? (
                      <Badge variant="docente-sin-asignar">Sin docente asignado</Badge>
                    ) : (
                      comision.docentesAsignados.map((docenteId) => (
                        <Badge key={docenteId} variant="docente-asignado" className="mr-1">
                          {nombreDocente(docenteId)}
                        </Badge>
                      ))
                    )}
                  </TableCell>
                  <TableCell>{conteoEstudiantes[comision.id] ?? "…"}</TableCell>
                  <TableCell>
                    <Badge variant={comision.activa ? "estado-activa" : "estado-inactiva"}>
                      {comision.activa ? "Activa" : "Inactiva"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1.5">
                      <RowActionButton
                        label="Ver detalle"
                        icon={Eye}
                        onClick={() => navigate(`/comisiones/${comision.id}`)}
                      />
                      {comision.activa ? (
                        <>
                          <RowActionButton
                            label="Editar"
                            icon={Pencil}
                            onClick={() => navigate(`/comisiones/${comision.id}/editar`)}
                          />
                          <RowActionButton
                            label="Eliminar"
                            icon={Trash2}
                            variant="destructive"
                            onClick={() => navigate(`/comisiones/${comision.id}/eliminar`)}
                          />
                        </>
                      ) : (
                        <RowActionButton
                          label="Activar"
                          icon={RotateCcw}
                          onClick={() => void handleActivar(comision.id)}
                        />
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  )
}
