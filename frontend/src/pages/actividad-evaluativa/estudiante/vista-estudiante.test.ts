import { describe, expect, it } from "vitest"

import type { EstadoSesionEnVivoResponse } from "@/lib/sesion-en-vivo-api"
import {
  aplicarMensajeEstudiante,
  calcularVistaEstudiante,
  type VistaEstudiante,
} from "./vista-estudiante"

const estado = (extra: Partial<EstadoSesionEnVivoResponse> = {}): EstadoSesionEnVivoResponse => ({
  estado: "en_espera",
  comisionId: "c1",
  cantidadPreguntas: 5,
  tiempoLimitePorPreguntaSegundos: 20,
  preguntaActualIndice: null,
  opcionesMostradas: false,
  opcionesMostradasEn: null,
  preguntaActualCerrada: false,
  preguntaActual: null,
  yaRespondio: false,
  puntajeAcumulado: 0,
  totalParticipantes: 3,
  cantidadRespuestas: 0,
  resultadoPregunta: null,
  ...extra,
})

const sala: VistaEstudiante = { etapa: "sala", totalParticipantes: 3 }

describe("calcularVistaEstudiante", () => {
  it("EnEspera es la sala, con el conteo de participantes", () => {
    expect(calcularVistaEstudiante(estado())).toEqual({ etapa: "sala", totalParticipantes: 3 })
  })

  it("EnCurso es la pregunta (unión tardía)", () => {
    expect(calcularVistaEstudiante(estado({ estado: "en_curso" })).etapa).toBe("pregunta")
  })

  it("Finalizada es el final", () => {
    expect(calcularVistaEstudiante(estado({ estado: "finalizada" })).etapa).toBe("finalizada")
  })
})

describe("aplicarMensajeEstudiante", () => {
  it("participantes_actualizados cambia el conteo", () => {
    expect(
      aplicarMensajeEstudiante(sala, { tipo: "participantes_actualizados", cantidad: 7, participantes: [] })
        .totalParticipantes,
    ).toBe(7)
  })

  it("pregunta_presentada saca de la sala", () => {
    const vista = aplicarMensajeEstudiante(sala, {
      tipo: "pregunta_presentada",
      preguntaActualIndice: 0,
      pregunta: { preguntaId: "p1", enunciado: "¿?", tipo: "opcion_multiple" },
    })
    expect(vista.etapa).toBe("pregunta")
  })

  it("pregunta_presentada no reabre una sesión finalizada", () => {
    const final: VistaEstudiante = { etapa: "finalizada", totalParticipantes: 3 }
    expect(
      aplicarMensajeEstudiante(final, {
        tipo: "pregunta_presentada",
        preguntaActualIndice: 1,
        pregunta: { preguntaId: "p2", enunciado: "¿?", tipo: "opcion_multiple" },
      }),
    ).toBe(final)
  })

  it("sesion_finalizada lleva al final", () => {
    expect(aplicarMensajeEstudiante(sala, { tipo: "sesion_finalizada", ranking: [] }).etapa).toBe(
      "finalizada",
    )
  })

  it("los mensajes que esta etapa no usa se ignoran", () => {
    expect(
      aplicarMensajeEstudiante(sala, {
        tipo: "conteo_respuestas_actualizado",
        preguntaActualIndice: 0,
        cantidadRespuestas: 2,
      }),
    ).toBe(sala)
  })
})
