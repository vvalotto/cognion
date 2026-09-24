import { useEffect } from "react"

import { Button } from "@/components/ui/button"
import { estiloOpcion, filasHistograma } from "@/lib/opciones-en-vivo"
import type { VistaProyeccion } from "./vista-proyeccion"

export const SEGUNDOS_HISTOGRAMA = 6

interface Props {
  vista: VistaProyeccion
  onVerRanking: () => void
}

/** Proyección — así respondió el aula (`#stage-histograma`, §2.5); pasa sola al ranking. */
export function StageHistograma({ vista, onVerRanking }: Props) {
  useEffect(() => {
    const timeout = setTimeout(onVerRanking, SEGUNDOS_HISTOGRAMA * 1000)
    return () => clearTimeout(timeout)
  }, [onVerRanking])

  const filas = filasHistograma(
    vista.tipo,
    vista.resultado?.respuestaCorrecta ?? null,
    vista.resultado?.distribucion ?? [],
  )
  const maximo = Math.max(1, ...filas.map((fila) => fila.cantidad))

  return (
    <div className="mx-auto flex min-h-screen max-w-5xl flex-col items-center justify-center px-8 text-center">
      <p className="mb-6 text-xl tracking-wider uppercase" style={{ color: "var(--stage-muted)" }}>
        Pregunta {vista.indice + 1} de {vista.cantidadPreguntas} — cerrada · así respondió el aula
      </p>

      <ul className="w-full max-w-3xl space-y-4">
        {filas.map((fila, posicion) => (
          <li
            key={`${posicion}-${fila.texto}`}
            data-correcta={fila.esCorrecta}
            className="flex items-center gap-4"
          >
            <span
              className={`w-2/5 rounded-lg px-4 py-3 text-left text-[26px] leading-snug font-bold${
                fila.esCorrecta ? " outline-3 outline-offset-2 outline-white" : ""
              }`}
              style={estiloOpcion(fila.color)}
            >
              {fila.texto}
              {fila.esCorrecta && " ✓"}
            </span>
            <span
              className="h-10 flex-1 overflow-hidden rounded-lg"
              style={{ background: "rgba(255,255,255,0.1)" }}
            >
              <span
                data-testid="barra-histograma"
                className="flex h-full items-center justify-end pr-3 text-[26px] font-extrabold"
                style={{
                  width: `${(fila.cantidad / maximo) * 100}%`,
                  background: fila.esCorrecta ? "var(--stage-accent)" : "var(--stage-primary)",
                }}
              >
                {fila.cantidad}
              </span>
            </span>
          </li>
        ))}
      </ul>

      <p className="mt-6 text-xl" style={{ color: "var(--stage-muted)" }}>
        Pasando al ranking en unos segundos…
      </p>
      <div className="mt-6">
        <Button
          type="button"
          variant="outline"
          size="lg"
          className="h-auto border-white/40 bg-transparent px-9 py-4 text-xl text-white hover:bg-white/10"
          onClick={onVerRanking}
        >
          Ver ranking ahora →
        </Button>
      </div>
    </div>
  )
}
