import { cleanup, render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, describe, expect, it } from "vitest"

import { AppNav } from "@/components/AppNav"

function renderAppNav(rol: "docente" | "estudiante" | "administrador", initialPath = "/") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="*" element={<AppNav rol={rol} />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("AppNav", () => {
  afterEach(() => {
    cleanup()
  })

  it("Docente ve sus 5 ítems", () => {
    renderAppNav("docente")

    expect(screen.getByText("Inicio")).toBeInTheDocument()
    expect(screen.getByText("Banco de Preguntas")).toBeInTheDocument()
    expect(screen.getByText("Actividades")).toBeInTheDocument()
    expect(screen.getByText("Desempeño por alumno")).toBeInTheDocument()
    expect(screen.getByText("Desempeño por tema")).toBeInTheDocument()
    expect(screen.getAllByRole("link")).toHaveLength(5)
  })

  it("Estudiante ve sus 3 ítems", () => {
    renderAppNav("estudiante")

    expect(screen.getByText("Inicio")).toBeInTheDocument()
    expect(screen.getByText("Mis Actividades")).toBeInTheDocument()
    expect(screen.getByText("Mi Desempeño")).toBeInTheDocument()
    expect(screen.getAllByRole("link")).toHaveLength(3)
  })

  it("Administrador ve sus 5 ítems", () => {
    renderAppNav("administrador")

    expect(screen.getByText("Inicio")).toBeInTheDocument()
    expect(screen.getByText("Comisiones")).toBeInTheDocument()
    expect(screen.getByText("Materias")).toBeInTheDocument()
    expect(screen.getByText("Docentes")).toBeInTheDocument()
    expect(screen.getByText("Cuentas")).toBeInTheDocument()
    expect(screen.getAllByRole("link")).toHaveLength(5)
  })

  it("marca el ítem de la sección actual como activo", () => {
    renderAppNav("docente", "/actividad-evaluativa/materias")

    expect(screen.getByText("Actividades")).toHaveAttribute("aria-current", "page")
    expect(screen.getByText("Inicio")).not.toHaveAttribute("aria-current")
  })

  it("marca como activo un ítem cuya ruta es prefijo de una sub-ruta", () => {
    renderAppNav("docente", "/materias/m1/banco")

    expect(screen.getByText("Banco de Preguntas")).toHaveAttribute("aria-current", "page")
  })

  it("solo marca 'Inicio' como activo en la raíz, no en cualquier ruta", () => {
    renderAppNav("docente", "/materias")

    expect(screen.getByText("Inicio")).not.toHaveAttribute("aria-current")
  })

  it("cada ítem navega a su ruta destino (atributo href)", () => {
    renderAppNav("administrador")

    expect(screen.getByText("Comisiones")).toHaveAttribute("href", "/comisiones")
    expect(screen.getByText("Docentes")).toHaveAttribute("href", "/docentes/nuevo")
    expect(screen.getByText("Cuentas")).toHaveAttribute("href", "/cuentas")
  })
})
