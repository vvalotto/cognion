import { useEffect, useState } from "react"
import { useNavigate } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Pagination } from "@/components/ui/pagination"
import { listarCuentas, type CuentaResponse, type Estado } from "@/lib/cuentas-api"
import type { Rol } from "@/lib/session"

const TAMANIO_PAGINA = 20

const ETIQUETA_ROL: Record<Rol, string> = {
  administrador: "Administrador",
  docente: "Docente",
  estudiante: "Estudiante",
}

const VARIANTE_ROL: Record<Rol, "rol-docente" | "rol-estudiante" | "rol-admin"> = {
  docente: "rol-docente",
  estudiante: "rol-estudiante",
  administrador: "rol-admin",
}

const ETIQUETA_ESTADO: Record<Estado, string> = {
  activa: "Activa",
  bloqueada: "Bloqueada",
}

const VARIANTE_ESTADO: Record<Estado, "estado-activa" | "estado-bloqueada"> = {
  activa: "estado-activa",
  bloqueada: "estado-bloqueada",
}

function estadoDe(cuenta: CuentaResponse): Estado {
  return cuenta.bloqueada ? "bloqueada" : "activa"
}

/** Pantalla de listado y filtro de cuentas (§2.1 `wireframes-cuentas-administracion.md`). */
export function Cuentas() {
  const navigate = useNavigate()

  const [cuentas, setCuentas] = useState<CuentaResponse[] | null>(null)
  const [total, setTotal] = useState(0)
  const [pagina, setPagina] = useState(1)
  const [rol, setRol] = useState<Rol | "">("")
  const [estado, setEstado] = useState<Estado | "">("")
  const [busqueda, setBusqueda] = useState("")

  useEffect(() => {
    let cancelado = false
    listarCuentas(
      {
        rol: rol || undefined,
        estado: estado || undefined,
        busqueda: busqueda || undefined,
      },
      { pagina, tamanioPagina: TAMANIO_PAGINA },
    ).then((resultado) => {
      if (cancelado) return
      setCuentas(resultado.cuentas)
      setTotal(resultado.total)
    })
    return () => {
      cancelado = true
    }
  }, [rol, estado, busqueda, pagina])

  function limpiarFiltros() {
    setRol("")
    setEstado("")
    setBusqueda("")
    setPagina(1)
  }

  const totalPaginas = Math.ceil(total / TAMANIO_PAGINA)

  return (
    <div>
      <Breadcrumb items={[{ label: "Administración" }, { label: "Cuentas" }]} />
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Cuentas</h1>
        <Button onClick={() => navigate("/docentes/nuevo")}>+ Nueva cuenta</Button>
      </div>

      <Card className="mt-4">
        <CardContent className="flex flex-wrap items-end gap-3 p-4">
          <div>
            <label htmlFor="filtro-rol" className="text-sm text-muted-foreground">
              Rol
            </label>
            <select
              id="filtro-rol"
              value={rol}
              onChange={(e) => {
                setRol(e.target.value as Rol | "")
                setPagina(1)
              }}
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
              onChange={(e) => {
                setEstado(e.target.value as Estado | "")
                setPagina(1)
              }}
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
              onChange={(e) => {
                setBusqueda(e.target.value)
                setPagina(1)
              }}
              placeholder="Nombre o email"
              className="mt-1 block rounded-md border border-border px-2 py-1 text-sm"
            />
          </div>
          <Button type="button" variant="outline" size="sm" onClick={limpiarFiltros}>
            Limpiar filtros
          </Button>
        </CardContent>
      </Card>

      <Card className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border bg-muted text-muted-foreground">
              <th className="py-2 pr-4 pl-4">Nombre</th>
              <th className="py-2 pr-4">Email</th>
              <th className="py-2 pr-4">Rol</th>
              <th className="py-2 pr-4">Estado</th>
              <th className="py-2 pr-4"></th>
            </tr>
          </thead>
          <tbody>
            {cuentas === null ? (
              <tr>
                <td colSpan={5} className="py-4 pl-4 text-muted-foreground">
                  Cargando…
                </td>
              </tr>
            ) : cuentas.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-4 pl-4 text-muted-foreground">
                  No hay cuentas que coincidan con los filtros.
                </td>
              </tr>
            ) : (
              cuentas.map((cuenta) => (
                <tr
                  key={cuenta.id}
                  className="cursor-pointer border-b border-border last:border-0 hover:bg-accent"
                  onClick={() => navigate(`/cuentas/${cuenta.id}`)}
                >
                  <td className="py-3 pr-4 pl-4">{cuenta.nombre}</td>
                  <td className="py-3 pr-4">{cuenta.email}</td>
                  <td className="py-3 pr-4">
                    <Badge variant={VARIANTE_ROL[cuenta.perfil]}>
                      {ETIQUETA_ROL[cuenta.perfil]}
                    </Badge>
                  </td>
                  <td className="py-3 pr-4">
                    <Badge variant={VARIANTE_ESTADO[estadoDe(cuenta)]}>
                      {ETIQUETA_ESTADO[estadoDe(cuenta)]}
                    </Badge>
                  </td>
                  <td className="py-3 pr-4">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation()
                        navigate(`/cuentas/${cuenta.id}`)
                      }}
                    >
                      Ver
                    </Button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </Card>

      <Pagination pagina={pagina} totalPaginas={totalPaginas} onCambiarPagina={setPagina} />
    </div>
  )
}
