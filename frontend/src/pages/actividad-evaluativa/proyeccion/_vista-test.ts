import type { VistaProyeccion } from "./vista-proyeccion"

/** Vista base para los tests de las etapas de resultado. */
export function vistaResultado(extra: Partial<VistaProyeccion> = {}): VistaProyeccion {
  return {
    etapa: "histograma",
    comisionId: "c1",
    indice: 1,
    cantidadPreguntas: 5,
    enunciado: "¿Qué es SOLID?",
    tipo: "opcion_multiple",
    opciones: ["Liskov", "DIP", "ISP", "SRP"],
    tiempoLimiteSegundos: 20,
    inicioOpcionesMs: 0,
    cantidadRespuestas: 4,
    totalParticipantes: 6,
    resultado: {
      respuestaCorrecta: {
        contenido: { opcion_indice: 1 },
        texto: "¿Qué es SOLID?",
        opciones: ["Liskov", "DIP", "ISP", "SRP"],
      },
      distribucion: [
        { opcion: "0", cantidad: 1 },
        { opcion: "1", cantidad: 3 },
      ],
      ranking: [6, 5, 4, 3, 2, 1].map((n) => ({
        posicion: 7 - n,
        estudianteId: `e${7 - n}`,
        nombre: `Estudiante ${7 - n}`,
        puntajeAcumulado: n * 1000,
      })),
    },
    ...extra,
  }
}
