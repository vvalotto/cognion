import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import {
  eliminarComision,
  obtenerComision,
  type ComisionDetalleResponse,
} from "@/lib/identidad-comisiones-api"

/**
 * Pantalla de confirmación de eliminación de una comisión — mismo patrón que
 * `EliminarPregunta.tsx` (§2.8 `wireframes-banco-preguntas.md`). Si tiene estudiantes
 * inscriptos, el backend la deshabilita en vez de borrarla — de cualquier forma, deja de
 * aparecer en el listado.
 */
export function EliminarComision() {
  const { comisionId } = useParams<{ comisionId: string }>()
  const navigate = useNavigate()

  const [comision, setComision] = useState<ComisionDetalleResponse | null>(null)

  useEffect(() => {
    if (!comisionId) return undefined
    const controller = new AbortController()
    obtenerComision(comisionId, controller.signal).then(setComision).catch(() => {})
    return () => controller.abort()
  }, [comisionId])

  async function handleEliminar() {
    if (!comisionId) return
    await eliminarComision(comisionId)
    void navigate("/comisiones")
  }

  function handleCancelar() {
    void navigate(`/comisiones/${comisionId}`)
  }

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Comisiones", to: "/comisiones" },
          { label: comision?.horario ?? "…", to: comisionId ? `/comisiones/${comisionId}` : undefined },
          { label: "Eliminar" },
        ]}
      />
      <h1 className="text-lg font-semibold">Eliminar comisión</h1>

      <Card className="mt-4 p-4">
        <p className="text-sm text-muted-foreground">Comisión a eliminar:</p>
        <p className="mt-1 font-medium">{comision?.horario ?? "…"}</p>
      </Card>

      <div
        role="alert"
        className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800"
      >
        <p>
          Si tiene estudiantes inscriptos, la comisión se deshabilita en vez de borrarse — deja
          de estar disponible para nuevas inscripciones, pero no afecta a quienes ya cursan.
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
