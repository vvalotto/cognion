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

  it("Estudiante sigue viendo el placeholder", () => {
    setSession({ token: "t", rol: "estudiante" })

    renderInicio()

    expect(screen.getByText("Sesión iniciada — pendiente de pantalla propia")).toBeInTheDocument()
  })

  it("Administrador sigue viendo el placeholder", () => {
    setSession({ token: "t", rol: "administrador" })

    renderInicio()

    expect(screen.getByText("Sesión iniciada — pendiente de pantalla propia")).toBeInTheDocument()
  })
})
