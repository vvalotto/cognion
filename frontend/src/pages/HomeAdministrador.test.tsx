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
        <Route path="/materias" element={<p>Materias listado</p>} />
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

  it("muestra las 2 cards de acceso — las Comisiones se gestionan desde Materias", () => {
    renderHomeAdministrador()

    expect(screen.getByText("Materias")).toBeInTheDocument()
    expect(screen.getByText("Cuentas")).toBeInTheDocument()
    expect(screen.queryByText("Comisiones")).not.toBeInTheDocument()
  })

  it("navega a /materias al hacer clic en Materias", async () => {
    renderHomeAdministrador()
    const user = userEvent.setup()

    await user.click(screen.getByText("Materias"))

    expect(await screen.findByText("Materias listado")).toBeInTheDocument()
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

    ;(screen.getByText("Materias").closest('[role="button"]') as HTMLElement).focus()
    await user.keyboard("{Enter}")

    await waitFor(() => {
      expect(screen.getByText("Materias listado")).toBeInTheDocument()
    })
  })
})
