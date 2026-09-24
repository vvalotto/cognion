import { describe, expect, it } from "vitest"

import { top3 } from "@/lib/ranking-en-vivo"

describe("top3", () => {
  it("ordena por posición y corta en 3", () => {
    const ranking = [4, 2, 6, 1, 3, 5].map((posicion) => ({ posicion }))
    expect(top3(ranking).map((r) => r.posicion)).toEqual([1, 2, 3])
  })

  it("con menos de 3 devuelve los que haya, sin mutar el original", () => {
    const ranking = [{ posicion: 2 }, { posicion: 1 }]
    expect(top3(ranking)).toEqual([{ posicion: 1 }, { posicion: 2 }])
    expect(ranking[0].posicion).toBe(2)
    expect(top3([])).toEqual([])
  })
})
