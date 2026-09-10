import { cleanup, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, describe, expect, it } from "vitest"

import { HomeAdministrador } from "@/pages/HomeAdministrador"

function renderHomeAdministrador() {
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route path="/" element={<HomeAdministrador />} />
        <Route path="/comisiones" element={<p>Comisiones listado</p>} />
        <Route path="/cuentas" element={<p>Cuentas listado</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("HomeAdministrador", () => {
  afterEach(() => {
    cleanup()
  })

  it("muestra el saludo genérico", () => {
    renderHomeAdministrador()

    expect(screen.getByRole("heading", { name: "Hola, Administrador" })).toBeInTheDocument()
  })

  it("muestra las 3 cards de acceso", () => {
    renderHomeAdministrador()

    expect(screen.getByText("Materias")).toBeInTheDocument()
    expect(screen.getByText("Comisiones")).toBeInTheDocument()
    expect(screen.getByText("Cuentas")).toBeInTheDocument()
  })

  it("navega a /comisiones al hacer clic en Comisiones", async () => {
    renderHomeAdministrador()
    const user = userEvent.setup()

    await user.click(screen.getByText("Comisiones"))

    expect(await screen.findByText("Comisiones listado")).toBeInTheDocument()
  })

  it("navega a /cuentas al hacer clic en Cuentas", async () => {
    renderHomeAdministrador()
    const user = userEvent.setup()

    await user.click(screen.getByText("Cuentas"))

    expect(await screen.findByText("Cuentas listado")).toBeInTheDocument()
  })

  it("navega con Enter cuando la card tiene foco", async () => {
    renderHomeAdministrador()
    const user = userEvent.setup()

    ;(screen.getByText("Comisiones").closest('[role="button"]') as HTMLElement).focus()
    await user.keyboard("{Enter}")

    await waitFor(() => {
      expect(screen.getByText("Comisiones listado")).toBeInTheDocument()
    })
  })
})
