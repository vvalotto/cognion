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

  it("muestra un mensaje genérico si no llega navigation state", () => {
    renderFueraDePeriodo()

    expect(screen.getByText("Todavía no está disponible")).toBeInTheDocument()
    expect(
      screen.getByText("Volvé a entrar cuando la actividad esté disponible."),
    ).toBeInTheDocument()
  })

  it("aclara que el mismo mensaje aplica si el período ya cerró", () => {
    renderFueraDePeriodo({ titulo: "Repaso Unidad 4" })

    expect(
      screen.getByText(/después del cierre y nunca iniciaste la evaluación/),
    ).toBeInTheDocument()
  })
})
