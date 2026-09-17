import { cleanup, render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, describe, expect, it } from "vitest"

import { RecuperarPasswordExito } from "@/pages/identidad/RecuperarPasswordExito"

describe("RecuperarPasswordExito", () => {
  afterEach(() => {
    cleanup()
  })

  it("muestra la confirmación y un link a /login", () => {
    render(
      <MemoryRouter initialEntries={["/recuperar-password/exito"]}>
        <Routes>
          <Route path="/recuperar-password/exito" element={<RecuperarPasswordExito />} />
          <Route path="/login" element={<p>Login</p>} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText("Contraseña actualizada")).toBeInTheDocument()
    expect(screen.getByRole("link", { name: "Iniciar sesión" })).toHaveAttribute("href", "/login")
  })
})
