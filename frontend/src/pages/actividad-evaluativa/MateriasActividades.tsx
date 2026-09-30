import { useEffect, useState } from "react"
import { useNavigate } from "react-router"

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
import { listarActividades } from "@/lib/actividad-evaluativa-api"
import { listarMaterias, type MateriaListItemResponse } from "@/lib/banco-preguntas-api"
import { listarComisionesPorMateria } from "@/lib/identidad-comisiones-api"

interface ResumenMateria {
  cantidadComisiones: number
  actividadesEnCurso: number
  actividadesProgramadas: number
  actividadesTotales: number
}

async function cargarResumen(materiaId: string, signal: AbortSignal): Promise<ResumenMateria> {
  const [comisiones, actividades] = await Promise.all([
    listarComisionesPorMateria(materiaId, signal),
    listarActividades(materiaId, signal),
  ])
  return {
    cantidadComisiones: comisiones.length,
    actividadesEnCurso: actividades.filter((a) => a.estado === "en_curso").length,
    actividadesProgramadas: actividades.filter((a) => a.estado === "programada").length,
    actividadesTotales: actividades.length,
  }
}

/** Pantalla "Mis materias" del BC Actividad Evaluativa (`#doc-materias`, `US-3.4.2`).
 *
 * Reutiliza `listarMaterias()` (`banco-preguntas-api.ts`, `US-2.1.9`) sin cambios — mismo dato
 * que `Materias.tsx` de Banco de Preguntas, con destino de navegación distinto. Tabla con
 * cantidad de Comisiones y de Actividades (en curso/planificadas/totales) por materia, mismo
 * patrón que el resto del portal Docente.
 */
export function MateriasActividades() {
  const navigate = useNavigate()
  const [materias, setMaterias] = useState<MateriaListItemResponse[] | null>(null)
  const [resumenes, setResumenes] = useState<Record<string, ResumenMateria>>({})

  useEffect(() => {
    const controller = new AbortController()
    listarMaterias(controller.signal)
      .then((resultado) => setMaterias(resultado))
      .catch(() => {})
    return () => controller.abort()
  }, [])

  useEffect(() => {
    if (!materias) return undefined
    const controller = new AbortController()
    Promise.all(
      materias.map((materia) =>
        cargarResumen(materia.id, controller.signal).then(
          (resumen) => [materia.id, resumen] as const,
        ),
      ),
    )
      .then((entradas) => setResumenes(Object.fromEntries(entradas)))
      .catch(() => {})
    return () => controller.abort()
  }, [materias])

  return (
    <div>
      <Breadcrumb items={[{ label: "Actividad evaluativa" }, { label: "Mis materias" }]} />
      <h1 className="text-lg font-semibold">Mis materias</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Elegí una materia para ver y gestionar sus actividades de período abierto.
      </p>

      <Card className="mt-4 overflow-x-auto py-0">
        <Table>
          <TableHeader>
            <tr>
              <TableHeaderCell>Nombre</TableHeaderCell>
              <TableHeaderCell>Comisiones</TableHeaderCell>
              <TableHeaderCell>Actividades en curso</TableHeaderCell>
              <TableHeaderCell>Actividades planificadas</TableHeaderCell>
              <TableHeaderCell>Actividades totales</TableHeaderCell>
            </tr>
          </TableHeader>
          <TableBody>
            {materias === null ? (
              <TableEmptyRow colSpan={5}>Cargando…</TableEmptyRow>
            ) : materias.length === 0 ? (
              <TableEmptyRow colSpan={5}>Todavía no hay materias creadas.</TableEmptyRow>
            ) : (
              materias.map((materia) => {
                const resumen = resumenes[materia.id]
                return (
                  <TableRow
                    key={materia.id}
                    className="cursor-pointer"
                    onClick={() =>
                      navigate(`/actividad-evaluativa/materias/${materia.id}/actividades`)
                    }
                  >
                    <TableCell className="font-medium">{materia.nombre}</TableCell>
                    <TableCell>{resumen?.cantidadComisiones ?? "…"}</TableCell>
                    <TableCell>{resumen?.actividadesEnCurso ?? "…"}</TableCell>
                    <TableCell>{resumen?.actividadesProgramadas ?? "…"}</TableCell>
                    <TableCell>{resumen?.actividadesTotales ?? "…"}</TableCell>
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
