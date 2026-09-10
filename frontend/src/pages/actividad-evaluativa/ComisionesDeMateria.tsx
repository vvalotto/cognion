import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Card } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableEmptyRow,
  TableHeader,
  TableHeaderCell,
  TableRow,
} from "@/components/ui/table"
import { listarActividades, type ActividadResumenResponse } from "@/lib/actividad-evaluativa-api"
import { listarMaterias, type MateriaListItemResponse } from "@/lib/banco-preguntas-api"
import {
  listarComisionesPorMateria,
  listarEstudiantesDeComision,
  type ComisionResumenResponse,
} from "@/lib/identidad-comisiones-api"

interface ResumenComision {
  cantidadEstudiantes: number
  actividadesEnCurso: number
  actividadesProgramadas: number
}

function aplicaAComision(actividad: ActividadResumenResponse, comisionId: string): boolean {
  return actividad.comisionesIds.length === 0 || actividad.comisionesIds.includes(comisionId)
}

/**
 * Comisiones de una materia — vista Docente (`US-ADJ-26`), entry point hacia el detalle donde
 * genera el link de invitación. Reutiliza `listarComisionesPorMateria` (`US-4.2.2`), ya
 * accesible con rol `docente`. Tabla con cantidad de estudiantes inscriptos y de Actividades
 * (en curso/planificadas) que aplican a cada comisión, mismo patrón que el resto del portal
 * Docente.
 */
export function ComisionesDeMateria() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const navigate = useNavigate()

  const [materia, setMateria] = useState<MateriaListItemResponse | null>(null)
  const [comisiones, setComisiones] = useState<ComisionResumenResponse[] | null>(null)
  const [resumenes, setResumenes] = useState<Record<string, ResumenComision>>({})

  useEffect(() => {
    const controller = new AbortController()
    listarMaterias(controller.signal)
      .then((materias) => setMateria(materias.find((m) => m.id === materiaId) ?? null))
      .catch(() => {})
    return () => controller.abort()
  }, [materiaId])

  useEffect(() => {
    if (!materiaId) return undefined
    const controller = new AbortController()
    listarComisionesPorMateria(materiaId, controller.signal)
      .then(setComisiones)
      .catch(() => {})
    return () => controller.abort()
  }, [materiaId])

  useEffect(() => {
    if (!materiaId || !comisiones) return undefined
    const controller = new AbortController()
    Promise.all([
      listarActividades(materiaId, controller.signal),
      Promise.all(
        comisiones.map((comision) =>
          listarEstudiantesDeComision(comision.id, controller.signal).then(
            (estudiantes) => [comision.id, estudiantes.length] as const,
          ),
        ),
      ),
    ])
      .then(([actividades, conteosEstudiantes]) => {
        const estudiantesPorComision = Object.fromEntries(conteosEstudiantes)
        const entradas = comisiones.map((comision) => {
          const actividadesDeComision = actividades.filter((a) => aplicaAComision(a, comision.id))
          const resumen: ResumenComision = {
            cantidadEstudiantes: estudiantesPorComision[comision.id] ?? 0,
            actividadesEnCurso: actividadesDeComision.filter((a) => a.estado === "en_curso")
              .length,
            actividadesProgramadas: actividadesDeComision.filter(
              (a) => a.estado === "programada",
            ).length,
          }
          return [comision.id, resumen] as const
        })
        setResumenes(Object.fromEntries(entradas))
      })
      .catch(() => {})
    return () => controller.abort()
  }, [materiaId, comisiones])

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Mis materias", to: "/actividad-evaluativa/materias" },
          { label: materia?.nombre ?? "…", to: `/actividad-evaluativa/materias/${materiaId}/actividades` },
          { label: "Comisiones" },
        ]}
      />
      <h1 className="text-lg font-semibold">Comisiones</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Elegí una comisión para ver sus estudiantes y generar el link de invitación.
      </p>

      <Card className="mt-4 overflow-x-auto py-0">
        <Table>
          <TableHeader>
            <tr>
              <TableHeaderCell>Horario</TableHeaderCell>
              <TableHeaderCell>Alumnos</TableHeaderCell>
              <TableHeaderCell>Actividades en curso</TableHeaderCell>
              <TableHeaderCell>Actividades planificadas</TableHeaderCell>
            </tr>
          </TableHeader>
          <TableBody>
            {comisiones === null ? (
              <TableEmptyRow colSpan={4}>Cargando…</TableEmptyRow>
            ) : comisiones.length === 0 ? (
              <TableEmptyRow colSpan={4}>
                Todavía no hay comisiones creadas para esta materia.
              </TableEmptyRow>
            ) : (
              comisiones.map((comision) => {
                const resumen = resumenes[comision.id]
                return (
                  <TableRow
                    key={comision.id}
                    className="cursor-pointer"
                    onClick={() => navigate(`/actividad-evaluativa/comisiones/${comision.id}`)}
                  >
                    <TableCell className="font-medium">{comision.horario}</TableCell>
                    <TableCell>{resumen?.cantidadEstudiantes ?? "…"}</TableCell>
                    <TableCell>{resumen?.actividadesEnCurso ?? "…"}</TableCell>
                    <TableCell>{resumen?.actividadesProgramadas ?? "…"}</TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  )
}
