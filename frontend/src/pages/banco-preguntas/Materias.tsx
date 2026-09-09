import { Eye, Pencil, RotateCcw, Trash2 } from "lucide-react"
import { useEffect, useState } from "react"
import { useNavigate } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
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
import {
  activarMateria,
  listarMaterias,
  type MateriaListItemResponse,
} from "@/lib/banco-preguntas-api"
import { getSession } from "@/lib/session"

/**
 * Pantalla de listado de materias (§2.1 `wireframes-banco-preguntas.md`) — consume
 * `GET /materias`. Tabla con acciones explícitas por fila, mismo patrón que `Cuentas.tsx`.
 *
 * El Administrador no gestiona el banco de preguntas (`Banco.tsx` sigue siendo exclusivo
 * del Docente) — ve "Ver" (detalle de solo lectura, `VerMateria.tsx`) en vez de "Ver banco".
 */
export function Materias() {
  const navigate = useNavigate()
  const [materias, setMaterias] = useState<MateriaListItemResponse[] | null>(null)
  const esDocente = getSession()?.rol === "docente"

  useEffect(() => {
    const controller = new AbortController()
    listarMaterias(controller.signal, true)
      .then((resultado) => setMaterias(resultado))
      .catch(() => {})
    return () => controller.abort()
  }, [])

  async function handleActivar(materiaId: string) {
    await activarMateria(materiaId)
    setMaterias(
      (actual) =>
        actual?.map((m) => (m.id === materiaId ? { ...m, activa: true } : m)) ?? actual,
    )
  }

  return (
    <div>
      <Breadcrumb items={[{ label: "Banco de preguntas" }, { label: "Materias" }]} />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Materias</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Elegí una materia para ver y cargar su banco de preguntas.
          </p>
        </div>
        <Button onClick={() => navigate("/materias/nueva")}>+ Nueva materia</Button>
      </div>

      <Card className="mt-4 overflow-x-auto py-0">
        <Table>
          <TableHeader>
            <tr>
              <TableHeaderCell>Nombre</TableHeaderCell>
              <TableHeaderCell>Preguntas activas</TableHeaderCell>
              <TableHeaderCell>Estado</TableHeaderCell>
              <TableHeaderCell></TableHeaderCell>
            </tr>
          </TableHeader>
          <TableBody>
            {materias === null ? (
              <TableEmptyRow colSpan={4}>Cargando…</TableEmptyRow>
            ) : materias.length === 0 ? (
              <TableEmptyRow colSpan={4}>Todavía no hay materias creadas.</TableEmptyRow>
            ) : (
              materias.map((materia) => {
                const rutaVer = esDocente
                  ? `/materias/${materia.id}/banco`
                  : `/materias/${materia.id}/ver`
                return (
                  <TableRow
                    key={materia.id}
                    className="cursor-pointer"
                    onClick={() => navigate(rutaVer)}
                  >
                    <TableCell className="font-medium">{materia.nombre}</TableCell>
                    <TableCell>{materia.cantidadPreguntasActivas}</TableCell>
                    <TableCell>
                      <Badge variant={materia.activa ? "estado-activa" : "estado-inactiva"}>
                        {materia.activa ? "Activa" : "Inactiva"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1.5">
                        <RowActionButton
                          label={esDocente ? "Ver banco" : "Ver"}
                          icon={Eye}
                          onClick={(e) => {
                            e.stopPropagation()
                            navigate(rutaVer)
                          }}
                        />
                        {materia.activa ? (
                          <>
                            <RowActionButton
                              label="Editar"
                              icon={Pencil}
                              onClick={(e) => {
                                e.stopPropagation()
                                navigate(`/materias/${materia.id}/editar`)
                              }}
                            />
                            <RowActionButton
                              label="Eliminar"
                              icon={Trash2}
                              variant="destructive"
                              onClick={(e) => {
                                e.stopPropagation()
                                navigate(`/materias/${materia.id}/eliminar`)
                              }}
                            />
                          </>
                        ) : (
                          <RowActionButton
                            label="Activar"
                            icon={RotateCcw}
                            onClick={(e) => {
                              e.stopPropagation()
                              void handleActivar(materia.id)
                            }}
                          />
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  )
}
