import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { Cuentas } from "@/pages/Cuentas"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function paginado<T>(cuentas: T[]): { cuentas: T[]; total: number } {
  return { cuentas, total: cuentas.length }
}

const cuentasResponse = [
  { id: "u1", nombre: "Ana Docente", email: "ana@fiuner.edu.ar", perfil: "docente", bloqueada: false },
  {
    id: "u2",
    nombre: "Luis Estudiante",
    email: "luis@fiuner.edu.ar",
    perfil: "estudiante",
    bloqueada: true,
  },
]

function renderCuentas() {
  return render(
    <MemoryRouter initialEntries={["/cuentas"]}>
      <Routes>
        <Route path="/cuentas" element={<Cuentas />} />
        <Route path="/cuentas/:usuarioId" element={<p>Detalle de cuenta</p>} />
        <Route path="/docentes/nuevo" element={<p>Alta de docente</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("Cuentas", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra todas las cuentas sin filtros al entrar a la pantalla", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, paginado(cuentasResponse)))

    renderCuentas()

    expect(await screen.findByText("Ana Docente")).toBeInTheDocument()
    expect(screen.getByText("Luis Estudiante")).toBeInTheDocument()
  })

  it("filtrar por rol y estado consulta el backend con ambos filtros combinados", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, paginado(cuentasResponse)))
      .mockResolvedValueOnce(jsonResponse(200, paginado([cuentasResponse[1]])))
      .mockResolvedValueOnce(jsonResponse(200, paginado([cuentasResponse[1]])))
    const user = userEvent.setup()

    renderCuentas()
    await screen.findByText("Ana Docente")

    await user.selectOptions(screen.getByLabelText("Rol"), "estudiante")
    await user.selectOptions(screen.getByLabelText("Estado"), "bloqueada")

    await screen.findByText("Luis Estudiante")
    expect(screen.queryByText("Ana Docente")).not.toBeInTheDocument()
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)?.[0] as string
    expect(ultimaLlamada).toContain("rol=estudiante")
    expect(ultimaLlamada).toContain("estado=bloqueada")
  })

  it("una combinación de filtros sin resultados deja la tabla vacía sin mensaje de error", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, paginado(cuentasResponse)))
      .mockResolvedValueOnce(jsonResponse(200, paginado([])))
    const user = userEvent.setup()

    renderCuentas()
    await screen.findByText("Ana Docente")

    await user.selectOptions(screen.getByLabelText("Rol"), "administrador")

    expect(await screen.findByText(/No hay cuentas/)).toBeInTheDocument()
    expect(screen.queryByText(/error/i)).not.toBeInTheDocument()
  })

  it("'Limpiar filtros' vuelve al listado sin filtros", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, paginado(cuentasResponse)))
      .mockResolvedValueOnce(jsonResponse(200, paginado([cuentasResponse[1]])))
      .mockResolvedValueOnce(jsonResponse(200, paginado(cuentasResponse)))
    const user = userEvent.setup()

    renderCuentas()
    await screen.findByText("Ana Docente")
    await user.selectOptions(screen.getByLabelText("Rol"), "estudiante")
    await screen.findByText("Luis Estudiante")

    await user.click(screen.getByText("Limpiar filtros"))

    await screen.findByText("Ana Docente")
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)?.[0] as string
    expect(ultimaLlamada).not.toContain("rol=")
  })

  it("hacer clic en una fila navega al detalle de esa cuenta", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, paginado(cuentasResponse)))
    const user = userEvent.setup()

    renderCuentas()
    await screen.findByText("Ana Docente")

    await user.click(screen.getByText("Ana Docente"))

    expect(await screen.findByText("Detalle de cuenta")).toBeInTheDocument()
  })

  it("'+ Nueva cuenta' navega al alta de docente existente", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, paginado(cuentasResponse)))
    const user = userEvent.setup()

    renderCuentas()
    await screen.findByText("Ana Docente")

    await user.click(screen.getByText("+ Nueva cuenta"))

    expect(await screen.findByText("Alta de docente")).toBeInTheDocument()
  })

  it("[US-ADJ-04] Rol y Estado se muestran con tags de color y cada fila tiene un botón Ver", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, paginado(cuentasResponse)))

    renderCuentas()
    await screen.findByText("Ana Docente")

    const badge = (texto: string) =>
      screen.getAllByText(texto).find((el) => el.getAttribute("data-slot") === "badge")
    expect(badge("Docente")).toHaveClass("bg-blue-50")
    expect(badge("Estudiante")).toHaveClass("bg-violet-50")
    expect(badge("Activa")).toHaveClass("bg-green-50")
    expect(badge("Bloqueada")).toHaveClass("bg-red-50")
    expect(screen.getAllByRole("button", { name: "Ver" })).toHaveLength(2)
  })

  it("[US-ADJ-04] el botón Ver navega al detalle sin duplicar la navegación de la fila", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, paginado(cuentasResponse)))
    const user = userEvent.setup()

    renderCuentas()
    await screen.findByText("Ana Docente")

    await user.click(screen.getAllByRole("button", { name: "Ver" })[0])

    expect(await screen.findByText("Detalle de cuenta")).toBeInTheDocument()
  })

  function paginaDe20(offset: number) {
    return Array.from({ length: 20 }, (_, i) => ({
      id: `pag-${offset + i}`,
      nombre: `Cuenta ${offset + i}`,
      email: `cuenta${offset + i}@fiuner.edu.ar`,
      perfil: "docente",
      bloqueada: false,
    }))
  }

  it("[US-ADJ-05] listado con más de una página muestra los controles de paginación", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, { cuentas: paginaDe20(1), total: 45 }))

    renderCuentas()

    expect(await screen.findByText("Cuenta 1")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "3" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Siguiente" })).toBeEnabled()
    expect(screen.getByRole("button", { name: "Anterior" })).toBeDisabled()
  })

  it("[US-ADJ-05] cambiar de página pide la página siguiente al backend", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, { cuentas: paginaDe20(1), total: 45 }))
      .mockResolvedValueOnce(jsonResponse(200, { cuentas: paginaDe20(21), total: 45 }))
    const user = userEvent.setup()

    renderCuentas()
    await screen.findByText("Cuenta 1")

    await user.click(screen.getByRole("button", { name: "Siguiente" }))

    expect(await screen.findByText("Cuenta 21")).toBeInTheDocument()
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)?.[0] as string
    expect(ultimaLlamada).toContain("pagina=2")
    expect(ultimaLlamada).toContain("tamanio_pagina=20")
  })

  it("[US-ADJ-05] cambiar un filtro reinicia la paginación a la página 1", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, { cuentas: paginaDe20(1), total: 45 }))
      .mockResolvedValueOnce(jsonResponse(200, { cuentas: paginaDe20(21), total: 45 }))
      .mockResolvedValueOnce(jsonResponse(200, { cuentas: paginaDe20(1), total: 10 }))
    const user = userEvent.setup()

    renderCuentas()
    await screen.findByText("Cuenta 1")
    await user.click(screen.getByRole("button", { name: "Siguiente" }))
    await screen.findByText("Cuenta 21")

    await user.selectOptions(screen.getByLabelText("Estado"), "bloqueada")

    await screen.findByText("Cuenta 1")
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)?.[0] as string
    expect(ultimaLlamada).toContain("pagina=1")
  })

  it("[US-ADJ-05] listado con una sola página no muestra controles de paginación", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, paginado(cuentasResponse)))

    renderCuentas()
    await screen.findByText("Ana Docente")

    expect(screen.queryByRole("navigation", { name: "Paginación" })).not.toBeInTheDocument()
  })
})
