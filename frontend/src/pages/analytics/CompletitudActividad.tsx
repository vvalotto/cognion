import { useEffect, useState } from "react"
import { useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import { Badge } from "@/components/ui/badge"
import {
  obtenerCompletitudPorActividad,
  type CompletitudPorActividadResponse,
} from "@/lib/analytics-api"
import { obtenerActividad, type ActividadResumenResponse } from "@/lib/actividad-evaluativa-api"
import { listarMaterias, type MateriaListItemResponse } from "@/lib/banco-preguntas-api"
import {
  listarComisionesPorMateria,
  listarEstudiantesDeComision,
} from "@/lib/identidad-comisiones-api"

type EstadoCompletitud = "finalizada" | "en_curso" | "suspendida" | "sin_iniciar"

const ETIQUETA_ESTADO: Record<EstadoCompletitud, string> = {
  finalizada: "Finalizada",
  en_curso: "En curso",
  suspendida: "Suspendida",
  sin_iniciar: "Sin iniciar",
}

const VARIANTE_ESTADO: Record<
  EstadoCompletitud,
  "completitud-finalizada" | "completitud-en-curso" | "completitud-suspendida" | "completitud-sin-iniciar"
> = {
  finalizada: "completitud-finalizada",
  en_curso: "completitud-en-curso",
  suspendida: "completitud-suspendida",
  sin_iniciar: "completitud-sin-iniciar",
}

function formatearFecha(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function tituloDeActividad(actividad: ActividadResumenResponse): string {
  return actividad.titulo || `Actividad del ${formatearFecha(actividad.fechaApertura)}`
}

/** Mapa estudianteId → horario de comisión, cruzando comisiones/estudiantes de la materia.
 *
 * Sin endpoint dedicado — reusa `listarComisionesPorMateria`/`listarEstudiantesDeComision`
 * ya consumidos por `DesempenoPorComision.tsx` (`US-ADJ-48`). Gap de Fase 2 documentado en
 * `docs/plans/inc5-adj/US-ADJ-51-plan.md`.
 */
async function mapaEstudianteAComision(
  materiaId: string,
  signal: AbortSignal,
): Promise<Map<string, string>> {
  const comisiones = await listarComisionesPorMateria(materiaId, signal)
  const mapa = new Map<string, string>()
  await Promise.all(
    comisiones.map(async (comision) => {
      const estudiantes = await listarEstudiantesDeComision(comision.id, signal)
      for (const estudiante of estudiantes) {
        mapa.set(estudiante.id, comision.horario)
      }
    }),
  )
  return mapa
}

/** Pantalla "Completitud de una actividad" del Docente (`#doc-completitud-actividad`, `US-ADJ-51`, RF-23). */
export function CompletitudActividad() {
  const { actividadId } = useParams<{ actividadId: string }>()

  const [actividad, setActividad] = useState<ActividadResumenResponse | null>(null)
  const [materia, setMateria] = useState<MateriaListItemResponse | null>(null)
  const [completitud, setCompletitud] = useState<CompletitudPorActividadResponse | null>(null)
  const [comisionPorEstudiante, setComisionPorEstudiante] = useState<Map<string, string>>(
    new Map(),
  )
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!actividadId) return undefined
    const controller = new AbortController()
    obtenerActividad(actividadId, controller.signal)
      .then(setActividad)
      .catch(() => {})
    return () => controller.abort()
  }, [actividadId])

  useEffect(() => {
    if (!actividadId) return undefined
    const controller = new AbortController()
    setError(null)
    obtenerCompletitudPorActividad(actividadId, controller.signal)
      .then(setCompletitud)
      .catch((err) => {
        if (err instanceof DOMException && err.name === "AbortError") return
        setError("No se pudo cargar la completitud de la actividad. Intentá de nuevo más tarde.")
      })
    return () => controller.abort()
  }, [actividadId])

  useEffect(() => {
    if (!actividad) return undefined
    const controller = new AbortController()
    listarMaterias(controller.signal)
      .then((materias) => setMateria(materias.find((m) => m.id === actividad.materiaId) ?? null))
      .catch(() => {})
    return () => controller.abort()
  }, [actividad])

  useEffect(() => {
    if (!actividad) return undefined
    const controller = new AbortController()
    mapaEstudianteAComision(actividad.materiaId, controller.signal)
      .then(setComisionPorEstudiante)
      .catch(() => {})
    return () => controller.abort()
  }, [actividad])

  if (error) {
    return (
      <div
        role="alert"
        className="mt-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
      >
        <p className="font-medium">{error}</p>
      </div>
    )
  }

  if (actividad === null || completitud === null) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  const horarios = new Set(
    completitud.detalle
      .map((fila) => comisionPorEstudiante.get(fila.estudianteId))
      .filter((horario): horario is string => horario !== undefined),
  )
  const mostrarColumnaComision = horarios.size > 1

  return (
    <div className="mx-auto max-w-2xl">
      <Breadcrumb
        items={[
          {
            label: "Actividades",
            to: `/actividad-evaluativa/materias/${actividad.materiaId}/actividades`,
          },
          {
            label: tituloDeActividad(actividad),
            to: `/actividad-evaluativa/actividades/${actividad.id}`,
          },
          { label: "Completitud" },
        ]}
      />
      <h1 className="text-lg font-semibold">Completitud de la actividad</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        {tituloDeActividad(actividad)} — {materia?.nombre ?? "…"}
      </p>

      <div className="mt-4 flex flex-wrap gap-6 rounded-lg border p-4">
        <div className="text-center">
          <p className="text-xl font-bold">{completitud.resumen.finalizadas}</p>
          <p className="text-xs uppercase text-muted-foreground">Finalizadas</p>
        </div>
        <div className="text-center">
          <p className="text-xl font-bold">{completitud.resumen.enCurso}</p>
          <p className="text-xs uppercase text-muted-foreground">En curso</p>
        </div>
        <div className="text-center">
          <p className="text-xl font-bold">{completitud.resumen.suspendidas}</p>
          <p className="text-xs uppercase text-muted-foreground">Suspendidas</p>
        </div>
        <div className="text-center">
          <p className="text-xl font-bold">{completitud.resumen.sinIniciar}</p>
          <p className="text-xs uppercase text-muted-foreground">Sin iniciar</p>
        </div>
      </div>

      <table className="mt-4 w-full text-sm">
        <thead>
          <tr className="border-b text-left text-muted-foreground">
            <th className="py-2">Nombre</th>
            {mostrarColumnaComision && <th className="py-2">Comisión</th>}
            <th className="py-2">Estado</th>
          </tr>
        </thead>
        <tbody>
          {completitud.detalle.map((fila) => {
            const estado = fila.estado as EstadoCompletitud
            return (
              <tr key={fila.estudianteId} className="border-b">
                <td className="py-2">{fila.nombre}</td>
                {mostrarColumnaComision && (
                  <td className="py-2">{comisionPorEstudiante.get(fila.estudianteId) ?? "—"}</td>
                )}
                <td className="py-2">
                  <Badge variant={VARIANTE_ESTADO[estado]}>{ETIQUETA_ESTADO[estado]}</Badge>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
