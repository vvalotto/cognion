import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import {
  listarActividades,
  type ActividadResumenResponse,
  type EstadoActividad,
} from "@/lib/actividad-evaluativa-api"
import { listarMaterias, type MateriaListItemResponse } from "@/lib/banco-preguntas-api"

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

function conteoDeActividad(actividad: ActividadResumenResponse): string {
  if (actividad.estado === "programada") return "0 evaluaciones"
  if (actividad.estado === "cerrada") {
    const n = actividad.cantidadEvaluacionesFinalizadas
    return `${n} evaluaci${n === 1 ? "ón" : "ones"} finalizada${n === 1 ? "" : "s"}`
  }
  const n = actividad.cantidadEvaluacionesActivas
  return `${n} evaluaci${n === 1 ? "ón" : "ones"} activa${n === 1 ? "" : "s"}`
}

/** Pantalla "Actividades de una materia" del BC Actividad Evaluativa (`#doc-actividades`, `US-3.4.2`). */
export function Actividades() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const navigate = useNavigate()

  const [materia, setMateria] = useState<MateriaListItemResponse | null>(null)
  const [actividades, setActividades] = useState<ActividadResumenResponse[] | null>(null)

  useEffect(() => {
    let cancelado = false
    listarMaterias().then((materias) => {
      if (!cancelado) setMateria(materias.find((m) => m.id === materiaId) ?? null)
    })
    return () => {
      cancelado = true
    }
  }, [materiaId])

  useEffect(() => {
    if (!materiaId) return
    let cancelado = false
    listarActividades(materiaId).then((resultado) => {
      if (!cancelado) setActividades(resultado)
    })
    return () => {
      cancelado = true
    }
  }, [materiaId])

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
          {actividades !== null && (
            <p className="mt-1 text-sm text-muted-foreground">
              {actividades.length} actividad{actividades.length === 1 ? "" : "es"}
            </p>
          )}
        </div>
        <Button
          onClick={() => navigate(`/actividad-evaluativa/materias/${materiaId}/actividades/nueva`)}
        >
          + Nueva actividad
        </Button>
      </div>

      {actividades === null ? (
        <p className="mt-4 text-sm text-muted-foreground">Cargando…</p>
      ) : actividades.length === 0 ? (
        <p className="mt-4 text-sm text-muted-foreground">
          Todavía no hay actividades creadas para esta materia.
        </p>
      ) : (
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {actividades.map((actividad) => (
            <Card
              key={actividad.id}
              role="button"
              tabIndex={0}
              className="cursor-pointer p-5 transition-colors hover:border-primary"
              onClick={() => navigate(`/actividad-evaluativa/actividades/${actividad.id}`)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  navigate(`/actividad-evaluativa/actividades/${actividad.id}`)
                }
              }}
            >
              <p className="font-semibold">{tituloDeActividad(actividad)}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Abre {formatearFecha(actividad.fechaApertura)} · Cierra{" "}
                {formatearFecha(actividad.fechaCierre)}
              </p>
              <div className="mt-3 flex items-center gap-2">
                <Badge variant={VARIANTE_ESTADO[actividad.estado]}>
                  {ETIQUETA_ESTADO[actividad.estado]}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {conteoDeActividad(actividad)}
                </span>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
