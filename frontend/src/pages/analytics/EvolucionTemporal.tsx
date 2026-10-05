import { useEffect, useState } from "react"
import { useParams } from "react-router"

import { Breadcrumb } from "@/components/Breadcrumb"
import {
  obtenerEvolucionTemporalComision,
  obtenerEvolucionTemporalEstudiante,
  type EvolucionTemporalComisionPuntoResponse,
  type EvolucionTemporalPuntoResponse,
} from "@/lib/analytics-api"

const ANCHO = 640
const ALTO = 320
const MARGEN = { top: 20, right: 20, bottom: 60, left: 40 }
const ANCHO_GRAFICO = ANCHO - MARGEN.left - MARGEN.right
const ALTO_GRAFICO = ALTO - MARGEN.top - MARGEN.bottom

interface ActividadEje {
  actividadId: string
  tituloActividad: string
}

/**
 * Une las actividades de ambas series en un solo eje X, en el orden en que ya vienen
 * (`US-ADJ-45` respeta el orden cronológico real de cada endpoint). La serie de comisión
 * ancla el orden — suele ser la más completa para esa comisión — y se agregan al final las
 * actividades que el estudiante rindió y no están ahí (p. ej. actividades sin restricción de
 * comisión). Ninguna serie fuerza un punto en una actividad que no le pertenece.
 */
function armarEjeX(
  comision: EvolucionTemporalComisionPuntoResponse[],
  estudiante: EvolucionTemporalPuntoResponse[],
): ActividadEje[] {
  const eje: ActividadEje[] = comision.map((p) => ({
    actividadId: p.actividadId,
    tituloActividad: p.tituloActividad,
  }))
  const yaPresentes = new Set(eje.map((p) => p.actividadId))
  for (const punto of estudiante) {
    if (!yaPresentes.has(punto.actividadId)) {
      eje.push({ actividadId: punto.actividadId, tituloActividad: punto.tituloActividad })
      yaPresentes.add(punto.actividadId)
    }
  }
  return eje
}

function coordenadaX(indice: number, total: number): number {
  if (total <= 1) return MARGEN.left + ANCHO_GRAFICO / 2
  return MARGEN.left + (indice / (total - 1)) * ANCHO_GRAFICO
}

function coordenadaY(porcentaje: number): number {
  return MARGEN.top + (1 - porcentaje / 100) * ALTO_GRAFICO
}

/** Ancho aproximado de un carácter de las etiquetas del eje (texto de 10px). */
const ANCHO_CARACTER_ETIQUETA = 5.5
const MIN_CARACTERES_ETIQUETA = 8
/** Aire mínimo entre el texto de una etiqueta y el borde del SVG. */
const MARGEN_BORDE_ETIQUETA = 4

/**
 * Máximo de caracteres de una etiqueta del eje X según el ancho que le toca a cada actividad:
 * con pocas actividades hay mucho lugar y no se trunca; con muchas se acorta para que las
 * etiquetas vecinas no se pisen. El título completo siempre queda en el `<title>` (tooltip).
 */
function maxCaracteresEtiqueta(totalActividades: number): number {
  const anchoPorActividad = ANCHO_GRAFICO / Math.max(totalActividades, 1)
  return Math.max(MIN_CARACTERES_ETIQUETA, Math.floor(anchoPorActividad / ANCHO_CARACTER_ETIQUETA))
}

/**
 * Posición X de la etiqueta de una actividad: centrada sobre su punto, pero desplazada lo mínimo
 * para que el texto quepa dentro del SVG. Las de los extremos quedan pegadas al borde del gráfico
 * y centradas se cortaban (hallazgo H-2 de la UAT 7-ADJ).
 */
function xEtiqueta(indice: number, total: number, etiqueta: string): number {
  const mitadAncho = (etiqueta.length * ANCHO_CARACTER_ETIQUETA) / 2
  const minimo = mitadAncho + MARGEN_BORDE_ETIQUETA
  const maximo = ANCHO - mitadAncho - MARGEN_BORDE_ETIQUETA
  return Math.min(Math.max(coordenadaX(indice, total), minimo), maximo)
}

function etiquetaEje(titulo: string, maxCaracteres: number): string {
  return titulo.length > maxCaracteres ? `${titulo.slice(0, maxCaracteres - 1)}…` : titulo
}

interface SerieGraficoProps {
  puntos: { indice: number; valor: number }[]
  ejeLength: number
  color: string
  discontinua: boolean
  /** Marca cada punto como un anillo hueco, para que se distinga aunque otra serie lo tape. */
  anillo?: boolean
}

function SerieGrafico({ puntos, ejeLength, color, discontinua, anillo = false }: SerieGraficoProps) {
  if (puntos.length === 0) return null
  const coords = puntos.map((p) => ({
    x: coordenadaX(p.indice, ejeLength),
    y: coordenadaY(p.valor),
  }))
  return (
    <>
      {coords.length > 1 && (
        <polyline
          points={coords.map((c) => `${c.x},${c.y}`).join(" ")}
          fill="none"
          stroke={color}
          strokeWidth={2}
          strokeDasharray={discontinua ? "6 4" : undefined}
        />
      )}
      {coords.map((c, i) =>
        anillo ? (
          <circle key={i} cx={c.x} cy={c.y} r={7} fill="none" stroke={color} strokeWidth={2} />
        ) : (
          <circle key={i} cx={c.x} cy={c.y} r={4} fill={color} />
        ),
      )}
    </>
  )
}

/** Pantalla "Evolución temporal" — drill-down desde `US-ADJ-48` (`#doc-evolucion-temporal`, RF-21). */
export function EvolucionTemporal() {
  const { materiaId, comisionId, estudianteId } = useParams<{
    materiaId: string
    comisionId: string
    estudianteId: string
  }>()

  const [puntosEstudiante, setPuntosEstudiante] = useState<EvolucionTemporalPuntoResponse[] | null>(
    null,
  )
  const [puntosComision, setPuntosComision] = useState<
    EvolucionTemporalComisionPuntoResponse[] | null
  >(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!materiaId || !comisionId || !estudianteId) return undefined
    const controller = new AbortController()
    setError(null)
    setPuntosEstudiante(null)
    setPuntosComision(null)
    Promise.all([
      obtenerEvolucionTemporalEstudiante(materiaId, estudianteId, controller.signal),
      obtenerEvolucionTemporalComision(materiaId, comisionId, controller.signal),
    ])
      .then(([estudiante, comision]) => {
        setPuntosEstudiante(estudiante)
        setPuntosComision(comision)
      })
      .catch((err) => {
        if (err instanceof DOMException && err.name === "AbortError") return
        setError("No se pudo cargar la evolución temporal. Intentá de nuevo más tarde.")
      })
    return () => controller.abort()
  }, [materiaId, comisionId, estudianteId])

  const cargando = puntosEstudiante === null || puntosComision === null

  const eje =
    !cargando && !error ? armarEjeX(puntosComision, puntosEstudiante) : []
  const indicePorActividad = new Map(eje.map((a, i) => [a.actividadId, i]))

  const serieEstudiante =
    puntosEstudiante
      ?.map((p) => ({ indice: indicePorActividad.get(p.actividadId), valor: p.porcentajeAcierto }))
      .filter((p): p is { indice: number; valor: number } => p.indice !== undefined) ?? []
  const serieComision =
    puntosComision
      ?.map((p) => ({
        indice: indicePorActividad.get(p.actividadId),
        valor: p.porcentajeAciertosPromedio,
      }))
      .filter((p): p is { indice: number; valor: number } => p.indice !== undefined) ?? []

  const sinDatos = !cargando && !error && serieEstudiante.length === 0 && serieComision.length === 0

  return (
    <div className="mx-auto max-w-2xl">
      <Breadcrumb
        items={[
          { label: "Reportes", to: "/analytics" },
          { label: "Desempeño por comisión", to: "/analytics/desempeno-por-comision" },
          {
            label: "Detalle del estudiante",
            to: `/analytics/desempeno-por-comision/materias/${materiaId}/comisiones/${comisionId}/estudiantes/${estudianteId}`,
          },
          { label: "Evolución temporal" },
        ]}
      />
      <h1 className="text-lg font-semibold">Evolución temporal</h1>

      {error && (
        <div
          role="alert"
          className="mt-4 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          <p className="font-medium">{error}</p>
        </div>
      )}

      {!error && sinDatos && (
        <p className="mt-4 text-sm text-muted-foreground">
          Ni el estudiante ni la comisión tienen evaluaciones finalizadas todavía.
        </p>
      )}

      {!error && !cargando && !sinDatos && (
        <>
          <svg
            viewBox={`0 0 ${ANCHO} ${ALTO}`}
            role="img"
            aria-label="Gráfico de evolución temporal del % de aciertos"
            className="mt-4 w-full"
          >
            <line
              x1={MARGEN.left}
              y1={MARGEN.top}
              x2={MARGEN.left}
              y2={ALTO - MARGEN.bottom}
              stroke="currentColor"
              className="text-border"
            />
            <line
              x1={MARGEN.left}
              y1={ALTO - MARGEN.bottom}
              x2={ANCHO - MARGEN.right}
              y2={ALTO - MARGEN.bottom}
              stroke="currentColor"
              className="text-border"
            />
            {[0, 25, 50, 75, 100].map((valor) => (
              <text
                key={valor}
                x={MARGEN.left - 8}
                y={coordenadaY(valor)}
                textAnchor="end"
                dominantBaseline="middle"
                className="fill-muted-foreground text-[10px]"
              >
                {valor}%
              </text>
            ))}
            {eje.map((actividad, i) => {
              const etiqueta = etiquetaEje(
                actividad.tituloActividad,
                maxCaracteresEtiqueta(eje.length),
              )
              return (
                <text
                  key={actividad.actividadId}
                  x={xEtiqueta(i, eje.length, etiqueta)}
                  y={ALTO - MARGEN.bottom + 16}
                  textAnchor="middle"
                  className="fill-muted-foreground text-[10px]"
                >
                  <title>{actividad.tituloActividad}</title>
                  {etiqueta}
                </text>
              )
            })}
            <SerieGrafico
              puntos={serieComision}
              ejeLength={eje.length}
              color="#047857"
              discontinua
              anillo
            />
            <SerieGrafico
              puntos={serieEstudiante}
              ejeLength={eje.length}
              color="#1d75b5"
              discontinua={false}
            />
          </svg>

          <div className="mt-2 flex items-center gap-4 text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-0.5 w-4 bg-primary" /> Estudiante
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-0.5 w-4 border-t-2 border-dashed border-emerald-700" />
              Promedio de la comisión
            </span>
          </div>
        </>
      )}
    </div>
  )
}
