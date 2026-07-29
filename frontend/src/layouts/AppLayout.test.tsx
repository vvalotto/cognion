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

    expect(screen.getByText("administrador")).toBeInTheDocument()
  })

  it("no muestra información de usuario sin sesión activa", () => {
    renderAppLayout()

    expect(screen.queryByText("administrador")).not.toBeInTheDocument()
    expect(screen.queryByText("docente")).not.toBeInTheDocument()
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
})
