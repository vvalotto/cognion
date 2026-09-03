import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, describe, expect, it } from "vitest"

import { AltaDocenteExito } from "@/pages/identidad/AltaDocenteExito"

describe("AltaDocenteExito", () => {
  afterEach(() => {
    cleanup()
  })

  it("muestra nombre y email del Docente recibidos por navegación", () => {
    render(
      <MemoryRouter
        initialEntries={[
          { pathname: "/docentes/nuevo/exito", state: { nombre: "Ana", email: "ana@fiuner.edu.ar" } },
        ]}
      >
        <Routes>
          <Route path="/docentes/nuevo/exito" element={<AltaDocenteExito />} />
          <Route path="/docentes/nuevo" element={<p>Alta docente</p>} />
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByText(/Ana \(ana@fiuner\.edu\.ar\)/)).toBeInTheDocument()
    expect(screen.getByText("Todavía no está asignado a ninguna comisión.")).toBeInTheDocument()
  })

  it("muestra un mensaje genérico si se accede sin state (fallback)", () => {
    render(
      <MemoryRouter initialEntries={["/docentes/nuevo/exito"]}>
        <Routes>
          <Route path="/docentes/nuevo/exito" element={<AltaDocenteExito />} />
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByText("Se creó la cuenta del Docente.")).toBeInTheDocument()
  })

  it("el botón 'Dar de alta otro Docente' navega de vuelta al formulario", async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter initialEntries={["/docentes/nuevo/exito"]}>
        <Routes>
          <Route path="/docentes/nuevo/exito" element={<AltaDocenteExito />} />
          <Route path="/docentes/nuevo" element={<p>Alta docente</p>} />
        </Routes>
      </MemoryRouter>
    )

    await user.click(screen.getByRole("button", { name: "Dar de alta otro Docente" }))

    expect(await screen.findByText("Alta docente")).toBeInTheDocument()
  })
})
