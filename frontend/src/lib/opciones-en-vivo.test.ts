import { describe, expect, it } from "vitest"

import { estiloOpcion, opcionesEnVivo } from "@/lib/opciones-en-vivo"

describe("opcionesEnVivo", () => {
  it("reparte los colores a, b, c, d en orden", () => {
    const opciones = opcionesEnVivo("opcion_multiple", ["uno", "dos", "tres", "cuatro"])
    expect(opciones.map((o) => o.color)).toEqual(["a", "b", "c", "d"])
    expect(opciones.map((o) => o.texto)).toEqual(["uno", "dos", "tres", "cuatro"])
  })

  it("con 3 opciones usa a, b, c", () => {
    expect(opcionesEnVivo("opcion_multiple", ["x", "y", "z"]).map((o) => o.color)).toEqual([
      "a",
      "b",
      "c",
    ])
  })

  it("con más de 4 opciones repite los colores cíclicamente", () => {
    const colores = opcionesEnVivo("opcion_multiple", ["1", "2", "3", "4", "5", "6"]).map(
      (o) => o.color,
    )
    expect(colores).toEqual(["a", "b", "c", "d", "a", "b"])
  })

  it("Verdadero/Falso son dos cajas b y c, sin depender de las opciones", () => {
    expect(opcionesEnVivo("verdadero_falso", null)).toEqual([
      { texto: "Verdadero", color: "b" },
      { texto: "Falso", color: "c" },
    ])
  })

  it("sin opciones devuelve una lista vacía", () => {
    expect(opcionesEnVivo("opcion_multiple", null)).toEqual([])
  })
})

describe("estiloOpcion", () => {
  it("usa el token de color de la proyección", () => {
    expect(estiloOpcion("a")).toEqual({ background: "var(--stage-color-a)", color: "#ffffff" })
  })

  it("el amarillo lleva texto oscuro", () => {
    expect(estiloOpcion("c").color).toBe("#2a1c00")
  })
})
