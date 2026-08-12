import { render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router"
import { describe, expect, it } from "vitest"

import { RegistroExito } from "@/pages/RegistroExito"

describe("RegistroExito", () => {
  it("muestra el nombre de la comisión recibido por navegación", () => {
    render(
      <MemoryRouter
        initialEntries={[{ pathname: "/registro/exito", state: { materia: "Ingeniería de Software" } }]}
      >
        <Routes>
          <Route path="/registro/exito" element={<RegistroExito />} />
          <Route path="/login" element={<p>Login</p>} />
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByText(/Ingeniería de Software/)).toBeInTheDocument()
    expect(screen.getByRole("link", { name: "Iniciar sesión" })).toHaveAttribute("href", "/login")
  })

  it("muestra un mensaje genérico si se accede sin state (fallback)", () => {
    render(
      <MemoryRouter initialEntries={["/registro/exito"]}>
        <Routes>
          <Route path="/registro/exito" element={<RegistroExito />} />
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByText("Ya quedaste asignado automáticamente a tu comisión.")).toBeInTheDocument()
  })
})
