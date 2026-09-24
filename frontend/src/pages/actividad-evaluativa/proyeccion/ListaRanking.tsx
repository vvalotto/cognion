import { top3 } from "@/lib/ranking-en-vivo"
import type { RankingItemCanal } from "@/lib/canal-sesion-en-vivo"

/** Top 3 del ranking con nombre y puntaje, o "Nadie participó" (H9). */
export function ListaRanking({ ranking }: { ranking: RankingItemCanal[] }) {
  const puestos = top3(ranking)
  if (puestos.length === 0) {
    return <p className="mt-8 text-[32px] font-bold">Nadie participó</p>
  }
  return (
    <ol className="mt-8 w-full max-w-2xl space-y-3">
      {puestos.map((item) => (
        <li
          key={item.estudianteId}
          className="flex items-center gap-4 rounded-xl px-6 py-4 text-[30px] font-bold"
          style={{ background: "rgba(255,255,255,0.08)" }}
        >
          <span className="w-11 font-black" style={{ color: "var(--stage-primary)" }}>
            {item.posicion}
          </span>
          <span>{item.nombre}</span>
          <span className="ml-auto font-black" style={{ color: "var(--stage-accent)" }}>
            {item.puntajeAcumulado}
          </span>
        </li>
      ))}
    </ol>
  )
}
