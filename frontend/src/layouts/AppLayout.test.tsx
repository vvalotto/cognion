import { cleanup, render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it } from "vitest"

import { AppLayout } from "@/layouts/AppLayout"
import { clearSession, setSession } from "@/lib/session"

function renderAppLayout() {
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<p>contenido</p>} />
        </Route>
      </Routes>
    </MemoryRouter>
  )
}

describe("AppLayout (integración)", () => {
  beforeEach(() => {
    clearSession()
  })

  afterEach(() => {
    cleanup()
  })

  it("muestra el rol del usuario autenticado en el header", () => {
    setSession({ token: "t", rol: "administrador" })

    renderAppLayout()

    expect(screen.getByText("Administrador")).toBeInTheDocument()
  })

  it("no muestra información de usuario sin sesión activa", () => {
    renderAppLayout()

    expect(screen.queryByText("Administrador")).not.toBeInTheDocument()
    expect(screen.queryByText("Docente")).not.toBeInTheDocument()
  })

  it("renderiza el contenido anidado vía Outlet", () => {
    renderAppLayout()

    expect(screen.getByText("contenido")).toBeInTheDocument()
  })

  it("muestra la marca institucional y la barra superior", () => {
    renderAppLayout()

    expect(screen.getByText("Cognión")).toBeInTheDocument()
    expect(screen.getByText("FACULTAD DE INGENIERÍA · UNER")).toBeInTheDocument()
  })

  it("muestra las iniciales del rol en el avatar", () => {
    setSession({ token: "t", rol: "administrador" })

    renderAppLayout()

    expect(screen.getByText("AD")).toBeInTheDocument()
  })

  it("muestra el menú de navegación con sesión activa", () => {
    setSession({ token: "t", rol: "administrador" })

    renderAppLayout()

    expect(screen.getByText("Comisiones")).toBeInTheDocument()
    expect(screen.getByText("Cuentas")).toBeInTheDocument()
  })

  it("no muestra el menú de navegación sin sesión activa", () => {
    renderAppLayout()

    expect(screen.queryByText("Comisiones")).not.toBeInTheDocument()
  })

  it("muestra el menú correspondiente al rol Docente", () => {
    setSession({ token: "t", rol: "docente" })

    renderAppLayout()

    expect(screen.getByText("Banco de Preguntas")).toBeInTheDocument()
    expect(screen.queryByText("Comisiones")).not.toBeInTheDocument()
  })
})
