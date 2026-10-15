import { cleanup, render, screen } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { LoginCuentaBloqueadaTemporalError } from "@/pages/identidad/LoginCuentaBloqueadaTemporalError"

describe("LoginCuentaBloqueadaTemporalError", () => {
  afterEach(cleanup)

  it("redondea los segundos hacia arriba a minutos", () => {
    render(<LoginCuentaBloqueadaTemporalError segundos={601} />)

    expect(screen.getByRole("alert")).toHaveTextContent("Cuenta bloqueada temporalmente")
    expect(screen.getByRole("alert")).toHaveTextContent("unos 11 minutos")
  })

  it("usa un mínimo de un minuto, en singular", () => {
    render(<LoginCuentaBloqueadaTemporalError segundos={3} />)

    expect(screen.getByRole("alert")).toHaveTextContent("unos 1 minuto.")
  })
})
