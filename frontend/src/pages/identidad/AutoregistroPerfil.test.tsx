import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, describe, expect, it } from "vitest"

import { AutoregistroPerfil } from "@/pages/identidad/AutoregistroPerfil"

function renderPantalla() {
  return render(
    <MemoryRouter initialEntries={["/autoregistro"]}>
      <Routes>
        <Route path="/autoregistro" element={<AutoregistroPerfil />} />
        <Route path="/autoregistro/docente" element={<p>Autoregistro Docente</p>} />
        <Route path="/autoregistro/estudiante" element={<p>Autoregistro Estudiante</p>} />
        <Route path="/login" element={<p>Login</p>} />
      </Routes>
    </MemoryRouter>
  )
}

describe("AutoregistroPerfil", () => {
  afterEach(() => {
    cleanup()
  })

  it("elegir 'Soy Docente' navega a /autoregistro/docente", async () => {
    const user = userEvent.setup()
    renderPantalla()

    await user.click(screen.getByText("Soy Docente"))

    expect(await screen.findByText("Autoregistro Docente")).toBeInTheDocument()
  })

  it("elegir 'Soy Estudiante' navega a /autoregistro/estudiante", async () => {
    const user = userEvent.setup()
    renderPantalla()

    await user.click(screen.getByText("Soy Estudiante"))

    expect(await screen.findByText("Autoregistro Estudiante")).toBeInTheDocument()
  })

  it("el link '¿Ya tenés cuenta? Iniciar sesión' navega a /login", async () => {
    const user = userEvent.setup()
    renderPantalla()

    await user.click(screen.getByRole("link", { name: "Iniciar sesión" }))

    expect(await screen.findByText("Login")).toBeInTheDocument()
  })

  it("no ofrece un tercer perfil de Administrador (INV-ID-15)", () => {
    renderPantalla()

    expect(screen.queryByText(/Administrador/)).not.toBeInTheDocument()
  })
})
