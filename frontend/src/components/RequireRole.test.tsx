import { cleanup, render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it } from "vitest"

import { RequireRole } from "@/components/RequireRole"
import { clearSession, setSession } from "@/lib/session"

function renderProtected() {
  return render(
    <MemoryRouter initialEntries={["/docentes/nuevo"]}>
      <Routes>
        <Route
          path="/docentes/nuevo"
          element={
            <RequireRole rol="administrador">
              <p>contenido protegido</p>
            </RequireRole>
          }
        />
        <Route path="/login" element={<p>Login</p>} />
      </Routes>
    </MemoryRouter>
  )
}

describe("RequireRole (integración)", () => {
  beforeEach(() => {
    clearSession()
  })

  afterEach(() => {
    cleanup()
  })

  it("sin sesión redirige a /login", () => {
    renderProtected()

    expect(screen.getByText("Login")).toBeInTheDocument()
    expect(screen.queryByText("contenido protegido")).not.toBeInTheDocument()
  })

  it("con sesión de rol distinto muestra acceso denegado", () => {
    setSession({ token: "t", rol: "docente" })

    renderProtected()

    expect(screen.getByText("Acceso denegado")).toBeInTheDocument()
    expect(screen.queryByText("contenido protegido")).not.toBeInTheDocument()
  })

  it("con sesión del rol requerido renderiza el contenido", () => {
    setSession({ token: "t", rol: "administrador" })

    renderProtected()

    expect(screen.getByText("contenido protegido")).toBeInTheDocument()
  })
})
