import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { eliminarCuenta, obtenerCuenta, type CuentaDetalleResponse } from "@/lib/cuentas-api"

/**
 * Pantalla de confirmación de eliminación de una cuenta — mismo patrón que
 * `EliminarMateria.tsx`/`EliminarComision.tsx`. Si tiene datos asociados (Comisiones
 * asignadas o creadas, evaluaciones rendidas), el backend la deshabilita en vez de borrarla —
 * de cualquier forma, deja de aparecer en el listado.
 */
export function EliminarCuenta() {
  const { usuarioId } = useParams<{ usuarioId: string }>()
  const navigate = useNavigate()

  const [cuenta, setCuenta] = useState<CuentaDetalleResponse | null>(null)

  useEffect(() => {
    if (!usuarioId) return undefined
    const controller = new AbortController()
    obtenerCuenta(usuarioId, controller.signal)
      .then((resultado) => setCuenta(resultado))
      .catch(() => {})
    return () => controller.abort()
  }, [usuarioId])

  async function handleEliminar() {
    if (!usuarioId) return
    await eliminarCuenta(usuarioId)
    void navigate("/cuentas")
  }

  function handleCancelar() {
    void navigate("/cuentas")
  }

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Administración" },
          { label: "Cuentas", to: "/cuentas" },
          { label: "Eliminar" },
        ]}
      />
      <h1 className="text-lg font-semibold">Eliminar cuenta</h1>

      <Card className="mt-4 p-4">
        <p className="text-sm text-muted-foreground">Cuenta a eliminar:</p>
        <p className="mt-1 font-medium">{cuenta?.nombre ?? "…"}</p>
        {cuenta && <p className="text-sm text-muted-foreground">{cuenta.email}</p>}
      </Card>

      <div
        role="alert"
        className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800"
      >
        <p>
          Si tiene datos asociados (Comisiones asignadas o creadas, evaluaciones rendidas), la
          cuenta se deshabilita en vez de borrarse — deja de poder iniciar sesión, pero no afecta
          lo que ya existe.
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
