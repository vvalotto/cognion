import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
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
import {
  listarActividades,
  type ActividadResumenResponse,
  type EstadoActividad,
} from "@/lib/actividad-evaluativa-api"
import { listarMaterias, type MateriaListItemResponse } from "@/lib/banco-preguntas-api"
import {
  listarComisionesPorMateria,
  listarEstudiantesDeComision,
  type ComisionResumenResponse,
} from "@/lib/identidad-comisiones-api"

const ETIQUETA_ESTADO: Record<EstadoActividad, string> = {
  en_curso: "En curso",
  programada: "Programada",
  cerrada: "Cerrada",
}

const VARIANTE_ESTADO: Record<EstadoActividad, "estado-en-curso" | "estado-programada" | "estado-cerrada"> = {
  en_curso: "estado-en-curso",
  programada: "estado-programada",
  cerrada: "estado-cerrada",
}

type FiltroEstado = "abiertas" | "cerradas" | "todas"

const ETIQUETA_FILTRO: Record<FiltroEstado, string> = {
  abiertas: "Abiertas",
  cerradas: "Cerradas",
  todas: "Todas",
}

function coincideFiltro(actividad: ActividadResumenResponse, filtro: FiltroEstado): boolean {
  if (filtro === "todas") return true
  if (filtro === "cerradas") return actividad.estado === "cerrada"
  return actividad.estado !== "cerrada"
}

function formatearFecha(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function tituloDeActividad(actividad: ActividadResumenResponse): string {
  return actividad.titulo || `Actividad del ${formatearFecha(actividad.fechaApertura)}`
}

function comisionesDeActividad(
  actividad: ActividadResumenResponse,
  comisiones: ComisionResumenResponse[],
): string {
  if (actividad.comisionesIds.length === 0) return "Todas"
  return actividad.comisionesIds
    .map((id) => comisiones.find((c) => c.id === id)?.horario ?? id)
    .join(", ")
}

function estudiantesDeActividad(
  actividad: ActividadResumenResponse,
  comisiones: ComisionResumenResponse[],
  estudiantesPorComision: Record<string, number>,
): number {
  const comisionesObjetivo =
    actividad.comisionesIds.length === 0
      ? comisiones.map((c) => c.id)
      : actividad.comisionesIds
  return comisionesObjetivo.reduce((total, id) => total + (estudiantesPorComision[id] ?? 0), 0)
}

function conteoDeActividad(actividad: ActividadResumenResponse): string {
  if (actividad.estado === "programada") return "0 evaluaciones"
  if (actividad.estado === "cerrada") {
    const n = actividad.cantidadEvaluacionesFinalizadas
    return `${n} evaluaci${n === 1 ? "ón" : "ones"} finalizada${n === 1 ? "" : "s"}`
  }
  const n = actividad.cantidadEvaluacionesActivas
  return `${n} evaluaci${n === 1 ? "ón" : "ones"} activa${n === 1 ? "" : "s"}`
}

/** Pantalla "Actividades de una materia" del BC Actividad Evaluativa (`#doc-actividades`, `US-3.4.2`).
 *
 * Tabla con filtro de estado — por defecto solo abiertas (`en_curso`/`programada`), con
 * opción de consultar las cerradas, mismo patrón ya usado en Materias/Comisiones/Cuentas. */
export function Actividades() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const navigate = useNavigate()

  const [materia, setMateria] = useState<MateriaListItemResponse | null>(null)
  const [actividades, setActividades] = useState<ActividadResumenResponse[] | null>(null)
  const [filtroEstado, setFiltroEstado] = useState<FiltroEstado>("abiertas")
  const [comisiones, setComisiones] = useState<ComisionResumenResponse[]>([])
  const [estudiantesPorComision, setEstudiantesPorComision] = useState<Record<string, number>>({})

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
    listarActividades(materiaId, controller.signal)
      .then((resultado) => setActividades(resultado))
      .catch(() => {})
    return () => controller.abort()
  }, [materiaId])

  useEffect(() => {
    if (!materiaId) return undefined
    const controller = new AbortController()
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
        setEstudiantesPorComision(Object.fromEntries(conteos))
      })
      .catch(() => {})
    return () => controller.abort()
  }, [materiaId])

  const actividadesFiltradas = actividades?.filter((actividad) =>
    coincideFiltro(actividad, filtroEstado),
  )

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Mis materias", to: "/actividad-evaluativa/materias" },
          { label: materia?.nombre ?? "…" },
          { label: "Actividades" },
        ]}
      />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Actividades de período abierto</h1>
          {actividadesFiltradas !== undefined && (
            <p className="mt-1 text-sm text-muted-foreground">
              {actividadesFiltradas.length} actividad{actividadesFiltradas.length === 1 ? "" : "es"}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => navigate(`/actividad-evaluativa/materias/${materiaId}/comisiones`)}
          >
            Ver Comisiones
          </Button>
          <Button
            onClick={() => navigate(`/actividad-evaluativa/materias/${materiaId}/actividades/nueva`)}
          >
            + Nueva actividad
          </Button>
        </div>
      </div>

      <Card className="mt-4 p-4">
        <label
          htmlFor="filtro-estado-actividad"
          className="text-[11px] font-bold tracking-wide text-muted-foreground uppercase"
        >
          Estado
        </label>
        <select
          id="filtro-estado-actividad"
          value={filtroEstado}
          onChange={(e) => setFiltroEstado(e.target.value as FiltroEstado)}
          className="mt-1 block rounded-md border border-border px-2 py-1 text-sm"
        >
          {(Object.keys(ETIQUETA_FILTRO) as FiltroEstado[]).map((valor) => (
            <option key={valor} value={valor}>
              {ETIQUETA_FILTRO[valor]}
            </option>
          ))}
        </select>
      </Card>

      <Card className="mt-4 overflow-x-auto py-0">
        <Table>
          <TableHeader>
            <tr>
              <TableHeaderCell>Título</TableHeaderCell>
              <TableHeaderCell>Período</TableHeaderCell>
              <TableHeaderCell>Estado</TableHeaderCell>
              <TableHeaderCell>Comisiones</TableHeaderCell>
              <TableHeaderCell>Estudiantes</TableHeaderCell>
              <TableHeaderCell>Evaluaciones</TableHeaderCell>
            </tr>
          </TableHeader>
          <TableBody>
            {actividadesFiltradas === undefined ? (
              <TableEmptyRow colSpan={6}>Cargando…</TableEmptyRow>
            ) : actividades?.length === 0 ? (
              <TableEmptyRow colSpan={6}>
                Todavía no hay actividades creadas para esta materia.
              </TableEmptyRow>
            ) : actividadesFiltradas.length === 0 ? (
              <TableEmptyRow colSpan={6}>
                No hay actividades {ETIQUETA_FILTRO[filtroEstado].toLowerCase()} para esta
                materia.
              </TableEmptyRow>
            ) : (
              actividadesFiltradas.map((actividad) => (
                <TableRow
                  key={actividad.id}
                  className="cursor-pointer"
                  onClick={() => navigate(`/actividad-evaluativa/actividades/${actividad.id}`)}
                >
                  <TableCell className="font-medium">{tituloDeActividad(actividad)}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    Abre {formatearFecha(actividad.fechaApertura)} · Cierra{" "}
                    {formatearFecha(actividad.fechaCierre)}
                  </TableCell>
                  <TableCell>
                    <Badge variant={VARIANTE_ESTADO[actividad.estado]}>
                      {ETIQUETA_ESTADO[actividad.estado]}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {comisionesDeActividad(actividad, comisiones)}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {estudiantesDeActividad(actividad, comisiones, estudiantesPorComision)}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {conteoDeActividad(actividad)}
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
