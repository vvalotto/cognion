import { cleanup, render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, describe, expect, it } from "vitest"

import { AuthLayout } from "@/layouts/AuthLayout"

describe("AuthLayout (integración)", () => {
  afterEach(() => {
    cleanup()
  })

  it("muestra la marca institucional y la barra superior", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route element={<AuthLayout />}>
            <Route index element={<p>contenido</p>} />
          </Route>
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByText("Cognión")).toBeInTheDocument()
    expect(screen.getByText("Evaluación universitaria")).toBeInTheDocument()
    expect(screen.getByText("FACULTAD DE INGENIERÍA · UNER")).toBeInTheDocument()
  })

  it("renderiza el contenido anidado vía Outlet", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route element={<AuthLayout />}>
            <Route index element={<p>contenido</p>} />
          </Route>
        </Routes>
      </MemoryRouter>
    )

    expect(screen.getByText("contenido")).toBeInTheDocument()
  })
})
