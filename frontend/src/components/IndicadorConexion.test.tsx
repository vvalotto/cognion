import { cleanup, render, screen } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { IndicadorConexion } from "@/components/IndicadorConexion"

afterEach(cleanup)

describe("IndicadorConexion", () => {
  it("muestra el chip solo mientras reconecta", () => {
    const { rerender } = render(<IndicadorConexion estado="reconectando" />)
    expect(screen.getByRole("status")).toHaveTextContent("Reconectando…")

    rerender(<IndicadorConexion estado="conectado" />)
    expect(screen.queryByRole("status")).not.toBeInTheDocument()
  })

  it("no se muestra desconectado", () => {
    render(<IndicadorConexion estado="desconectado" />)
    expect(screen.queryByRole("status")).not.toBeInTheDocument()
  })
})
