import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, describe, expect, it } from "vitest"

import { RecuperarPasswordSolicitado } from "@/pages/identidad/RecuperarPasswordSolicitado"

function renderPantalla() {
  return render(
    <MemoryRouter initialEntries={["/recuperar-password/solicitado"]}>
      <Routes>
        <Route path="/recuperar-password/solicitado" element={<RecuperarPasswordSolicitado />} />
        <Route path="/login" element={<p>Iniciar sesión</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("RecuperarPasswordSolicitado", () => {
  afterEach(() => {
    cleanup()
  })

  it("muestra el mensaje genérico y la vigencia del link", () => {
    renderPantalla()

    expect(screen.getByText(/si el email ingresado corresponde a una cuenta/i)).toBeInTheDocument()
    expect(screen.getByText(/1 hora/)).toBeInTheDocument()
  })

  it("el botón 'Volver a iniciar sesión' navega a /login", async () => {
    const user = userEvent.setup()
    renderPantalla()

    await user.click(screen.getByRole("link", { name: "Volver a iniciar sesión" }))

    expect(await screen.findByText("Iniciar sesión")).toBeInTheDocument()
  })
})
