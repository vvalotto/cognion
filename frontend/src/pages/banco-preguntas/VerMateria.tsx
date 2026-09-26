import { Eye } from "lucide-react"
import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Badge } from "@/components/ui/badge"
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
import { listarMaterias, type MateriaListItemResponse } from "@/lib/banco-preguntas-api"
import { listarCuentas, type CuentaResponse } from "@/lib/cuentas-api"
import {
  listarComisionesPorMateria,
  listarEstudiantesDeComision,
  type ComisionResumenResponse,
} from "@/lib/identidad-comisiones-api"

function Resumen({ valor, etiqueta }: { valor: string; etiqueta: string }) {
  return (
    <Card className="p-4 text-center">
      <p className="text-2xl font-semibold">{valor}</p>
      <p className="text-xs text-muted-foreground">{etiqueta}</p>
    </Card>
  )
}

/**
 * Detalle de solo lectura de una Materia — pensado para el Administrador, que no gestiona
 * el banco de preguntas (`Banco.tsx` sigue siendo exclusivo del Docente). Resumen de la materia
 * y sus Comisiones, activas e inactivas, con Docentes y estudiantes (revisión manual 2026-09-26).
 * Reutiliza `GET /materias`, `GET /materias/{id}/comisiones` y `GET /comisiones/{id}/estudiantes`.
 */
export function VerMateria() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const navigate = useNavigate()
  const [materia, setMateria] = useState<MateriaListItemResponse | null>(null)
  const [comisiones, setComisiones] = useState<ComisionResumenResponse[] | null>(null)
  const [docentes, setDocentes] = useState<CuentaResponse[]>([])
  const [estudiantes, setEstudiantes] = useState<Record<string, number>>({})

  useEffect(() => {
    if (!materiaId) return undefined
    const controller = new AbortController()
    listarMaterias(controller.signal, true)
      .then((materias) => setMateria(materias.find((m) => m.id === materiaId) ?? null))
      .catch(() => {})
    listarComisionesPorMateria(materiaId, controller.signal, true)
      .then(async (resultado) => {
        setComisiones(resultado)
        const conteos = await Promise.all(
          resultado.map((comision) =>
            listarEstudiantesDeComision(comision.id, controller.signal).then(
              (lista) => [comision.id, lista.length] as const,
            ),
          ),
        )
        setEstudiantes(Object.fromEntries(conteos))
      })
      .catch(() => {})
    listarCuentas({ rol: "docente" }, { pagina: 1, tamanioPagina: 100 }, controller.signal)
      .then((resultado) => setDocentes(resultado.cuentas))
      .catch(() => {})
    return () => controller.abort()
  }, [materiaId])

  function nombreDocente(docenteId: string): string {
    return docentes.find((docente) => docente.id === docenteId)?.nombre ?? "…"
  }

  const activas = comisiones?.filter((c) => c.activa).length ?? 0
  const totalEstudiantes = Object.values(estudiantes).reduce((suma, n) => suma + n, 0)

  return (
    <div>
      <Breadcrumb items={[{ label: "Materias", to: "/materias" }, { label: materia?.nombre ?? "…" }]} />
      <div className="flex items-center gap-3">
        <h1 className="text-lg font-semibold">{materia?.nombre ?? "Cargando…"}</h1>
        {materia && (
          <Badge variant={materia.activa ? "estado-activa" : "estado-inactiva"}>
            {materia.activa ? "Activa" : "Inactiva"}
          </Badge>
        )}
      </div>
      <p className="text-sm text-muted-foreground">Banco de preguntas y comisiones de la materia.</p>

      <div className="mt-4 grid grid-cols-3 gap-3">
        <Resumen valor={materia ? String(materia.cantidadPreguntasActivas) : "…"} etiqueta="Preguntas activas" />
        <Resumen
          valor={comisiones ? `${activas} de ${comisiones.length}` : "…"}
          etiqueta="Comisiones activas"
        />
        <Resumen valor={comisiones ? String(totalEstudiantes) : "…"} etiqueta="Estudiantes inscriptos" />
      </div>

      <h2 className="mt-6 mb-2 text-sm font-semibold">Comisiones</h2>
      <Card className="overflow-x-auto py-0">
        <Table>
          <TableHeader>
            <tr>
              <TableHeaderCell>Horario</TableHeaderCell>
              <TableHeaderCell>Docentes asignados</TableHeaderCell>
              <TableHeaderCell>Estudiantes</TableHeaderCell>
              <TableHeaderCell>Estado</TableHeaderCell>
              <TableHeaderCell></TableHeaderCell>
            </tr>
          </TableHeader>
          <TableBody>
            {comisiones === null ? (
              <TableEmptyRow colSpan={5}>Cargando…</TableEmptyRow>
            ) : comisiones.length === 0 ? (
              <TableEmptyRow colSpan={5}>Esta materia todavía no tiene comisiones.</TableEmptyRow>
            ) : (
              comisiones.map((comision) => (
                <TableRow
                  key={comision.id}
                  className="cursor-pointer"
                  onClick={() => navigate(`/comisiones/${comision.id}`)}
                >
                  <TableCell className="font-medium">{comision.horario}</TableCell>
                  <TableCell>
                    {comision.docentesAsignados.length === 0 ? (
                      <Badge variant="docente-sin-asignar">Sin docente asignado</Badge>
                    ) : (
                      comision.docentesAsignados.map((docenteId) => (
                        <Badge key={docenteId} variant="docente-asignado" className="mr-1">
                          {nombreDocente(docenteId)}
                        </Badge>
                      ))
                    )}
                  </TableCell>
                  <TableCell>{estudiantes[comision.id] ?? "…"}</TableCell>
                  <TableCell>
                    <Badge variant={comision.activa ? "estado-activa" : "estado-inactiva"}>
                      {comision.activa ? "Activa" : "Inactiva"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <RowActionButton
                      label="Ver detalle"
                      icon={Eye}
                      onClick={(event) => {
                        event.stopPropagation()
                        navigate(`/comisiones/${comision.id}`)
                      }}
                    />
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  )
}
