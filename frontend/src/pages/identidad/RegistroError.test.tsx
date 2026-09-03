import { render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router"
import { describe, expect, it } from "vitest"

import { RegistroError } from "@/pages/identidad/RegistroError"

describe("RegistroError", () => {
  it("muestra el mensaje genérico y no muestra un formulario", () => {
    render(
      <MemoryRouter initialEntries={["/registro/error"]}>
        <Routes>
          <Route path="/registro/error" element={<RegistroError />} />
          <Route path="/login" element={<p>Login</p>} />
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByText("Este link ya no es válido")).toBeInTheDocument()
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument()
    expect(screen.getByRole("link", { name: "Ir a iniciar sesión" })).toHaveAttribute(
      "href",
      "/login"
    )
  })
})
