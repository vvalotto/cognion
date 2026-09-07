import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Card } from "@/components/ui/card"
import { listarMaterias, type MateriaListItemResponse } from "@/lib/banco-preguntas-api"
import {
  listarComisionesPorMateria,
  type ComisionResumenResponse,
} from "@/lib/identidad-comisiones-api"

/**
 * Comisiones de una materia — vista Docente (`US-ADJ-26`), entry point hacia el detalle donde
 * genera el link de invitación. Reutiliza `listarComisionesPorMateria` (`US-4.2.2`), ya
 * accesible con rol `docente`.
 */
export function ComisionesDeMateria() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const navigate = useNavigate()

  const [materia, setMateria] = useState<MateriaListItemResponse | null>(null)
  const [comisiones, setComisiones] = useState<ComisionResumenResponse[] | null>(null)

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

      {comisiones === null ? (
        <p className="mt-4 text-sm text-muted-foreground">Cargando…</p>
      ) : comisiones.length === 0 ? (
        <p className="mt-4 text-sm text-muted-foreground">
          Todavía no hay comisiones creadas para esta materia.
        </p>
      ) : (
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {comisiones.map((comision) => (
            <Card
              key={comision.id}
              role="button"
              tabIndex={0}
              className="cursor-pointer p-5 transition-colors hover:border-primary"
              onClick={() => navigate(`/actividad-evaluativa/comisiones/${comision.id}`)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  navigate(`/actividad-evaluativa/comisiones/${comision.id}`)
                }
              }}
            >
              <p className="font-semibold">{comision.horario}</p>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
