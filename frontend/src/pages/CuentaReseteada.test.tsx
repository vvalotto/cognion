import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, describe, expect, it } from "vitest"

import { CuentaReseteada } from "@/pages/CuentaReseteada"

describe("CuentaReseteada", () => {
  afterEach(() => {
    cleanup()
  })

  it("muestra el nombre de la cuenta recibido por navegación", () => {
    render(
      <MemoryRouter initialEntries={[{ pathname: "/cuentas/u1/reseteada", state: { nombre: "Ana" } }]}>
        <Routes>
          <Route path="/cuentas/:usuarioId/reseteada" element={<CuentaReseteada />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText(/Se reseteó la contraseña de Ana/)).toBeInTheDocument()
  })

  it("muestra un mensaje genérico si se accede sin state (fallback)", () => {
    render(
      <MemoryRouter initialEntries={["/cuentas/u1/reseteada"]}>
        <Routes>
          <Route path="/cuentas/:usuarioId/reseteada" element={<CuentaReseteada />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText(/Se reseteó la contraseña y la cuenta quedó desbloqueada\./)).toBeInTheDocument()
  })

  it("[US-ADJ-04] muestra un ícono de éxito dentro de una tarjeta centrada", () => {
    render(
      <MemoryRouter initialEntries={[{ pathname: "/cuentas/u1/reseteada", state: { nombre: "Ana" } }]}>
        <Routes>
          <Route path="/cuentas/:usuarioId/reseteada" element={<CuentaReseteada />} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText("✓")).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "Contraseña reseteada" })).toBeInTheDocument()
  })

  it("'Volver al listado de cuentas' navega a /cuentas", async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter initialEntries={["/cuentas/u1/reseteada"]}>
        <Routes>
          <Route path="/cuentas/:usuarioId/reseteada" element={<CuentaReseteada />} />
          <Route path="/cuentas" element={<p>Listado de cuentas</p>} />
        </Routes>
      </MemoryRouter>,
    )

    await user.click(screen.getByRole("button", { name: "Volver al listado de cuentas" }))

    expect(await screen.findByText("Listado de cuentas")).toBeInTheDocument()
  })
})
