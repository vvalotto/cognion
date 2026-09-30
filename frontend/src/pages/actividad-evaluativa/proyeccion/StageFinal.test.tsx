import { cleanup, render, screen, within } from "@testing-library/react"
import { MemoryRouter } from "react-router"
import { afterEach, describe, expect, it } from "vitest"

import { StageFinal } from "./StageFinal"
import { vistaResultado } from "./_vista-test"
import type { VistaProyeccion } from "./vista-proyeccion"

afterEach(cleanup)

function renderFinal(vista: VistaProyeccion) {
  return render(
    <MemoryRouter>
      <StageFinal vista={vista} />
    </MemoryRouter>,
  )
}

function conRanking(cantidad: number): VistaProyeccion {
  const base = vistaResultado({ etapa: "finalizada" })
  return { ...base, resultado: { ...base.resultado!, ranking: base.resultado!.ranking.slice(0, cantidad) } }
}

describe("StageFinal", () => {
  it("podio Top 3 con nombres, en orden 2°-1°-3°, y '¡Gracias por participar!'", () => {
    renderFinal(vistaResultado({ etapa: "finalizada" }))

    const podio = within(screen.getByRole("list", { name: "Podio" })).getAllByRole("listitem")
    expect(podio.map((p) => p.getAttribute("data-puesto"))).toEqual(["2", "1", "3"])
    expect(podio[1]).toHaveTextContent("Estudiante 1")
    expect(podio[1]).toHaveTextContent("6000 pts")
    expect(screen.queryByText("Estudiante 4")).not.toBeInTheDocument()
    expect(screen.getByText("¡Gracias por participar!")).toBeInTheDocument()
  })

  it("con 2 participantes muestra solo 2 escalones", () => {
    renderFinal(conRanking(2))
    const podio = within(screen.getByRole("list", { name: "Podio" })).getAllByRole("listitem")
    expect(podio.map((p) => p.getAttribute("data-puesto"))).toEqual(["2", "1"])
  })

  it("sin participantes dice 'Nadie participó'", () => {
    renderFinal(conRanking(0))
    expect(screen.getByText("Nadie participó")).toBeInTheDocument()
    expect(screen.queryByRole("list", { name: "Podio" })).not.toBeInTheDocument()
  })

  it("enlace discreto para volver a la Comisión (H7)", () => {
    renderFinal(vistaResultado({ etapa: "finalizada", resultado: null }))
    expect(screen.getByRole("link", { name: /Volver a la Comisión/ })).toHaveAttribute(
      "href",
      "/actividad-evaluativa/comisiones/c1",
    )
  })
})
