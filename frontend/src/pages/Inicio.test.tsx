import { cleanup, render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router"
import { afterEach, describe, expect, it } from "vitest"

import { Inicio } from "@/pages/Inicio"
import { clearSession, setSession } from "@/lib/session"

function renderInicio() {
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <Inicio />
    </MemoryRouter>,
  )
}

describe("Inicio", () => {
  afterEach(() => {
    clearSession()
    cleanup()
  })

  it("Docente ve HomeDocente", () => {
    setSession({ token: "t", rol: "docente" })

    renderInicio()

    expect(screen.getByRole("heading", { name: "Hola, Docente" })).toBeInTheDocument()
  })

  it("Estudiante ve HomeEstudiante", () => {
    setSession({ token: "t", rol: "estudiante" })

    renderInicio()

    expect(screen.getByRole("heading", { name: "Hola, Estudiante" })).toBeInTheDocument()
  })

  it("Administrador ve HomeAdministrador", () => {
    setSession({ token: "t", rol: "administrador" })

    renderInicio()

    expect(screen.getByRole("heading", { name: "Hola, Administrador" })).toBeInTheDocument()
  })

  it("sin rol reconocido muestra el placeholder (fallback defensivo)", () => {
    renderInicio()

    expect(screen.getByText("Sesión iniciada — pendiente de pantalla propia")).toBeInTheDocument()
  })
})
