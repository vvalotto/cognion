import { useEffect, useState } from "react"
import { useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Card } from "@/components/ui/card"
import { listarMaterias, type MateriaListItemResponse } from "@/lib/banco-preguntas-api"

/**
 * Detalle de solo lectura de una Materia — pensado para el Administrador, que no gestiona
 * el banco de preguntas (`Banco.tsx` sigue siendo exclusivo del Docente). Reutiliza
 * `GET /materias` (sin endpoint nuevo), igual que `EditarMateria.tsx`.
 */
export function VerMateria() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const [materia, setMateria] = useState<MateriaListItemResponse | null>(null)

  useEffect(() => {
    if (!materiaId) return undefined
    const controller = new AbortController()
    listarMaterias(controller.signal)
      .then((materias) => setMateria(materias.find((m) => m.id === materiaId) ?? null))
      .catch(() => {})
    return () => controller.abort()
  }, [materiaId])

  return (
    <div>
      <Breadcrumb items={[{ label: "Materias", to: "/materias" }, { label: materia?.nombre ?? "…" }]} />
      <h1 className="text-lg font-semibold">{materia?.nombre ?? "Cargando…"}</h1>

      <Card className="mt-4 p-7 text-sm">
        <dl className="divide-y divide-border">
          <div className="flex items-center justify-between py-2.5">
            <dt className="text-muted-foreground">Preguntas activas</dt>
            <dd>{materia?.cantidadPreguntasActivas ?? "…"}</dd>
          </div>
        </dl>
      </Card>
    </div>
  )
}
