import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { AltaDocente } from "@/pages/identidad/AltaDocente"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function renderAltaDocente() {
  return render(
    <MemoryRouter initialEntries={["/docentes/nuevo"]}>
      <Routes>
        <Route path="/docentes/nuevo" element={<AltaDocente />} />
        <Route path="/docentes/nuevo/exito" element={<p>Alta docente exito</p>} />
        <Route path="/" element={<p>Inicio</p>} />
      </Routes>
    </MemoryRouter>
  )
}

async function completarFormulario(
  email: string,
  password = "password123",
  confirmar = password
) {
  const user = userEvent.setup()
  await user.type(screen.getByLabelText("Nombre completo"), "Ana")
  await user.type(screen.getByLabelText("Email"), email)
  await user.type(screen.getByLabelText("Contraseña temporal"), password)
  await user.type(screen.getByLabelText("Confirmar contraseña"), confirmar)
  await user.click(screen.getByRole("button", { name: "Crear cuenta de Docente" }))
}

describe("AltaDocente", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra el perfil fijo en Docente, sin selector", () => {
    renderAltaDocente()

    expect(screen.getByText("Docente")).toBeInTheDocument()
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument()
  })

  it("alta exitosa crea el usuario y muestra la pantalla de confirmación", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(201, { id: "u1", nombre: "Ana", email: "ana@fiuner.edu.ar", perfil: "docente" })
    )

    renderAltaDocente()
    await completarFormulario("ana@fiuner.edu.ar")

    expect(await screen.findByText("Alta docente exito")).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/usuarios"),
      expect.objectContaining({ method: "POST" })
    )
  })

  it("email ya registrado (409) muestra el error en el propio formulario, sin navegar", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(409, { detail: "El email ya está registrado." })
    )

    renderAltaDocente()
    await completarFormulario("ya-existe@fiuner.edu.ar")

    expect(await screen.findByRole("alert")).toHaveTextContent("Ese email ya está registrado.")
    expect(screen.getByLabelText("Email")).toHaveValue("ya-existe@fiuner.edu.ar")
  })

  it("contraseñas que no coinciden muestran error de cliente sin llamar al backend", async () => {
    renderAltaDocente()
    await completarFormulario("ana@fiuner.edu.ar", "password123", "otra-password")

    expect(await screen.findByRole("alert")).toHaveTextContent("Las contraseñas no coinciden.")
    expect(fetch).not.toHaveBeenCalled()
  })
})
