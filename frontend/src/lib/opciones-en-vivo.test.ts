import { describe, expect, it } from "vitest"

import { estiloOpcion, filasHistograma, opcionesEnVivo } from "@/lib/opciones-en-vivo"

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

describe("filasHistograma", () => {
  const correcta = { contenido: { opcion_indice: 1 }, opciones: ["uno", "dos", "tres"] }

  it("una fila por opción, con las que nadie eligió en 0 y la correcta marcada", () => {
    const filas = filasHistograma("opcion_multiple", correcta, [{ opcion: "1", cantidad: 4 }])
    expect(filas).toEqual([
      { texto: "uno", color: "a", cantidad: 0, esCorrecta: false },
      { texto: "dos", color: "b", cantidad: 4, esCorrecta: true },
      { texto: "tres", color: "c", cantidad: 0, esCorrecta: false },
    ])
  })

  it("Verdadero/Falso usa las claves verdadero/falso y el valor correcto", () => {
    const filas = filasHistograma("verdadero_falso", { contenido: { valor: false }, opciones: null }, [
      { opcion: "verdadero", cantidad: 2 },
      { opcion: "falso", cantidad: 5 },
    ])
    expect(filas).toEqual([
      { texto: "Verdadero", color: "b", cantidad: 2, esCorrecta: false },
      { texto: "Falso", color: "c", cantidad: 5, esCorrecta: true },
    ])
  })

  it("sin respuesta correcta no marca ninguna ni inventa opciones", () => {
    expect(filasHistograma("opcion_multiple", null, [])).toEqual([])
    expect(filasHistograma("verdadero_falso", null, []).every((f) => !f.esCorrecta)).toBe(true)
  })
})
