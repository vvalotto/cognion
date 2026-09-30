import { describe, expect, it, vi } from "vitest"

import { esEnteroPositivo, soloEnterosPositivos } from "@/lib/entero-positivo"

describe("esEnteroPositivo", () => {
  it.each([
    [1, true],
    [20, true],
    [0, false],
    [-3, false],
    [2.5, false],
    [Number.NaN, false],
  ])("%s → %s", (valor, esperado) => {
    expect(esEnteroPositivo(valor)).toBe(esperado)
  })
})

describe("soloEnterosPositivos", () => {
  it.each(["-", "+", "e", "E", ".", ","])("bloquea '%s'", (key) => {
    const preventDefault = vi.fn()
    soloEnterosPositivos({ key, preventDefault } as never)
    expect(preventDefault).toHaveBeenCalled()
  })

  it("deja pasar dígitos y teclas de edición", () => {
    for (const key of ["5", "0", "Backspace", "ArrowUp", "Tab"]) {
      const preventDefault = vi.fn()
      soloEnterosPositivos({ key, preventDefault } as never)
      expect(preventDefault).not.toHaveBeenCalled()
    }
  })
})
