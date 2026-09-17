import { useEffect, useMemo, useState } from "react"
import { useNavigate } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Pagination } from "@/components/ui/pagination"
import {
  obtenerDesempenoPorComision,
  type DesempenoComisionFilaResponse,
} from "@/lib/analytics-api"
import { listarMaterias, type MateriaListItemResponse } from "@/lib/banco-preguntas-api"
import {
  listarComisionesPorMateria,
  type ComisionResumenResponse,
} from "@/lib/identidad-comisiones-api"

type Columna = "nombre" | "porcentajeAciertosAcumulado" | "actividadesPendientes"
type Direccion = "asc" | "desc"

const TAMANIO_PAGINA = 20

function ordenarFilas(
  filas: DesempenoComisionFilaResponse[],
  columna: Columna,
  direccion: Direccion,
): DesempenoComisionFilaResponse[] {
  const signo = direccion === "asc" ? 1 : -1
  return [...filas].sort((a, b) => {
    if (columna === "nombre") return signo * a.nombre.localeCompare(b.nombre)
    const valorA = a[columna] ?? -1
    const valorB = b[columna] ?? -1
    return signo * (valorA - valorB)
  })
}

/** Pantalla "Desempeño por comisión" del Docente (`#doc-desempeno-comision`, `US-ADJ-48`, RF-20). */
export function DesempenoPorComision() {
  const navigate = useNavigate()

  const [materias, setMaterias] = useState<MateriaListItemResponse[]>([])
  const [materiaId, setMateriaId] = useState<string>("")

  const [comisiones, setComisiones] = useState<ComisionResumenResponse[]>([])
  const [comisionId, setComisionId] = useState<string>("")

  const [filas, setFilas] = useState<DesempenoComisionFilaResponse[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [columna, setColumna] = useState<Columna>("nombre")
  const [direccion, setDireccion] = useState<Direccion>("asc")
  const [pagina, setPagina] = useState(1)

  useEffect(() => {
    const controller = new AbortController()
    listarMaterias(controller.signal)
      .then(setMaterias)
      .catch(() => {})
    return () => controller.abort()
  }, [])

  function elegirMateria(value: string) {
    setMateriaId(value)
    setComisionId("")
    setFilas(null)
    setError(null)
  }

  function elegirComision(value: string) {
    setComisionId(value)
    setFilas(null)
    setError(null)
    setPagina(1)
  }

  useEffect(() => {
    if (!materiaId) {
      setComisiones([])
      return undefined
    }
    const controller = new AbortController()
    listarComisionesPorMateria(materiaId, controller.signal)
      .then(setComisiones)
      .catch(() => {})
    return () => controller.abort()
  }, [materiaId])

  useEffect(() => {
    if (!materiaId || !comisionId) return undefined
    const controller = new AbortController()
    setError(null)
    setFilas(null)
    obtenerDesempenoPorComision(materiaId, comisionId, controller.signal)
      .then(setFilas)
      .catch((err) => {
        if (err instanceof DOMException && err.name === "AbortError") return
        setError("No se pudo cargar el desempeño de la comisión. Intentá de nuevo más tarde.")
      })
    return () => controller.abort()
  }, [materiaId, comisionId])

  function ordenarPor(nuevaColumna: Columna) {
    if (nuevaColumna === columna) {
      setDireccion(direccion === "asc" ? "desc" : "asc")
    } else {
      setColumna(nuevaColumna)
      setDireccion("asc")
    }
    setPagina(1)
  }

  const filasOrdenadas = useMemo(
    () => (filas ? ordenarFilas(filas, columna, direccion) : []),
    [filas, columna, direccion],
  )
  const totalPaginas = Math.ceil(filasOrdenadas.length / TAMANIO_PAGINA)
  const filasPagina = filasOrdenadas.slice((pagina - 1) * TAMANIO_PAGINA, pagina * TAMANIO_PAGINA)

  function verDetalle(estudianteId: string) {
    navigate(
      `/analytics/desempeno-por-comision/materias/${materiaId}/comisiones/${comisionId}/estudiantes/${estudianteId}`,
    )
  }

  return (
    <div className="mx-auto max-w-2xl">
      <Breadcrumb items={[{ label: "Reportes", to: "/analytics" }, { label: "Desempeño por comisión" }]} />
      <h1 className="text-lg font-semibold">Desempeño por comisión</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Elegí una materia y una comisión para ver el desempeño de cada estudiante.
      </p>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <div>
          <label htmlFor="materia" className="text-sm font-medium">
            Materia
          </label>
          <select
            id="materia"
            className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={materiaId}
            onChange={(e) => elegirMateria(e.target.value)}
          >
            <option value="">Elegí una materia</option>
            {materias.map((materia) => (
              <option key={materia.id} value={materia.id}>
                {materia.nombre}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="comision" className="text-sm font-medium">
            Comisión
          </label>
          <select
            id="comision"
            className="mt-1 block w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={comisionId}
            onChange={(e) => elegirComision(e.target.value)}
            disabled={!materiaId}
          >
            <option value="">Elegí una comisión</option>
            {comisiones.map((comision) => (
              <option key={comision.id} value={comision.id}>
                {comision.horario}
              </option>
            ))}
          </select>
        </div>
      </div>

      {!comisionId && !error && (
        <p className="mt-4 text-sm text-muted-foreground">
          Elegí una comisión para ver el desempeño de sus estudiantes.
        </p>
      )}

      {error && (
        <div
          role="alert"
          className="mt-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          <p className="font-medium">{error}</p>
        </div>
      )}

      {!error && filas !== null && (
        <>
        <table className="mt-4 w-full text-sm">
          <thead>
            <tr className="border-b text-left text-muted-foreground">
              <th className="cursor-pointer py-2" onClick={() => ordenarPor("nombre")}>
                Nombre
              </th>
              <th
                className="cursor-pointer py-2"
                onClick={() => ordenarPor("porcentajeAciertosAcumulado")}
              >
                % Aciertos
              </th>
              <th
                className="cursor-pointer py-2"
                onClick={() => ordenarPor("actividadesPendientes")}
              >
                Actividades pendientes
              </th>
            </tr>
          </thead>
          <tbody>
            {filasPagina.map((fila) => (
              <tr
                key={fila.estudianteId}
                className="cursor-pointer border-b hover:bg-accent"
                tabIndex={0}
                onClick={() => verDetalle(fila.estudianteId)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") verDetalle(fila.estudianteId)
                }}
              >
                <td className="py-2">{fila.nombre}</td>
                <td className="py-2">
                  {fila.porcentajeAciertosAcumulado === null ? (
                    <span className="italic text-muted-foreground">Sin datos</span>
                  ) : (
                    `${fila.porcentajeAciertosAcumulado}%`
                  )}
                </td>
                <td className="py-2">
                  <span
                    className={
                      fila.actividadesPendientes > 0
                        ? "font-semibold text-amber-600"
                        : undefined
                    }
                  >
                    {fila.actividadesPendientes}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <Pagination pagina={pagina} totalPaginas={totalPaginas} onCambiarPagina={setPagina} />
        </>
      )}
    </div>
  )
}
