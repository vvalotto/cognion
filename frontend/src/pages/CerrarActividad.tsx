import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Button } from "@/components/ui/button"
import {
  cerrarActividad,
  obtenerActividad,
  type ActividadResumenResponse,
} from "@/lib/actividad-evaluativa-api"

function tituloDeActividad(actividad: ActividadResumenResponse): string {
  return actividad.titulo || `Actividad del ${new Date(actividad.fechaApertura).toLocaleString()}`
}

/** Confirmación de cierre manual de una actividad (`#doc-cerrar-actividad`, `US-3.4.4`). */
export function CerrarActividad() {
  const { actividadId } = useParams<{ actividadId: string }>()
  const navigate = useNavigate()

  const [actividad, setActividad] = useState<ActividadResumenResponse | null>(null)

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

  async function handleCerrar() {
    if (!actividadId) return
    await cerrarActividad(actividadId)
    void navigate(`/actividad-evaluativa/actividades/${actividadId}`)
  }

  function handleCancelar() {
    void navigate(`/actividad-evaluativa/actividades/${actividadId}`)
  }

  if (actividad === null) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Mis materias", to: "/actividad-evaluativa/materias" },
          {
            label: tituloDeActividad(actividad),
            to: `/actividad-evaluativa/actividades/${actividad.id}`,
          },
          { label: "Cerrar actividad" },
        ]}
      />
      <h1 className="text-lg font-semibold">Cerrar actividad ahora</h1>
      <p className="mt-1 text-sm text-muted-foreground">{tituloDeActividad(actividad)}</p>

      <div
        role="alert"
        className="mt-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
      >
        <p className="font-medium">Acción terminal, no se puede deshacer</p>
        <p>
          Las {actividad.cantidadEvaluacionesActivas} evaluaciones en curso o suspendidas se
          finalizan de inmediato, tal como están respondidas hasta ahora. No se puede volver a
          abrir esta actividad ni extender su plazo después.
        </p>
      </div>

      <p className="mt-4 text-sm text-muted-foreground">
        Usalo cuando la actividad ya cumplió su propósito antes de lo previsto (ej. toda la
        clase ya respondió) — la mayoría de las actividades no necesita esta acción y
        simplemente llega a su fecha de cierre.
      </p>

      <div className="mt-4 flex gap-2">
        <Button variant="destructive-solid" onClick={handleCerrar}>
          Sí, cerrar actividad ahora
        </Button>
        <Button variant="outline" onClick={handleCancelar}>
          Cancelar
        </Button>
      </div>
    </div>
  )
}
