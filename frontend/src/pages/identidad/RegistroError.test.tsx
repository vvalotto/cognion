import { cleanup, render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, describe, expect, it } from "vitest"

import { RegistroError } from "@/pages/identidad/RegistroError"

function renderError(url: string) {
  return render(
    <MemoryRouter initialEntries={[url]}>
      <Routes>
        <Route path="/registro/error" element={<RegistroError />} />
        <Route path="/login" element={<p>Login</p>} />
      </Routes>
    </MemoryRouter>
  )
}

describe("RegistroError", () => {
  afterEach(() => {
    cleanup()
  })

  it("sin motivo reconocible dice que el link no es correcto y no muestra un formulario", () => {
    renderError("/registro/error")

    expect(screen.getByText("Este link no es correcto")).toBeInTheDocument()
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument()
    expect(screen.getByRole("link", { name: "Ir a iniciar sesión" })).toHaveAttribute(
      "href",
      "/login"
    )
  })

  it.each([
    ["vencida", "Este link venció", "Invitación vencida"],
    ["revocada", "Este link fue desactivado", "Invitación desactivada"],
    ["usada", "Este link ya fue utilizado", "Invitación ya utilizada"],
    ["invalida", "Este link no es correcto", "Invitación no válida"],
  ])("el motivo %s muestra su propio título y alerta (US-ADJ-67)", (motivo, titulo, alerta) => {
    renderError(`/registro/error?motivo=${motivo}`)

    expect(screen.getByRole("heading", { name: titulo })).toBeInTheDocument()
    expect(screen.getByRole("alert")).toHaveTextContent(alerta)
  })

  it("un motivo desconocido cae en 'no es correcto'", () => {
    renderError("/registro/error?motivo=cualquiera")

    expect(screen.getByRole("heading", { name: "Este link no es correcto" })).toBeInTheDocument()
  })
})
