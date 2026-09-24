import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { StageRanking } from "./StageRanking"
import { vistaResultado } from "./_vista-test"

afterEach(cleanup)

function renderRanking(extra = {}, props = {}) {
  return render(
    <StageRanking
      vista={vistaResultado({ etapa: "ranking", ...extra })}
      enviando={false}
      onSiguiente={() => {}}
      onFinalizar={() => {}}
      {...props}
    />,
  )
}

describe("StageRanking", () => {
  it("con 6 participantes muestra solo el Top 3, con nombre y puntaje, en orden descendente", () => {
    renderRanking()
    const puestos = screen.getAllByRole("listitem")
    expect(puestos).toHaveLength(3)
    expect(puestos.map((p) => p.textContent)).toEqual([
      "1Estudiante 16000",
      "2Estudiante 25000",
      "3Estudiante 34000",
    ])
  })

  it("con 2 participantes muestra esos 2", () => {
    const base = vistaResultado()
    renderRanking({ resultado: { ...base.resultado!, ranking: base.resultado!.ranking.slice(0, 2) } })
    expect(screen.getAllByRole("listitem")).toHaveLength(2)
  })

  it("sin participantes dice 'Nadie participó'", () => {
    const base = vistaResultado()
    renderRanking({ resultado: { ...base.resultado!, ranking: [] } })
    expect(screen.getByText("Nadie participó")).toBeInTheDocument()
    expect(screen.queryAllByRole("listitem")).toHaveLength(0)
  })

  it("con preguntas restantes ofrece 'Siguiente pregunta' y 'Finalizar sesión'", () => {
    const onSiguiente = vi.fn()
    const onFinalizar = vi.fn()
    renderRanking({}, { onSiguiente, onFinalizar })

    fireEvent.click(screen.getByRole("button", { name: "Siguiente pregunta" }))
    fireEvent.click(screen.getByRole("button", { name: "Finalizar sesión" }))
    expect(onSiguiente).toHaveBeenCalledTimes(1)
    expect(onFinalizar).toHaveBeenCalledTimes(1)
  })

  it("en la última pregunta solo está 'Finalizar sesión'", () => {
    renderRanking({ indice: 4 })
    expect(screen.queryByRole("button", { name: "Siguiente pregunta" })).not.toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Finalizar sesión" })).toBeInTheDocument()
  })

  it("mientras envía, los botones quedan deshabilitados", () => {
    render(
      <StageRanking
        vista={vistaResultado({ etapa: "ranking" })}
        enviando
        onSiguiente={() => {}}
        onFinalizar={() => {}}
      />,
    )
    expect(screen.getByRole("button", { name: "Siguiente pregunta" })).toBeDisabled()
    expect(screen.getByRole("button", { name: "Finalizar sesión" })).toBeDisabled()
  })

  it("sin resultado muestra 'Nadie participó'", () => {
    renderRanking({ resultado: null })
    expect(screen.getByText("Nadie participó")).toBeInTheDocument()
  })
})
