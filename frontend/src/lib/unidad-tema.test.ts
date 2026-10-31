import { describe, expect, it } from "vitest"

import {
  sugerenciasDeTema,
  temasDeUnidad,
  temaTrasCambiarUnidad,
  unidadesDe,
} from "./unidad-tema"

const BANCO = [
  { unidadTematica: "U1 Fundamentos", tema: "Principios" },
  { unidadTematica: "U1 Fundamentos", tema: "Calidad" },
  { unidadTematica: "U2 Diseño", tema: "DDD" },
  { unidadTematica: "U2 Diseño", tema: "Clean Architecture" },
  { unidadTematica: "U3 Arquitectura", tema: "Clean Architecture" },
  { unidadTematica: "U3 Arquitectura", tema: "Testing" },
  { unidadTematica: "U3 Arquitectura", tema: "Testing" },
]

describe("unidadesDe", () => {
  it("devuelve las unidades sin repetir y ordenadas", () => {
    expect(unidadesDe(BANCO)).toEqual(["U1 Fundamentos", "U2 Diseño", "U3 Arquitectura"])
  })

  it("con un banco vacío no devuelve nada", () => {
    expect(unidadesDe([])).toEqual([])
  })
})

describe("temasDeUnidad", () => {
  it("con la unidad vacía ('Todas') ofrece todos los temas del banco, sin repetir", () => {
    expect(temasDeUnidad(BANCO, "")).toEqual([
      "Calidad",
      "Clean Architecture",
      "DDD",
      "Principios",
      "Testing",
    ])
  })

  it("con una unidad elegida ofrece solo los temas de esa unidad", () => {
    expect(temasDeUnidad(BANCO, "U1 Fundamentos")).toEqual(["Calidad", "Principios"])
    expect(temasDeUnidad(BANCO, "U3 Arquitectura")).toEqual(["Clean Architecture", "Testing"])
  })

  it("un tema repetido en dos unidades aparece en cada una", () => {
    expect(temasDeUnidad(BANCO, "U2 Diseño")).toContain("Clean Architecture")
    expect(temasDeUnidad(BANCO, "U3 Arquitectura")).toContain("Clean Architecture")
  })

  it("una unidad que no existe no ofrece temas", () => {
    expect(temasDeUnidad(BANCO, "Unidad inexistente")).toEqual([])
  })
})

describe("temaTrasCambiarUnidad", () => {
  it("conserva el tema si la nueva unidad también lo ofrece", () => {
    expect(temaTrasCambiarUnidad(BANCO, "U3 Arquitectura", "Clean Architecture")).toBe(
      "Clean Architecture",
    )
  })

  it("vuelve a 'Todos' (vacío) si la nueva unidad no ofrece el tema", () => {
    expect(temaTrasCambiarUnidad(BANCO, "U2 Diseño", "Calidad")).toBe("")
  })

  it("al pasar a 'Todas' conserva cualquier tema del banco", () => {
    expect(temaTrasCambiarUnidad(BANCO, "", "Calidad")).toBe("Calidad")
  })

  it("sin tema elegido sigue sin tema", () => {
    expect(temaTrasCambiarUnidad(BANCO, "U1 Fundamentos", "")).toBe("")
  })
})

describe("sugerenciasDeTema (cargar y editar pregunta)", () => {
  it("ofrece solo los temas de la unidad escrita o elegida", () => {
    expect(sugerenciasDeTema(BANCO, "U1 Fundamentos")).toEqual(["Calidad", "Principios"])
  })

  it("ignora los espacios en los bordes de la unidad escrita", () => {
    expect(sugerenciasDeTema(BANCO, "  U1 Fundamentos ")).toEqual(["Calidad", "Principios"])
  })

  it("con la unidad en blanco no ofrece nada (no hay 'Todos' en un campo obligatorio)", () => {
    expect(sugerenciasDeTema(BANCO, "")).toEqual([])
    expect(sugerenciasDeTema(BANCO, "   ")).toEqual([])
  })

  it("con una unidad nueva no ofrece nada", () => {
    expect(sugerenciasDeTema(BANCO, "Unidad nueva")).toEqual([])
  })
})
