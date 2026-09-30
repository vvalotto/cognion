import { cleanup, render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, describe, expect, it } from "vitest"

import { AutoregistroExito } from "@/pages/identidad/AutoregistroExito"

describe("AutoregistroExito", () => {
  afterEach(() => {
    cleanup()
  })

  it("muestra el mensaje de confirmación y el link a login", () => {
    render(
      <MemoryRouter initialEntries={["/autoregistro/exito"]}>
        <Routes>
          <Route path="/autoregistro/exito" element={<AutoregistroExito />} />
          <Route path="/login" element={<p>Login</p>} />
        </Routes>
      </MemoryRouter>
    )

    expect(
      screen.getByText("Tu cuenta ya está activa. Iniciá sesión para continuar.")
    ).toBeInTheDocument()
    expect(screen.getByRole("link", { name: "Iniciar sesión" })).toHaveAttribute("href", "/login")
  })
})
