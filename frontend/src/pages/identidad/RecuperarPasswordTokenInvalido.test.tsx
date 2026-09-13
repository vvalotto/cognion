import { cleanup, render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, describe, expect, it } from "vitest"

import { RecuperarPasswordTokenInvalido } from "@/pages/identidad/RecuperarPasswordTokenInvalido"

describe("RecuperarPasswordTokenInvalido", () => {
  afterEach(() => {
    cleanup()
  })

  it("muestra el mensaje de link no válido, sin formulario de contraseña", () => {
    render(
      <MemoryRouter initialEntries={["/recuperar-password/invalido"]}>
        <Routes>
          <Route path="/recuperar-password/invalido" element={<RecuperarPasswordTokenInvalido />} />
          <Route path="/recuperar-password" element={<p>Recuperar</p>} />
        </Routes>
      </MemoryRouter>,
    )

    expect(screen.getByText("Este link ya no es válido")).toBeInTheDocument()
    expect(screen.queryByLabelText(/contraseña/i)).not.toBeInTheDocument()
    expect(screen.getByRole("link", { name: "Pedir un nuevo link" })).toHaveAttribute(
      "href",
      "/recuperar-password",
    )
  })
})
