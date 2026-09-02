import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import {
  obtenerActividad,
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
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function tituloDeActividad(actividad: ActividadResumenResponse): string {
  return actividad.titulo || `Actividad del ${formatearFecha(actividad.fechaApertura)}`
}

/** Detalle de una actividad, con acciones de extender plazo y cerrar (`#doc-detalle-actividad`, `US-3.4.4`). */
export function ActividadDetalle() {
  const { actividadId } = useParams<{ actividadId: string }>()
  const navigate = useNavigate()

  const [actividad, setActividad] = useState<ActividadResumenResponse | null>(null)
  const [materia, setMateria] = useState<MateriaListItemResponse | null>(null)

  useEffect(() => {
    if (!actividadId) return
    let cancelado = false
    obtenerActividad(actividadId).then((resultado) => {
      if (!cancelado) setActividad(resultado)
    })
    return () => {
      cancelado = true
    }
  }, [actividadId])

  useEffect(() => {
    if (!actividad) return
    let cancelado = false
    listarMaterias().then((materias) => {
      if (!cancelado) setMateria(materias.find((m) => m.id === actividad.materiaId) ?? null)
    })
    return () => {
      cancelado = true
    }
  }, [actividad])

  if (actividad === null) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Mis materias", to: "/actividad-evaluativa/materias" },
          {
            label: materia?.nombre ?? "…",
            to: `/actividad-evaluativa/materias/${actividad.materiaId}/actividades`,
          },
          {
            label: "Actividades",
            to: `/actividad-evaluativa/materias/${actividad.materiaId}/actividades`,
          },
          { label: tituloDeActividad(actividad) },
        ]}
      />
      <Button
        variant="outline"
        className="mb-2"
        onClick={() =>
          navigate(`/actividad-evaluativa/materias/${actividad.materiaId}/actividades`)
        }
      >
        ‹ Volver a actividades
      </Button>
      <div className="flex items-center gap-2">
        <h1 className="text-lg font-semibold">{tituloDeActividad(actividad)}</h1>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate(`/actividad-evaluativa/actividades/${actividad.id}/editar-titulo`)}
        >
          Editar título
        </Button>
      </div>
      <div className="mt-1">
        <Badge variant={VARIANTE_ESTADO[actividad.estado]}>{ETIQUETA_ESTADO[actividad.estado]}</Badge>
      </div>

      <Card className="mt-4 divide-y p-0">
        <div className="flex items-center justify-between px-4 py-3 text-sm">
          <span className="text-muted-foreground">Apertura</span>
          <span className="font-medium">{formatearFecha(actividad.fechaApertura)}</span>
        </div>
        <div className="flex items-center justify-between px-4 py-3 text-sm">
          <span className="text-muted-foreground">Cierre</span>
          <span className="font-medium">{formatearFecha(actividad.fechaCierre)}</span>
        </div>
        <div className="flex items-center justify-between px-4 py-3 text-sm">
          <span className="text-muted-foreground">Cantidad de preguntas</span>
          <span className="font-medium">{actividad.cantidadPreguntas}</span>
        </div>
        <div className="flex items-center justify-between px-4 py-3 text-sm">
          <span className="text-muted-foreground">Intentos permitidos</span>
          <span className="font-medium">{actividad.cantidadIntentosPermitidos}</span>
        </div>
        <div className="flex items-center justify-between px-4 py-3 text-sm">
          <span className="text-muted-foreground">Evaluaciones activas</span>
          <span className="font-medium">
            {actividad.cantidadEvaluacionesActivas} (en curso o suspendidas)
          </span>
        </div>
        <div className="flex items-center justify-between px-4 py-3 text-sm">
          <span className="text-muted-foreground">Evaluaciones finalizadas</span>
          <span className="font-medium">{actividad.cantidadEvaluacionesFinalizadas}</span>
        </div>
      </Card>

      {!actividad.cerradaManualmente && (
        <div className="mt-4 flex flex-col gap-2">
          <Button
            variant="outline"
            onClick={() =>
              navigate(`/actividad-evaluativa/actividades/${actividad.id}/extender-plazo`)
            }
          >
            Extender plazo
          </Button>
          <Button
            variant="destructive-solid"
            onClick={() => navigate(`/actividad-evaluativa/actividades/${actividad.id}/cerrar`)}
          >
            Cerrar actividad ahora
          </Button>
          <p className="mt-1 text-center text-xs text-muted-foreground">
            "Extender plazo" solo permite mover el cierre hacia adelante. Para acortarlo, no
            puede haber estudiantes con evaluaciones activas.
          </p>
        </div>
      )}
    </div>
  )
}
