import { cleanup, render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, describe, expect, it } from "vitest"

import { FueraDePeriodo } from "@/pages/actividad-evaluativa/FueraDePeriodo"

function renderFueraDePeriodo(state?: object) {
  return render(
    <MemoryRouter
      initialEntries={[{ pathname: "/mis-actividades/act-1/fuera-de-periodo", state }]}
    >
      <Routes>
        <Route
          path="/mis-actividades/:actividadId/fuera-de-periodo"
          element={<FueraDePeriodo />}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe("FueraDePeriodo", () => {
  afterEach(() => {
    cleanup()
  })

  it("muestra el título y la fecha de apertura recibidos por navigation state", () => {
    renderFueraDePeriodo({ titulo: "Repaso Unidad 4", fechaApertura: "2026-10-05T00:00:00+00:00" })

    expect(screen.getByText("Todavía no está disponible")).toBeInTheDocument()
    expect(screen.getAllByText("Repaso Unidad 4").length).toBeGreaterThan(0)
    expect(screen.getByText(/Esta actividad abre el/)).toBeInTheDocument()
  })

  it("sin navigation state muestra un texto neutro que no afirma si abrió o cerró", () => {
    renderFueraDePeriodo()

    expect(
      screen.getByText("Esta actividad no está disponible en este momento"),
    ).toBeInTheDocument()
    expect(screen.queryByText("Todavía no está disponible")).not.toBeInTheDocument()
    expect(screen.queryByText(/Volvé a entrar/)).not.toBeInTheDocument()
  })

  it("con estado 'cerrada' explica que ya cerró, con la fecha de cierre, sin invitar a volver", () => {
    renderFueraDePeriodo({
      titulo: "Parcial de prueba",
      estado: "cerrada",
      fechaCierre: "2026-09-20T23:59:00+00:00",
    })

    expect(screen.getByText("Esta actividad ya cerró")).toBeInTheDocument()
    expect(screen.getByText(/Cerró el/)).toBeInTheDocument()
    expect(screen.getByText(/Ya no se puede rendir/)).toBeInTheDocument()
    expect(screen.queryByText(/Volvé a entrar/)).not.toBeInTheDocument()
  })

  it("con estado 'cerrada' y sin fecha igual dice que ya cerró", () => {
    renderFueraDePeriodo({ titulo: "Parcial de prueba", estado: "cerrada" })

    expect(screen.getByText("Esta actividad ya cerró")).toBeInTheDocument()
    expect(screen.queryByText(/Cerró el/)).not.toBeInTheDocument()
  })

  it("ya no muestra la nota al pie que admitía la ambigüedad", () => {
    renderFueraDePeriodo({ titulo: "Repaso Unidad 4", estado: "todavia_no_abrio" })

    expect(
      screen.queryByText(/después del cierre y nunca iniciaste la evaluación/),
    ).not.toBeInTheDocument()
  })
})
