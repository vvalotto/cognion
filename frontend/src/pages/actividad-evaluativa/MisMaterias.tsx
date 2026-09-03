import { useEffect, useState } from "react"
import { useNavigate } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { listarActividadesVisibles } from "@/lib/actividad-evaluativa-api"
import { listarMisMaterias, type MateriaEstudianteResponse } from "@/lib/identidad-estudiante-api"

interface MateriaConResumen extends MateriaEstudianteResponse {
  cantidadPendientes: number
}

/** Pantalla "Mis materias" del Estudiante (`#est-materias`, `US-3.4.5`).
 *
 * El Badge resumen ("N pendiente" / "Sin actividades disponibles") no lo expone el backend —
 * se deriva acá contando el estado `"pendiente"` de `listarActividadesVisibles()` por materia,
 * aceptable a esta escala (un Estudiante cursa una cantidad chica de materias).
 */
export function MisMaterias() {
  const navigate = useNavigate()
  const [materias, setMaterias] = useState<MateriaConResumen[] | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    listarMisMaterias(controller.signal)
      .then(async (resultado) => {
        const conResumen = await Promise.all(
          resultado.map(async (materia) => {
            const actividades = await listarActividadesVisibles(materia.id, controller.signal)
            const cantidadPendientes = actividades.filter((a) => a.estado === "pendiente").length
            return { ...materia, cantidadPendientes }
          }),
        )
        setMaterias(conResumen)
      })
      .catch(() => {})
    return () => controller.abort()
  }, [])

  return (
    <div>
      <Breadcrumb items={[{ label: "Actividad evaluativa" }, { label: "Mis materias" }]} />
      <h1 className="text-lg font-semibold">Mis materias</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Materias de tu comisión — elegí una para ver sus actividades.
      </p>

      {materias === null ? (
        <p className="mt-4 text-sm text-muted-foreground">Cargando…</p>
      ) : (
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {materias.map((materia) => (
            <Card
              key={materia.id}
              role="button"
              tabIndex={0}
              className="cursor-pointer p-5 transition-colors hover:border-primary"
              onClick={() => navigate(`/mis-actividades/materias/${materia.id}/actividades`)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  navigate(`/mis-actividades/materias/${materia.id}/actividades`)
                }
              }}
            >
              <p className="mb-2 text-xl">📘</p>
              <p className="font-semibold">{materia.nombre}</p>
              <div className="mt-3">
                {materia.cantidadPendientes > 0 ? (
                  <Badge variant="visible-pendiente">{materia.cantidadPendientes} pendiente{materia.cantidadPendientes === 1 ? "" : "s"}</Badge>
                ) : (
                  <Badge variant="visible-todavia-no-abrio">Sin actividades disponibles</Badge>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
