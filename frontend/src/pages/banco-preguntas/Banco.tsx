import { Pencil, Trash2 } from "lucide-react"
import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
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
import {
  derivarSugerencias,
  filtrarBanco,
  listarMaterias,
  type Dificultad,
  type FiltrosBanco,
  type Importancia,
  type MateriaListItemResponse,
  type PreguntaResponse,
} from "@/lib/banco-preguntas-api"

const TAMANIO_PAGINA = 20

const NIVELES: Array<Dificultad | Importancia> = ["alto", "medio", "bajo"]
const ETIQUETA_NIVEL: Record<Dificultad | Importancia, string> = {
  alto: "Alto",
  medio: "Medio",
  bajo: "Bajo",
}
const VARIANTE_NIVEL: Record<Dificultad | Importancia, "nivel-alto" | "nivel-medio" | "nivel-bajo"> = {
  alto: "nivel-alto",
  medio: "nivel-medio",
  bajo: "nivel-bajo",
}

function esOpcionMultiple(pregunta: PreguntaResponse): boolean {
  return "opciones" in pregunta
}

/** Pantalla de listado y filtro del banco de preguntas (§2.3 `wireframes-banco-preguntas.md`). */
export function Banco() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const navigate = useNavigate()

  const [materia, setMateria] = useState<MateriaListItemResponse | null>(null)
  const [preguntas, setPreguntas] = useState<PreguntaResponse[] | null>(null)
  const [total, setTotal] = useState(0)
  const [pagina, setPagina] = useState(1)
  const [unidad, setUnidad] = useState("")
  const [tema, setTema] = useState("")
  const [dificultad, setDificultad] = useState<Dificultad | "">("")
  const [importancia, setImportancia] = useState<Importancia | "">("")
  const [sugerenciasUnidad, setSugerenciasUnidad] = useState<string[]>([])
  const [sugerenciasTema, setSugerenciasTema] = useState<string[]>([])

  useEffect(() => {
    const controller = new AbortController()
    listarMaterias(controller.signal)
      .then((materias) => setMateria(materias.find((m) => m.id === materiaId) ?? null))
      .catch(() => {})
    return () => controller.abort()
  }, [materiaId])

  useEffect(() => {
    if (!materia) return undefined
    const controller = new AbortController()
    filtrarBanco(materia.bancoId, {}, undefined, controller.signal)
      .then((resultado) => {
        const { unidades, temas } = derivarSugerencias(resultado.preguntas)
        setSugerenciasUnidad(unidades)
        setSugerenciasTema(temas)
      })
      .catch(() => {})
    return () => controller.abort()
  }, [materia])

  useEffect(() => {
    if (!materia) return undefined
    const controller = new AbortController()
    const filtros: FiltrosBanco = {
      unidad: unidad || undefined,
      tema: tema || undefined,
      dificultad: dificultad || undefined,
      importancia: importancia || undefined,
    }
    filtrarBanco(materia.bancoId, filtros, { pagina, tamanioPagina: TAMANIO_PAGINA }, controller.signal)
      .then((resultado) => {
        setPreguntas(resultado.preguntas)
        setTotal(resultado.total)
      })
      .catch(() => {})
    return () => controller.abort()
  }, [materia, unidad, tema, dificultad, importancia, pagina])

  function limpiarFiltros() {
    setUnidad("")
    setTema("")
    setDificultad("")
    setImportancia("")
    setPagina(1)
  }

  const totalPaginas = Math.ceil(total / TAMANIO_PAGINA)

  if (materia === null) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Banco de preguntas" },
          { label: "Materias", to: "/materias" },
          { label: materia.nombre },
        ]}
      />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">{materia.nombre}</h1>
          <p className="text-sm text-muted-foreground">
            {total} pregunta{total === 1 ? "" : "s"} activa{total === 1 ? "" : "s"} en el banco
          </p>
        </div>
        <Button onClick={() => navigate(`/materias/${materiaId}/banco/preguntas/nueva`)}>
          + Nueva pregunta
        </Button>
      </div>

      <Card className="mt-4">
        <CardContent className="flex flex-wrap items-end gap-3 p-4">
        <div>
          <label
            htmlFor="filtro-unidad"
            className="text-[11px] font-bold tracking-wide text-muted-foreground uppercase"
          >
            Unidad temática
          </label>
          <select
            id="filtro-unidad"
            value={unidad}
            onChange={(e) => {
              setUnidad(e.target.value)
              setPagina(1)
            }}
            className="mt-1 block rounded-md border border-border px-2 py-1 text-sm"
          >
            <option value="">Todos</option>
            {sugerenciasUnidad.map((valor) => (
              <option key={valor} value={valor}>
                {valor}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label
            htmlFor="filtro-tema"
            className="text-[11px] font-bold tracking-wide text-muted-foreground uppercase"
          >
            Tema
          </label>
          <input
            id="filtro-tema"
            type="text"
            list="filtro-tema-sugerencias"
            value={tema}
            onChange={(e) => {
              setTema(e.target.value)
              setPagina(1)
            }}
            className="mt-1 block rounded-md border border-border px-2 py-1 text-sm"
          />
          <datalist id="filtro-tema-sugerencias">
            {sugerenciasTema.map((valor) => (
              <option key={valor} value={valor} />
            ))}
          </datalist>
        </div>
        <div>
          <label
            htmlFor="filtro-dificultad"
            className="text-[11px] font-bold tracking-wide text-muted-foreground uppercase"
          >
            Dificultad
          </label>
          <select
            id="filtro-dificultad"
            value={dificultad}
            onChange={(e) => {
              setDificultad(e.target.value as Dificultad | "")
              setPagina(1)
            }}
            className="mt-1 block rounded-md border border-border px-2 py-1 text-sm"
          >
            <option value="">Todas</option>
            {NIVELES.map((nivel) => (
              <option key={nivel} value={nivel}>
                {ETIQUETA_NIVEL[nivel]}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label
            htmlFor="filtro-importancia"
            className="text-[11px] font-bold tracking-wide text-muted-foreground uppercase"
          >
            Importancia
          </label>
          <select
            id="filtro-importancia"
            value={importancia}
            onChange={(e) => {
              setImportancia(e.target.value as Importancia | "")
              setPagina(1)
            }}
            className="mt-1 block rounded-md border border-border px-2 py-1 text-sm"
          >
            <option value="">Todas</option>
            {NIVELES.map((nivel) => (
              <option key={nivel} value={nivel}>
                {ETIQUETA_NIVEL[nivel]}
              </option>
            ))}
          </select>
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
              <TableHeaderCell>Pregunta</TableHeaderCell>
              <TableHeaderCell>Tipo</TableHeaderCell>
              <TableHeaderCell>Unidad / Tema</TableHeaderCell>
              <TableHeaderCell>Dificultad</TableHeaderCell>
              <TableHeaderCell>Importancia</TableHeaderCell>
              <TableHeaderCell></TableHeaderCell>
            </tr>
          </TableHeader>
          <TableBody>
            {preguntas === null ? (
              <TableEmptyRow colSpan={6}>Cargando…</TableEmptyRow>
            ) : (
              preguntas.map((pregunta) => (
                <TableRow key={pregunta.id}>
                  <TableCell className="max-w-[220px] pr-3">{pregunta.texto}</TableCell>
                  <TableCell className="whitespace-nowrap pr-3">
                    <Badge variant={esOpcionMultiple(pregunta) ? "tipo-om" : "tipo-vf"}>
                      {esOpcionMultiple(pregunta) ? "Opción múltiple" : "Verdadero/Falso"}
                    </Badge>
                  </TableCell>
                  <TableCell className="max-w-[130px] pr-3">
                    {pregunta.unidadTematica} · {pregunta.tema}
                  </TableCell>
                  <TableCell className="pr-3">
                    <Badge variant={VARIANTE_NIVEL[pregunta.dificultad]}>
                      {ETIQUETA_NIVEL[pregunta.dificultad]}
                    </Badge>
                  </TableCell>
                  <TableCell className="pr-3">
                    <Badge variant={VARIANTE_NIVEL[pregunta.importancia]}>
                      {ETIQUETA_NIVEL[pregunta.importancia]}
                    </Badge>
                  </TableCell>
                  <TableCell className="whitespace-nowrap pr-3">
                    <div className="flex gap-1.5">
                      <RowActionButton
                        label="Editar"
                        icon={Pencil}
                        onClick={() =>
                          navigate(
                            `/materias/${materiaId}/banco/preguntas/${pregunta.id}/editar`,
                          )
                        }
                      />
                      <RowActionButton
                        label="Eliminar"
                        icon={Trash2}
                        variant="destructive-solid"
                        onClick={() =>
                          navigate(
                            `/materias/${materiaId}/banco/preguntas/${pregunta.id}/eliminar`,
                          )
                        }
                      />
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
