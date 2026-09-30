import { useCallback, useEffect, useRef, useState } from "react"
import { useNavigate, useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { ApiError } from "@/lib/api-client"
import {
  listarSesionesEnVivo,
  unirseASesion,
  type SesionEnVivoResumenResponse,
} from "@/lib/sesion-en-vivo-api"
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
  listarActividadesVisibles,
  type ActividadVisibleResponse,
  type EstadoVisible,
} from "@/lib/actividad-evaluativa-api"
import { listarMisMaterias, type MateriaEstudianteResponse } from "@/lib/identidad-estudiante-api"

const ETIQUETA_ESTADO: Record<EstadoVisible, string> = {
  pendiente: "Pendiente de responder",
  todavia_no_abrio: "Todavía no abrió",
  finalizada: "Finalizada — ver revisión",
}

const VARIANTE_ESTADO: Record<EstadoVisible, "visible-pendiente" | "visible-todavia-no-abrio" | "visible-finalizada"> = {
  pendiente: "visible-pendiente",
  todavia_no_abrio: "visible-todavia-no-abrio",
  finalizada: "visible-finalizada",
}

const REFRESCO_SESIONES_MS = 10_000

function formatearFecha(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function tituloDeActividad(actividad: ActividadVisibleResponse): string {
  return actividad.titulo || `Actividad del ${formatearFecha(actividad.fechaApertura)}`
}

/**
 * Pantalla "Actividades de una materia" del Estudiante (`#est-actividades`, `US-3.4.5`). Suma las
 * sesiones en vivo de su Comisión para esa materia (`#est-sesiones`, `US-6.3.8`): un solo lugar
 * donde mirar, sin menú aparte.
 */
export function MisActividades() {
  const { materiaId } = useParams<{ materiaId: string }>()
  const navigate = useNavigate()

  const [materia, setMateria] = useState<MateriaEstudianteResponse | null>(null)
  const [actividades, setActividades] = useState<ActividadVisibleResponse[] | null>(null)
  const [sesiones, setSesiones] = useState<SesionEnVivoResumenResponse[] | null>(null)
  const [errorSesion, setErrorSesion] = useState<string | null>(null)
  const uniendoRef = useRef(false)
  const controladorSesionesRef = useRef<AbortController | null>(null)

  const cargarSesiones = useCallback(async () => {
    const controller = controladorSesionesRef.current
    if (!controller) return
    try {
      const todas = await listarSesionesEnVivo(undefined, controller.signal)
      setSesiones(todas.filter((s) => s.materiaId === materiaId && s.estado !== "finalizada"))
    } catch {
      // Sin la lista no se muestra nada nuevo; el próximo ciclo reintenta.
    }
  }, [materiaId])

  useEffect(() => {
    const controller = new AbortController()
    listarMisMaterias(controller.signal)
      .then((materias) => setMateria(materias.find((m) => m.id === materiaId) ?? null))
      .catch(() => {})
    return () => controller.abort()
  }, [materiaId])

  useEffect(() => {
    if (!materiaId) return undefined
    const controller = new AbortController()
    listarActividadesVisibles(materiaId, controller.signal)
      .then((resultado) => setActividades(resultado))
      .catch(() => {})
    return () => controller.abort()
  }, [materiaId])

  // Sin WebSocket acá (todavía no hay `sesion_id`): se refresca cada 10 s mientras la pantalla
  // está abierta y visible.
  useEffect(() => {
    const controller = new AbortController()
    controladorSesionesRef.current = controller
    void cargarSesiones()
    const intervalo = setInterval(() => {
      if (document.visibilityState !== "hidden") void cargarSesiones()
    }, REFRESCO_SESIONES_MS)
    return () => {
      clearInterval(intervalo)
      controller.abort()
    }
  }, [cargarSesiones])

  async function unirse(sesion: SesionEnVivoResumenResponse) {
    if (uniendoRef.current) return
    uniendoRef.current = true
    setErrorSesion(null)
    try {
      await unirseASesion(sesion.id, controladorSesionesRef.current?.signal)
      navigate(`/mis-sesiones-en-vivo/${sesion.id}`)
    } catch (err) {
      if (controladorSesionesRef.current?.signal.aborted) return
      if (err instanceof ApiError && (err.status === 422 || err.status === 404)) {
        setErrorSesion("Esa sesión ya no está disponible.")
        void cargarSesiones()
      } else {
        setErrorSesion("No se pudo unir a la sesión. Reintentá.")
      }
    } finally {
      uniendoRef.current = false
    }
  }

  function irA(actividad: ActividadVisibleResponse) {
    if (actividad.estado === "todavia_no_abrio") {
      navigate(`/mis-actividades/${actividad.id}/fuera-de-periodo`, {
        state: { titulo: tituloDeActividad(actividad), fechaApertura: actividad.fechaApertura },
      })
      return
    }
    if (actividad.estado === "finalizada" && actividad.evaluacionId) {
      navigate(`/mis-actividades/evaluaciones/${actividad.evaluacionId}/revision`)
      return
    }
    navigate(`/mis-actividades/actividades/${actividad.id}/rendir`)
  }

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Mis materias", to: "/mis-actividades/materias" },
          { label: materia?.nombre ?? "…" },
          { label: "Actividades" },
        ]}
      />
      <h1 className="text-lg font-semibold">Actividades de período abierto</h1>

      <h2 className="mt-4 text-base font-semibold">Sesiones en vivo</h2>
      {errorSesion && (
        <p role="alert" className="mt-2 text-sm text-destructive">
          {errorSesion}
        </p>
      )}
      {sesiones === null ? (
        <p className="mt-2 text-sm text-muted-foreground">Buscando sesiones…</p>
      ) : sesiones.length === 0 ? (
        <p className="mt-2 text-sm text-muted-foreground">Por ahora no hay sesiones en vivo.</p>
      ) : (
        <ul className="mt-3 grid gap-3 sm:grid-cols-2">
          {sesiones.map((sesion) => (
            <li key={sesion.id}>
              <button
                type="button"
                className="w-full rounded-xl border bg-card p-4 text-left transition-colors hover:border-primary"
                onClick={() => void unirse(sesion)}
              >
                <span className="block font-semibold">{sesion.materiaNombre}</span>
                <span className="mt-1 block text-xs text-muted-foreground">
                  {sesion.cantidadPreguntas} preguntas · {sesion.tiempoLimitePorPreguntaSegundos}s
                  cada una
                </span>
                <Badge
                  className="mt-3"
                  variant={sesion.estado === "en_curso" ? "estado-en-curso" : "estado-en-espera"}
                >
                  {sesion.estado === "en_curso" ? "En curso" : "En espera"}
                </Badge>
              </button>
            </li>
          ))}
        </ul>
      )}

      <h2 className="mt-8 text-base font-semibold">Período abierto</h2>

      <Card className="mt-4 overflow-x-auto py-0">
        <Table>
          <TableHeader>
            <tr>
              <TableHeaderCell>Título</TableHeaderCell>
              <TableHeaderCell>Período</TableHeaderCell>
              <TableHeaderCell>Estado</TableHeaderCell>
            </tr>
          </TableHeader>
          <TableBody>
            {actividades === null ? (
              <TableEmptyRow colSpan={3}>Cargando…</TableEmptyRow>
            ) : actividades.length === 0 ? (
              <TableEmptyRow colSpan={3}>
                Todavía no hay actividades disponibles para esta materia.
              </TableEmptyRow>
            ) : (
              actividades.map((actividad) => (
                <TableRow
                  key={actividad.id}
                  className="cursor-pointer"
                  onClick={() => irA(actividad)}
                >
                  <TableCell className="font-medium">{tituloDeActividad(actividad)}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    Abre {formatearFecha(actividad.fechaApertura)} · Cierra{" "}
                    {formatearFecha(actividad.fechaCierre)}
                  </TableCell>
                  <TableCell>
                    <Badge variant={VARIANTE_ESTADO[actividad.estado]}>
                      {ETIQUETA_ESTADO[actividad.estado]}
                    </Badge>
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
