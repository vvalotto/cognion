import { describe, expect, it } from "vitest"

import type { EstadoSesionEnVivoResponse } from "@/lib/sesion-en-vivo-api"
import { vistaEstudiante } from "./_vista-test"
import {
  aplicarMensajeEstudiante,
  calcularVistaEstudiante,
  contenidoRespuesta,
  registrarRespuesta,
  sincronizarVistaEstudiante,
  type VistaEstudiante,
} from "./vista-estudiante"

const pregunta = {
  preguntaId: "p1",
  enunciado: "¿Qué es SOLID?",
  tipo: "opcion_multiple",
  opciones: ["a", "b"],
  respuestaCorrecta: null,
}

const estado = (extra: Partial<EstadoSesionEnVivoResponse> = {}): EstadoSesionEnVivoResponse => ({
  estado: "en_curso",
  comisionId: "c1",
  cantidadPreguntas: 5,
  tiempoLimitePorPreguntaSegundos: 20,
  preguntaActualIndice: 0,
  opcionesMostradas: true,
  opcionesMostradasEn: "2026-09-25T10:00:00Z",
  preguntaActualCerrada: false,
  preguntaActual: pregunta,
  yaRespondio: false,
  puntajeAcumulado: 1200,
  totalParticipantes: 3,
  cantidadRespuestas: 0,
  resultadoPregunta: null,
  ...extra,
})

function comoVista(resultado: VistaEstudiante | "recalcular"): VistaEstudiante {
  if (resultado === "recalcular") throw new Error("esperaba una vista")
  return resultado
}

describe("calcularVistaEstudiante", () => {
  it("EnEspera es la sala", () => {
    expect(calcularVistaEstudiante(estado({ estado: "en_espera", preguntaActual: null })).etapa).toBe("sala")
  })

  it("Finalizada es el final", () => {
    expect(calcularVistaEstudiante(estado({ estado: "finalizada" })).etapa).toBe("finalizada")
  })

  it("sin opciones mostradas es la espera de opciones", () => {
    expect(calcularVistaEstudiante(estado({ opcionesMostradas: false })).etapa).toBe("espera-opciones")
  })

  it("con opciones y sin responder es la pregunta, con la pregunta y el inicio del temporizador", () => {
    const vista = calcularVistaEstudiante(estado())
    expect(vista).toMatchObject({
      etapa: "pregunta",
      preguntaId: "p1",
      opciones: ["a", "b"],
      inicioOpcionesMs: Date.parse("2026-09-25T10:00:00Z"),
      puntajeAcumulado: 1200,
    })
  })

  it("ya respondió es el resultado, sin conocer el acierto de esa pregunta", () => {
    const vista = calcularVistaEstudiante(estado({ yaRespondio: true }))
    expect(vista.etapa).toBe("resultado")
    expect(vista.resultado).toBeNull()
  })

  it("pregunta cerrada sin responder es sin respuesta por cierre", () => {
    const vista = calcularVistaEstudiante(estado({ preguntaActualCerrada: true }))
    expect(vista).toMatchObject({ etapa: "sin-respuesta", motivoSinRespuesta: "cierre" })
  })

  it("tras un rechazo con la pregunta abierta y sin responder es tiempo agotado", () => {
    const vista = calcularVistaEstudiante(estado(), { trasRechazo: true })
    expect(vista).toMatchObject({ etapa: "sin-respuesta", motivoSinRespuesta: "tiempo" })
  })

  it("tras un rechazo que ya estaba respondida es el resultado", () => {
    expect(calcularVistaEstudiante(estado({ yaRespondio: true }), { trasRechazo: true }).etapa).toBe("resultado")
  })

  it("sin pregunta ni acumulado usa valores vacíos", () => {
    const vista = calcularVistaEstudiante(
      estado({ preguntaActual: null, preguntaActualIndice: null, puntajeAcumulado: null, opcionesMostradasEn: null }),
    )
    expect(vista).toMatchObject({ indice: 0, preguntaId: "", puntajeAcumulado: 0 })
  })
})

describe("aplicarMensajeEstudiante", () => {
  it("participantes_actualizados cambia el conteo", () => {
    const vista = comoVista(
      aplicarMensajeEstudiante(vistaEstudiante(), { tipo: "participantes_actualizados", cantidad: 9, participantes: [] }),
    )
    expect(vista.totalParticipantes).toBe(9)
  })

  it("pregunta_presentada pasa a la espera de opciones de la nueva pregunta y limpia el resultado", () => {
    const vista = comoVista(
      aplicarMensajeEstudiante(vistaEstudiante({ etapa: "resultado", resultado: { esCorrecta: true, puntaje: 900 } }), {
        tipo: "pregunta_presentada",
        preguntaActualIndice: 3,
        pregunta: { preguntaId: "p4", enunciado: "Otra", tipo: "verdadero_falso" },
      }),
    )
    expect(vista).toMatchObject({
      etapa: "espera-opciones",
      indice: 3,
      preguntaId: "p4",
      tipo: "verdadero_falso",
      opciones: null,
      resultado: null,
    })
  })

  it("pregunta_presentada no reabre una sesión finalizada", () => {
    const final = vistaEstudiante({ etapa: "finalizada" })
    expect(
      aplicarMensajeEstudiante(final, {
        tipo: "pregunta_presentada",
        preguntaActualIndice: 3,
        pregunta: { preguntaId: "p4", enunciado: "Otra", tipo: "opcion_multiple" },
      }),
    ).toBe(final)
  })

  it("opciones_mostradas muestra las tarjetas y arranca el temporizador en el instante recibido", () => {
    const vista = comoVista(
      aplicarMensajeEstudiante(
        vistaEstudiante({ etapa: "espera-opciones", opciones: null }),
        {
          tipo: "opciones_mostradas",
          preguntaActualIndice: 2,
          opciones: ["x", "y", "z"],
          tiempoLimitePorPreguntaSegundos: 30,
          cantidadRespuestas: 0,
        },
        12345,
      ),
    )
    expect(vista).toMatchObject({ etapa: "pregunta", opciones: ["x", "y", "z"], tiempoLimiteSegundos: 30, inicioOpcionesMs: 12345 })
  })

  it("opciones_mostradas repetido fuera de la espera no cambia nada", () => {
    const resultado = vistaEstudiante({ etapa: "resultado" })
    expect(
      aplicarMensajeEstudiante(resultado, {
        tipo: "opciones_mostradas",
        preguntaActualIndice: 2,
        opciones: null,
        tiempoLimitePorPreguntaSegundos: 20,
        cantidadRespuestas: 0,
      }),
    ).toBe(resultado)
  })

  it("un mensaje de otra pregunta pide recalcular", () => {
    expect(
      aplicarMensajeEstudiante(vistaEstudiante(), {
        tipo: "opciones_mostradas",
        preguntaActualIndice: 7,
        opciones: null,
        tiempoLimitePorPreguntaSegundos: 20,
        cantidadRespuestas: 0,
      }),
    ).toBe("recalcular")
    expect(
      aplicarMensajeEstudiante(vistaEstudiante(), {
        tipo: "pregunta_cerrada",
        preguntaActualIndice: 7,
        respuestaCorrecta: { contenido: {}, texto: "", opciones: null },
        distribucion: [],
        ranking: [],
      }),
    ).toBe("recalcular")
  })

  it("pregunta_cerrada sin haber respondido pasa a sin respuesta, sin exponer correcta ni ranking", () => {
    const vista = comoVista(
      aplicarMensajeEstudiante(vistaEstudiante(), {
        tipo: "pregunta_cerrada",
        preguntaActualIndice: 2,
        respuestaCorrecta: { contenido: { opcion_indice: 1 }, texto: "", opciones: null },
        distribucion: [{ opcion: "1", cantidad: 3 }],
        ranking: [{ posicion: 1, estudianteId: "e1", nombre: "Ana", puntajeAcumulado: 900 }],
      }),
    )
    expect(vista).toMatchObject({ etapa: "sin-respuesta", motivoSinRespuesta: "cierre", ranking: null })
  })

  it("pregunta_cerrada después de responder deja el resultado", () => {
    const resultado = vistaEstudiante({ etapa: "resultado" })
    expect(
      aplicarMensajeEstudiante(resultado, {
        tipo: "pregunta_cerrada",
        preguntaActualIndice: 2,
        respuestaCorrecta: { contenido: {}, texto: "", opciones: null },
        distribucion: [],
        ranking: [],
      }),
    ).toBe(resultado)
  })

  it("sesion_finalizada lleva al final con el ranking", () => {
    const ranking = [{ posicion: 1, estudianteId: "e1", nombre: "Ana", puntajeAcumulado: 900 }]
    const vista = comoVista(aplicarMensajeEstudiante(vistaEstudiante(), { tipo: "sesion_finalizada", ranking }))
    expect(vista).toMatchObject({ etapa: "finalizada", ranking })
  })

  it("los mensajes que el celular no usa se ignoran", () => {
    const vista = vistaEstudiante()
    expect(
      aplicarMensajeEstudiante(vista, { tipo: "conteo_respuestas_actualizado", preguntaActualIndice: 2, cantidadRespuestas: 4 }),
    ).toBe(vista)
  })
})

describe("registrarRespuesta y contenidoRespuesta", () => {
  it("registra el resultado y el acumulado", () => {
    expect(registrarRespuesta(vistaEstudiante(), { esCorrecta: true, puntaje: 1850, puntajeAcumulado: 9270 })).toMatchObject({
      etapa: "resultado",
      resultado: { esCorrecta: true, puntaje: 1850 },
      puntajeAcumulado: 9270,
    })
  })

  it("opción múltiple manda el índice; Verdadero/Falso manda el valor", () => {
    expect(contenidoRespuesta("opcion_multiple", 2)).toEqual({ opcion_indice: 2 })
    expect(contenidoRespuesta("verdadero_falso", 0)).toEqual({ valor: true })
    expect(contenidoRespuesta("verdadero_falso", 1)).toEqual({ valor: false })
  })
})

describe("sincronizarVistaEstudiante (hallazgo #7)", () => {
  it("sin vista previa toma la del servidor", () => {
    const nueva = vistaEstudiante()
    expect(sincronizarVistaEstudiante(null, nueva)).toBe(nueva)
  })

  it("no retrocede del resultado a la pregunta, y conserva el acierto", () => {
    const actual = vistaEstudiante({ etapa: "resultado", resultado: { esCorrecta: true, puntaje: 1850 } })
    const vista = sincronizarVistaEstudiante(actual, vistaEstudiante({ etapa: "pregunta", totalParticipantes: 9 }))
    expect(vista).toMatchObject({ etapa: "resultado", resultado: { esCorrecta: true, puntaje: 1850 }, totalParticipantes: 9 })
  })

  it("no pisa el 'se acabó el tiempo' con la pregunta todavía abierta en el servidor", () => {
    const actual = vistaEstudiante({ etapa: "sin-respuesta", motivoSinRespuesta: "tiempo" })
    expect(sincronizarVistaEstudiante(actual, vistaEstudiante({ etapa: "pregunta" })).etapa).toBe("sin-respuesta")
  })

  it("avanza si el servidor está más adelante en la misma pregunta (opciones perdidas)", () => {
    const actual = vistaEstudiante({ etapa: "espera-opciones", opciones: null })
    const vista = sincronizarVistaEstudiante(actual, vistaEstudiante({ etapa: "pregunta" }))
    expect(vista.etapa).toBe("pregunta")
  })

  it("en la misma etapa manda el servidor (temporizador) sin perder el resultado propio", () => {
    const actual = vistaEstudiante({ etapa: "resultado", resultado: { esCorrecta: false, puntaje: 0 }, inicioOpcionesMs: 1 })
    const vista = sincronizarVistaEstudiante(actual, vistaEstudiante({ etapa: "resultado", resultado: null, inicioOpcionesMs: 500 }))
    expect(vista).toMatchObject({ inicioOpcionesMs: 500, resultado: { esCorrecta: false, puntaje: 0 } })
  })

  it("otra pregunta toma la del servidor", () => {
    const actual = vistaEstudiante({ etapa: "resultado", indice: 1 })
    const nueva = vistaEstudiante({ etapa: "espera-opciones", indice: 2 })
    expect(sincronizarVistaEstudiante(actual, nueva)).toBe(nueva)
  })
})

