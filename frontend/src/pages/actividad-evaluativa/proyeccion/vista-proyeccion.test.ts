import { describe, expect, it } from "vitest"

import type { EstadoSesionEnVivoResponse } from "@/lib/sesion-en-vivo-api"
import {
  aplicarMensaje,
  calcularVista,
  type VistaProyeccion,
  verRanking,
} from "@/pages/actividad-evaluativa/proyeccion/vista-proyeccion"

const estadoBase: EstadoSesionEnVivoResponse = {
  estado: "en_curso",
  comisionId: "c1",
  cantidadPreguntas: 5,
  tiempoLimitePorPreguntaSegundos: 20,
  preguntaActualIndice: 2,
  opcionesMostradas: false,
  opcionesMostradasEn: null,
  preguntaActualCerrada: false,
  preguntaActual: {
    preguntaId: "p1",
    enunciado: "¿Qué es SOLID?",
    tipo: "opcion_multiple",
    opciones: null,
    respuestaCorrecta: null,
  },
  yaRespondio: null,
  puntajeAcumulado: null,
  totalParticipantes: 5,
  cantidadRespuestas: 0,
  resultadoPregunta: null,
}

const vistaBase: VistaProyeccion = {
  etapa: "pregunta-opciones",
  comisionId: "c1",
  indice: 2,
  cantidadPreguntas: 5,
  enunciado: "¿Qué es SOLID?",
  tipo: "opcion_multiple",
  opciones: ["a", "b"],
  tiempoLimiteSegundos: 20,
  inicioOpcionesMs: 0,
  cantidadRespuestas: 1,
  totalParticipantes: 5,
  resultado: null,
}

describe("calcularVista", () => {
  it("EnEspera no tiene vista (redirige a la sala)", () => {
    expect(calcularVista({ ...estadoBase, estado: "en_espera" })).toBeNull()
  })

  it("sin opciones mostradas es la pregunta sola", () => {
    expect(calcularVista(estadoBase)?.etapa).toBe("pregunta-sola")
  })

  it("con opciones mostradas y sin cerrar es la pregunta con opciones", () => {
    const vista = calcularVista({
      ...estadoBase,
      opcionesMostradas: true,
      opcionesMostradasEn: "2026-09-23T10:00:00Z",
      cantidadRespuestas: 3,
    })
    expect(vista?.etapa).toBe("pregunta-opciones")
    expect(vista?.inicioOpcionesMs).toBe(Date.parse("2026-09-23T10:00:00Z"))
    expect(vista?.cantidadRespuestas).toBe(3)
  })

  it("con la pregunta cerrada es la etapa de resultado, con su resultado", () => {
    const vista = calcularVista({
      ...estadoBase,
      opcionesMostradas: true,
      preguntaActualCerrada: true,
      resultadoPregunta: { distribucion: [{ opcion: "a", cantidad: 2 }], ranking: [] },
    })
    expect(vista?.etapa).toBe("histograma")
    expect(vista?.resultado?.distribucion).toEqual([{ opcion: "a", cantidad: 2 }])
  })

  it("una sesión finalizada es la etapa final", () => {
    expect(calcularVista({ ...estadoBase, estado: "finalizada" })?.etapa).toBe("finalizada")
  })

  it("sin pregunta cargada usa valores vacíos", () => {
    const vista = calcularVista({ ...estadoBase, preguntaActual: null, preguntaActualIndice: null })
    expect(vista?.enunciado).toBe("")
    expect(vista?.indice).toBe(0)
  })
})

describe("aplicarMensaje", () => {
  it("participantes_actualizados cambia el total", () => {
    const vista = aplicarMensaje(
      vistaBase,
      { tipo: "participantes_actualizados", cantidad: 9, participantes: [] },
      0,
    ) as VistaProyeccion
    expect(vista.totalParticipantes).toBe(9)
  })

  it("pregunta_presentada vuelve a la pregunta sola y reinicia el conteo", () => {
    const vista = aplicarMensaje(
      vistaBase,
      {
        tipo: "pregunta_presentada",
        preguntaActualIndice: 3,
        pregunta: { preguntaId: "p2", enunciado: "Otra", tipo: "verdadero_falso" },
      },
      0,
    ) as VistaProyeccion
    expect(vista).toMatchObject({
      etapa: "pregunta-sola",
      indice: 3,
      enunciado: "Otra",
      opciones: null,
      cantidadRespuestas: 0,
    })
  })

  it("opciones_mostradas arranca el temporizador en el instante recibido", () => {
    const vista = aplicarMensaje(
      { ...vistaBase, etapa: "pregunta-sola", opciones: null },
      {
        tipo: "opciones_mostradas",
        preguntaActualIndice: 2,
        opciones: ["x", "y"],
        tiempoLimitePorPreguntaSegundos: 30,
        cantidadRespuestas: 0,
      },
      12345,
    ) as VistaProyeccion
    expect(vista).toMatchObject({
      etapa: "pregunta-opciones",
      opciones: ["x", "y"],
      tiempoLimiteSegundos: 30,
      inicioOpcionesMs: 12345,
    })
  })

  it("opciones_mostradas de otra pregunta pide recalcular", () => {
    expect(
      aplicarMensaje(
        vistaBase,
        {
          tipo: "opciones_mostradas",
          preguntaActualIndice: 9,
          opciones: null,
          tiempoLimitePorPreguntaSegundos: 20,
          cantidadRespuestas: 0,
        },
        0,
      ),
    ).toBe("recalcular")
  })

  it("conteo_respuestas_actualizado actualiza el conteo de la pregunta actual", () => {
    const vista = aplicarMensaje(
      vistaBase,
      { tipo: "conteo_respuestas_actualizado", preguntaActualIndice: 2, cantidadRespuestas: 4 },
      0,
    ) as VistaProyeccion
    expect(vista.cantidadRespuestas).toBe(4)
  })

  it("conteo de otra pregunta se ignora", () => {
    const vista = aplicarMensaje(
      vistaBase,
      { tipo: "conteo_respuestas_actualizado", preguntaActualIndice: 1, cantidadRespuestas: 4 },
      0,
    )
    expect(vista).toBe(vistaBase)
  })

  it("pregunta_cerrada pasa a la etapa de resultado con el resultado", () => {
    const vista = aplicarMensaje(
      vistaBase,
      {
        tipo: "pregunta_cerrada",
        preguntaActualIndice: 2,
        respuestaCorrecta: { contenido: {}, texto: "a", opciones: null },
        distribucion: [{ opcion: "a", cantidad: 3 }],
        ranking: [],
      },
      0,
    ) as VistaProyeccion
    expect(vista.etapa).toBe("histograma")
    expect(vista.resultado?.respuestaCorrecta?.texto).toBe("a")
  })

  it("pregunta_cerrada de otra pregunta pide recalcular", () => {
    expect(
      aplicarMensaje(
        vistaBase,
        {
          tipo: "pregunta_cerrada",
          preguntaActualIndice: 7,
          respuestaCorrecta: { contenido: {}, texto: "a", opciones: null },
          distribucion: [],
          ranking: [],
        },
        0,
      ),
    ).toBe("recalcular")
  })

  it("sesion_finalizada pasa a la etapa final con el ranking", () => {
    const vista = aplicarMensaje(
      vistaBase,
      {
        tipo: "sesion_finalizada",
        ranking: [{ posicion: 1, estudianteId: "e1", nombre: "Ana", puntajeAcumulado: 900 }],
      },
      0,
    ) as VistaProyeccion
    expect(vista.etapa).toBe("finalizada")
    expect(vista.resultado?.ranking).toHaveLength(1)
  })
})

describe("verRanking", () => {
  it("pasa del histograma al ranking", () => {
    expect(verRanking({ ...vistaBase, etapa: "histograma" }).etapa).toBe("ranking")
  })

  it("fuera del histograma no cambia nada", () => {
    expect(verRanking(vistaBase)).toBe(vistaBase)
  })
})

describe("calcularVista — comisión", () => {
  it("conserva la Comisión de la sesión", () => {
    expect(calcularVista(estadoBase)?.comisionId).toBe("c1")
  })
})
