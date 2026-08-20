import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Button } from "@/components/ui/button"
import { obtenerCuenta, type CuentaDetalleResponse } from "@/lib/cuentas-api"
import type { Rol } from "@/lib/session"

const ETIQUETA_ROL: Record<Rol, string> = {
  administrador: "Administrador",
  docente: "Docente",
  estudiante: "Estudiante",
}

/** Pantalla de detalle de cuenta (§2.2 `wireframes-cuentas-administracion.md`). */
export function CuentaDetalle() {
  const { usuarioId } = useParams<{ usuarioId: string }>()
  const navigate = useNavigate()

  const [cuenta, setCuenta] = useState<CuentaDetalleResponse | null>(null)

  useEffect(() => {
    if (!usuarioId) return
    let cancelado = false
    obtenerCuenta(usuarioId).then((resultado) => {
      if (!cancelado) setCuenta(resultado)
    })
    return () => {
      cancelado = true
    }
  }, [usuarioId])

  if (!cuenta) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  return (
    <div>
      <p className="text-sm text-muted-foreground">
        Administración › Cuentas › {cuenta.nombre}
      </p>
      <h1 className="text-lg font-semibold">{cuenta.nombre}</h1>

      {cuenta.bloqueada && (
        <div
          role="alert"
          className="mt-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          <p className="font-medium">Esta cuenta está bloqueada.</p>
          <p className="mt-1">
            Se bloqueó automáticamente tras 3 intentos fallidos de inicio de sesión
            consecutivos.
          </p>
        </div>
      )}

      <div className="mt-4 rounded-lg border border-border p-4 text-sm">
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2">
          <dt className="text-muted-foreground">Email</dt>
          <dd>{cuenta.email}</dd>
          <dt className="text-muted-foreground">Rol</dt>
          <dd>{ETIQUETA_ROL[cuenta.perfil]}</dd>
          <dt className="text-muted-foreground">Estado</dt>
          <dd>{cuenta.bloqueada ? "Bloqueada" : "Activa"}</dd>
          {cuenta.perfil === "estudiante" && cuenta.comisionId && (
            <>
              <dt className="text-muted-foreground">Comisión</dt>
              <dd>{cuenta.comisionId}</dd>
            </>
          )}
          <dt className="text-muted-foreground">Fecha de creación</dt>
          <dd>{new Date(cuenta.creadoEn).toLocaleDateString()}</dd>
        </dl>
      </div>

      <Button
        className="mt-4"
        onClick={() => navigate(`/cuentas/${cuenta.id}/resetear-password`)}
      >
        Resetear contraseña y desbloquear
      </Button>
    </div>
  )
}
