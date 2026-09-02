import { useEffect, useState, type FormEvent } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  modificarPeriodoDisponibilidad,
  obtenerActividad,
  type ActividadResumenResponse,
} from "@/lib/actividad-evaluativa-api"
import { ApiError } from "@/lib/api-client"

function tituloDeActividad(actividad: ActividadResumenResponse): string {
  return actividad.titulo || `Actividad del ${new Date(actividad.fechaApertura).toLocaleString()}`
}

/** Formulario de extensión/acortamiento del plazo de una actividad (`#doc-extender-plazo`, `US-3.4.4`). */
export function ExtenderPlazo() {
  const { actividadId } = useParams<{ actividadId: string }>()
  const navigate = useNavigate()

  const [actividad, setActividad] = useState<ActividadResumenResponse | null>(null)
  const [nuevaFechaCierre, setNuevaFechaCierre] = useState("")
  const [error, setError] = useState<string | null>(null)

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

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    if (!actividadId || !nuevaFechaCierre) return
    try {
      await modificarPeriodoDisponibilidad(actividadId, nuevaFechaCierre)
    } catch (err) {
      if (err instanceof ApiError && err.status === 422) {
        setError(err.message)
        return
      }
      throw err
    }
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
          { label: "Extender plazo" },
        ]}
      />
      <h1 className="text-lg font-semibold">Modificar período de disponibilidad</h1>
      <p className="mt-1 text-sm text-muted-foreground">{tituloDeActividad(actividad)}</p>

      <div
        role="status"
        className="mb-4 mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800"
      >
        <p className="font-medium">Tiene efecto inmediato</p>
        <p>
          Los estudiantes con evaluaciones en curso o suspendidas pueden seguir respondiendo
          hasta el nuevo cierre.
        </p>
      </div>

      {error && (
        <div
          role="alert"
          className="mb-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          <p className="font-medium">{error}</p>
        </div>
      )}

      <Card>
        <CardContent>
          <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="ep-cierre-actual">Cierre actual</Label>
              <Input
                id="ep-cierre-actual"
                type="text"
                value={new Date(actividad.fechaCierre).toLocaleString()}
                disabled
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="ep-nuevo-cierre">Nuevo cierre</Label>
              <Input
                id="ep-nuevo-cierre"
                type="datetime-local"
                required
                value={nuevaFechaCierre}
                onChange={(event) => setNuevaFechaCierre(event.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Solo se puede acortar si no hay evaluaciones activas para esta actividad.
              </p>
            </div>
            <div className="flex gap-2">
              <Button type="submit">Guardar nuevo cierre</Button>
              <Button type="button" variant="outline" onClick={handleCancelar}>
                Cancelar
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
