import { useEffect, useState } from "react"
import { useNavigate } from "react-router"

import { listarCuentas, type CuentaResponse, type Estado } from "@/lib/cuentas-api"
import type { Rol } from "@/lib/session"

const ETIQUETA_ROL: Record<Rol, string> = {
  administrador: "Administrador",
  docente: "Docente",
  estudiante: "Estudiante",
}

const ETIQUETA_ESTADO: Record<Estado, string> = {
  activa: "Activa",
  bloqueada: "Bloqueada",
}

function estadoDe(cuenta: CuentaResponse): Estado {
  return cuenta.bloqueada ? "bloqueada" : "activa"
}

/** Pantalla de listado y filtro de cuentas (§2.1 `wireframes-cuentas-administracion.md`). */
export function Cuentas() {
  const navigate = useNavigate()

  const [cuentas, setCuentas] = useState<CuentaResponse[] | null>(null)
  const [rol, setRol] = useState<Rol | "">("")
  const [estado, setEstado] = useState<Estado | "">("")
  const [busqueda, setBusqueda] = useState("")

  useEffect(() => {
    let cancelado = false
    listarCuentas({
      rol: rol || undefined,
      estado: estado || undefined,
      busqueda: busqueda || undefined,
    }).then((resultado) => {
      if (!cancelado) setCuentas(resultado)
    })
    return () => {
      cancelado = true
    }
  }, [rol, estado, busqueda])

  function limpiarFiltros() {
    setRol("")
    setEstado("")
    setBusqueda("")
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Cuentas</h1>
        <button
          type="button"
          className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          onClick={() => navigate("/docentes/nuevo")}
        >
          + Nueva cuenta
        </button>
      </div>

      <div className="mt-4 flex flex-wrap items-end gap-3">
        <div>
          <label htmlFor="filtro-rol" className="text-sm text-muted-foreground">
            Rol
          </label>
          <select
            id="filtro-rol"
            value={rol}
            onChange={(e) => setRol(e.target.value as Rol | "")}
            className="mt-1 block rounded-md border border-border px-2 py-1 text-sm"
          >
            <option value="">Todos</option>
            <option value="docente">Docente</option>
            <option value="estudiante">Estudiante</option>
            <option value="administrador">Administrador</option>
          </select>
        </div>
        <div>
          <label htmlFor="filtro-estado" className="text-sm text-muted-foreground">
            Estado
          </label>
          <select
            id="filtro-estado"
            value={estado}
            onChange={(e) => setEstado(e.target.value as Estado | "")}
            className="mt-1 block rounded-md border border-border px-2 py-1 text-sm"
          >
            <option value="">Todos</option>
            <option value="activa">Activa</option>
            <option value="bloqueada">Bloqueada</option>
          </select>
        </div>
        <div>
          <label htmlFor="filtro-busqueda" className="text-sm text-muted-foreground">
            Búsqueda
          </label>
          <input
            id="filtro-busqueda"
            type="text"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Nombre o email"
            className="mt-1 block rounded-md border border-border px-2 py-1 text-sm"
          />
        </div>
        <button
          type="button"
          className="rounded-md border border-border px-3 py-1 text-sm hover:bg-accent"
          onClick={limpiarFiltros}
        >
          Limpiar filtros
        </button>
      </div>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border text-muted-foreground">
              <th className="py-2 pr-4">Nombre</th>
              <th className="py-2 pr-4">Email</th>
              <th className="py-2 pr-4">Rol</th>
              <th className="py-2 pr-4">Estado</th>
            </tr>
          </thead>
          <tbody>
            {cuentas === null ? (
              <tr>
                <td colSpan={4} className="py-4 text-muted-foreground">
                  Cargando…
                </td>
              </tr>
            ) : cuentas.length === 0 ? (
              <tr>
                <td colSpan={4} className="py-4 text-muted-foreground">
                  No hay cuentas que coincidan con los filtros.
                </td>
              </tr>
            ) : (
              cuentas.map((cuenta) => (
                <tr
                  key={cuenta.id}
                  className="cursor-pointer border-b border-border hover:bg-accent"
                  onClick={() => navigate(`/cuentas/${cuenta.id}`)}
                >
                  <td className="py-2 pr-4">{cuenta.nombre}</td>
                  <td className="py-2 pr-4">{cuenta.email}</td>
                  <td className="py-2 pr-4">{ETIQUETA_ROL[cuenta.perfil]}</td>
                  <td className="py-2 pr-4">{ETIQUETA_ESTADO[estadoDe(cuenta)]}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
