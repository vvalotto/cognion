import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import {
  eliminarMateria,
  listarMaterias,
  type MateriaListItemResponse,
} from "@/lib/banco-preguntas-api"

/**
 * Pantalla de confirmación de eliminación de una materia — mismo patrón que
 * `EliminarPregunta.tsx`. Si tiene preguntas cargadas o comisiones asociadas, el backend la
 * deshabilita en vez de borrarla — de cualquier forma, deja de aparecer en el listado.
 */
export function EliminarMateria() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const navigate = useNavigate()

  const [materia, setMateria] = useState<MateriaListItemResponse | null>(null)

  useEffect(() => {
    if (!materiaId) return undefined
    const controller = new AbortController()
    listarMaterias(controller.signal)
      .then((materias) => setMateria(materias.find((m) => m.id === materiaId) ?? null))
      .catch(() => {})
    return () => controller.abort()
  }, [materiaId])

  async function handleEliminar() {
    if (!materiaId) return
    await eliminarMateria(materiaId)
    void navigate("/materias")
  }

  function handleCancelar() {
    void navigate("/materias")
  }

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Banco de preguntas" },
          { label: "Materias", to: "/materias" },
          { label: "Eliminar" },
        ]}
      />
      <h1 className="text-lg font-semibold">Eliminar materia</h1>

      <Card className="mt-4 p-4">
        <p className="text-sm text-muted-foreground">Materia a eliminar:</p>
        <p className="mt-1 font-medium">{materia?.nombre ?? "…"}</p>
      </Card>

      <div
        role="alert"
        className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800"
      >
        <p>
          Si tiene preguntas cargadas o Comisiones asociadas, la materia se deshabilita en vez
          de borrarse — deja de estar disponible para nuevas Comisiones, pero no afecta lo que
          ya existe.
        </p>
      </div>

      <div className="mt-4 flex gap-2">
        <Button variant="destructive-solid" onClick={handleEliminar}>
          Sí, eliminar
        </Button>
        <Button variant="outline" onClick={handleCancelar}>
          Cancelar
        </Button>
      </div>
    </div>
  )
}
