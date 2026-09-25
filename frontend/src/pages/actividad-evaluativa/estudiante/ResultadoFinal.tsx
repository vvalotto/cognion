import { Card } from "@/components/ui/card"
import type { RankingItemCanal } from "@/lib/canal-sesion-en-vivo"
import { top3 } from "@/lib/ranking-en-vivo"

function Fila({ item, propia }: { item: RankingItemCanal; propia: boolean }) {
  return (
    <li
      data-propia={propia}
      className={`flex items-center gap-3 rounded-lg px-3 py-2 ${propia ? "bg-primary/10 font-semibold" : ""}`}
    >
      <span className="w-6 font-bold text-primary">{item.posicion}</span>
      <span>{propia ? "Vos" : item.nombre}</span>
      <span className="ml-auto font-bold tabular-nums">{item.puntajeAcumulado}</span>
    </li>
  )
}

/**
 * Resultado final (`#est-resultado-final`, §3.5): posición propia + Top 3 con la fila propia resaltada;
 * si quedó fuera del Top 3, su fila va debajo con su posición.
 */
export function ResultadoFinal({
  ranking,
  estudianteId,
}: {
  ranking: RankingItemCanal[]
  estudianteId: string | null
}) {
  const propio = ranking.find((item) => item.estudianteId === estudianteId) ?? null
  const puestos = top3(ranking)
  const fueraDelTop = propio !== null && !puestos.some((item) => item.estudianteId === propio.estudianteId)

  return (
    <Card className="mx-auto mt-10 max-w-md p-6 text-center">
      <div className="text-4xl" aria-hidden="true">
        🏆
      </div>
      <h1 className="mt-2 text-lg font-semibold">¡Terminó la sesión!</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        {propio
          ? `Quedaste ${propio.posicion}° con ${propio.puntajeAcumulado} puntos`
          : "No sumaste puntos en esta sesión"}
      </p>
      {puestos.length > 0 && (
        <ol aria-label="Ranking final" className="mt-4 space-y-1 text-left">
          {puestos.map((item) => (
            <Fila key={item.estudianteId} item={item} propia={item.estudianteId === estudianteId} />
          ))}
          {fueraDelTop && propio && <Fila item={propio} propia />}
        </ol>
      )}
    </Card>
  )
}
