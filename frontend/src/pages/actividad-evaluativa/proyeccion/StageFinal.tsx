import { Link } from "react-router"

import type { RankingItemCanal } from "@/lib/canal-sesion-en-vivo"
import { top3 } from "@/lib/ranking-en-vivo"
import type { VistaProyeccion } from "./vista-proyeccion"

const ESCALON: Record<number, { alto: string; fondo: string; texto: string }> = {
  1: { alto: "150px", fondo: "#f5c542", texto: "#3a2c00" },
  2: { alto: "110px", fondo: "#c8d2d8", texto: "#1b1b1b" },
  3: { alto: "80px", fondo: "#cf8a4a", texto: "#2a1600" },
}

/** Orden visual clásico del podio: 2° a la izquierda, 1° al centro, 3° a la derecha. */
function ordenPodio(puestos: RankingItemCanal[]): RankingItemCanal[] {
  const porPuesto = (n: number) => puestos.filter((_, i) => i + 1 === n)
  return [...porPuesto(2), ...porPuesto(1), ...porPuesto(3)]
}

/** Proyección — resultado final con el podio (`#stage-final`, §2.7 + H7/H9). */
export function StageFinal({ vista }: { vista: VistaProyeccion }) {
  const puestos = top3(vista.resultado?.ranking ?? [])

  return (
    <div className="mx-auto flex min-h-screen max-w-5xl flex-col items-center justify-center px-8 text-center">
      <Link
        to={`/actividad-evaluativa/comisiones/${vista.comisionId}`}
        className="absolute top-4 left-4 text-sm"
        style={{ color: "rgba(255,255,255,0.45)" }}
      >
        ‹ Volver a la Comisión
      </Link>
      <p className="text-xl tracking-wider uppercase" style={{ color: "var(--stage-muted)" }}>
        Sesión finalizada
      </p>

      {puestos.length === 0 ? (
        <p className="my-10 text-[32px] font-bold">Nadie participó</p>
      ) : (
        <ol aria-label="Podio" className="my-10 flex items-end gap-6">
          {ordenPodio(puestos).map((item) => {
            const puesto = puestos.indexOf(item) + 1
            const escalon = ESCALON[puesto]
            return (
              <li key={item.estudianteId} data-puesto={puesto} className="text-center">
                <div
                  className="flex w-32 justify-center rounded-t-xl pt-2.5 text-[32px] font-black"
                  style={{ height: escalon.alto, background: escalon.fondo, color: escalon.texto }}
                >
                  {puesto}°
                </div>
                <p className="mt-2 text-[22px] font-bold">{item.nombre}</p>
                <p className="text-lg" style={{ color: "var(--stage-accent)" }}>
                  {item.puntajeAcumulado} pts
                </p>
              </li>
            )
          })}
        </ol>
      )}

      <p className="text-[28px] font-bold">¡Gracias por participar!</p>
    </div>
  )
}
