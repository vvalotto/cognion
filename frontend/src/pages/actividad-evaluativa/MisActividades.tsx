import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Badge } from "@/components/ui/badge"
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
  listarActividadesVisibles,
  type ActividadVisibleResponse,
  type EstadoVisible,
} from "@/lib/actividad-evaluativa-api"
import { listarMisMaterias, type MateriaEstudianteResponse } from "@/lib/identidad-estudiante-api"

const ETIQUETA_ESTADO: Record<EstadoVisible, string> = {
  pendiente: "Pendiente de responder",
  todavia_no_abrio: "Todavía no abrió",
  finalizada: "Finalizada — ver revisión",
}

const VARIANTE_ESTADO: Record<EstadoVisible, "visible-pendiente" | "visible-todavia-no-abrio" | "visible-finalizada"> = {
  pendiente: "visible-pendiente",
  todavia_no_abrio: "visible-todavia-no-abrio",
  finalizada: "visible-finalizada",
}

function formatearFecha(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function tituloDeActividad(actividad: ActividadVisibleResponse): string {
  return actividad.titulo || `Actividad del ${formatearFecha(actividad.fechaApertura)}`
}

/** Pantalla "Actividades de una materia" del Estudiante (`#est-actividades`, `US-3.4.5`). */
export function MisActividades() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const navigate = useNavigate()

  const [materia, setMateria] = useState<MateriaEstudianteResponse | null>(null)
  const [actividades, setActividades] = useState<ActividadVisibleResponse[] | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    listarMisMaterias(controller.signal)
      .then((materias) => setMateria(materias.find((m) => m.id === materiaId) ?? null))
      .catch(() => {})
    return () => controller.abort()
  }, [materiaId])

  useEffect(() => {
    if (!materiaId) return undefined
    const controller = new AbortController()
    listarActividadesVisibles(materiaId, controller.signal)
      .then((resultado) => setActividades(resultado))
      .catch(() => {})
    return () => controller.abort()
  }, [materiaId])

  function irA(actividad: ActividadVisibleResponse) {
    if (actividad.estado === "todavia_no_abrio") {
      navigate(`/mis-actividades/${actividad.id}/fuera-de-periodo`, {
        state: { titulo: tituloDeActividad(actividad), fechaApertura: actividad.fechaApertura },
      })
      return
    }
    if (actividad.estado === "finalizada" && actividad.evaluacionId) {
      navigate(`/mis-actividades/evaluaciones/${actividad.evaluacionId}/revision`)
      return
    }
    navigate(`/mis-actividades/actividades/${actividad.id}/rendir`)
  }

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Mis materias", to: "/mis-actividades/materias" },
          { label: materia?.nombre ?? "…" },
          { label: "Actividades" },
        ]}
      />
      <h1 className="text-lg font-semibold">Actividades de período abierto</h1>

      <Card className="mt-4 overflow-x-auto py-0">
        <Table>
          <TableHeader>
            <tr>
              <TableHeaderCell>Título</TableHeaderCell>
              <TableHeaderCell>Período</TableHeaderCell>
              <TableHeaderCell>Estado</TableHeaderCell>
            </tr>
          </TableHeader>
          <TableBody>
            {actividades === null ? (
              <TableEmptyRow colSpan={3}>Cargando…</TableEmptyRow>
            ) : actividades.length === 0 ? (
              <TableEmptyRow colSpan={3}>
                Todavía no hay actividades disponibles para esta materia.
              </TableEmptyRow>
            ) : (
              actividades.map((actividad) => (
                <TableRow
                  key={actividad.id}
                  className="cursor-pointer"
                  onClick={() => irA(actividad)}
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
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  )
}
