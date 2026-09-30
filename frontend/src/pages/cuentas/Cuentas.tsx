import { Eye, RotateCcw, Trash2 } from "lucide-react"
import { useEffect, useState } from "react"
import { useNavigate } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { RolBadge } from "@/components/RolBadge"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Pagination } from "@/components/ui/pagination"
import { RowActionButton } from "@/components/ui/row-action-button"
import {
  Table,
  TableBody,
  TableCell,
  TableEmptyRow,
  TableHeader,
  TableHeaderCell,
  TableRow,
} from "@/components/ui/table"
import { activarCuenta, listarCuentas, type CuentaResponse, type Estado } from "@/lib/cuentas-api"
import type { Rol } from "@/lib/session"

const TAMANIO_PAGINA = 20

const ETIQUETA_ESTADO: Record<Estado, string> = {
  activa: "Activa",
  bloqueada: "Bloqueada",
  inactiva: "Inactiva",
}

const VARIANTE_ESTADO: Record<Estado, "estado-activa" | "estado-bloqueada" | "estado-inactiva"> = {
  activa: "estado-activa",
  bloqueada: "estado-bloqueada",
  inactiva: "estado-inactiva",
}

function estadoDe(cuenta: CuentaResponse): Estado {
  if (cuenta.deshabilitada) return "inactiva"
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
    const controller = new AbortController()
    listarCuentas(
      {
        rol: rol || undefined,
        estado: estado || undefined,
        busqueda: busqueda || undefined,
      },
      { pagina, tamanioPagina: TAMANIO_PAGINA },
      controller.signal,
      true,
    )
      .then((resultado) => {
        setCuentas(resultado.cuentas)
        setTotal(resultado.total)
      })
      .catch(() => {})
    return () => controller.abort()
  }, [rol, estado, busqueda, pagina])

  function limpiarFiltros() {
    setRol("")
    setEstado("")
    setBusqueda("")
    setPagina(1)
  }

  async function handleActivar(id: string) {
    await activarCuenta(id)
    setCuentas(
      (actual) => actual?.map((c) => (c.id === id ? { ...c, deshabilitada: false } : c)) ?? actual,
    )
  }

  const totalPaginas = Math.ceil(total / TAMANIO_PAGINA)

  return (
    <div>
      <Breadcrumb items={[{ label: "Administración" }, { label: "Cuentas" }]} />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Cuentas</h1>
          {cuentas !== null && (
            <p className="text-sm text-muted-foreground">
              {total} {total === 1 ? "cuenta registrada" : "cuentas registradas"}
            </p>
          )}
        </div>
        <Button onClick={() => navigate("/docentes/nuevo")}>+ Nueva cuenta</Button>
      </div>

      <Card className="mt-4">
        <CardContent className="flex flex-wrap items-end gap-3 p-4">
          <div>
            <label
              htmlFor="filtro-rol"
              className="text-[11px] font-bold tracking-wide text-muted-foreground uppercase"
            >
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
            <label
              htmlFor="filtro-estado"
              className="text-[11px] font-bold tracking-wide text-muted-foreground uppercase"
            >
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
              <option value="inactiva">Inactiva</option>
            </select>
          </div>
          <div>
            <label
              htmlFor="filtro-busqueda"
              className="text-[11px] font-bold tracking-wide text-muted-foreground uppercase"
            >
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

      <Card className="mt-4 overflow-x-auto py-0">
        <Table>
          <TableHeader>
            <tr>
              <TableHeaderCell>Nombre</TableHeaderCell>
              <TableHeaderCell>Email</TableHeaderCell>
              <TableHeaderCell>Rol</TableHeaderCell>
              <TableHeaderCell>Estado</TableHeaderCell>
              <TableHeaderCell></TableHeaderCell>
            </tr>
          </TableHeader>
          <TableBody>
            {cuentas === null ? (
              <TableEmptyRow colSpan={5}>Cargando…</TableEmptyRow>
            ) : cuentas.length === 0 ? (
              <TableEmptyRow colSpan={5}>No hay cuentas que coincidan con los filtros.</TableEmptyRow>
            ) : (
              cuentas.map((cuenta) => (
                <TableRow
                  key={cuenta.id}
                  className="cursor-pointer"
                  onClick={() => navigate(`/cuentas/${cuenta.id}`)}
                >
                  <TableCell className="font-medium">{cuenta.nombre}</TableCell>
                  <TableCell>{cuenta.email}</TableCell>
                  <TableCell>
                    <RolBadge rol={cuenta.perfil} />
                  </TableCell>
                  <TableCell>
                    <Badge variant={VARIANTE_ESTADO[estadoDe(cuenta)]}>
                      {ETIQUETA_ESTADO[estadoDe(cuenta)]}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1.5">
                      <RowActionButton
                        label="Ver"
                        icon={Eye}
                        onClick={(e) => {
                          e.stopPropagation()
                          navigate(`/cuentas/${cuenta.id}`)
                        }}
                      />
                      {cuenta.deshabilitada ? (
                        <RowActionButton
                          label="Activar"
                          icon={RotateCcw}
                          onClick={(e) => {
                            e.stopPropagation()
                            void handleActivar(cuenta.id)
                          }}
                        />
                      ) : (
                        <RowActionButton
                          label="Eliminar"
                          icon={Trash2}
                          variant="destructive"
                          onClick={(e) => {
                            e.stopPropagation()
                            navigate(`/cuentas/${cuenta.id}/eliminar`)
                          }}
                        />
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>

      <Pagination pagina={pagina} totalPaginas={totalPaginas} onCambiarPagina={setPagina} />
    </div>
  )
}
