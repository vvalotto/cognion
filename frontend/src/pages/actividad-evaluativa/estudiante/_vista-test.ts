import type { VistaEstudiante } from "./vista-estudiante"

/** Vista base para los tests de las etapas del Estudiante. */
export function vistaEstudiante(extra: Partial<VistaEstudiante> = {}): VistaEstudiante {
  return {
    etapa: "pregunta",
    totalParticipantes: 5,
    indice: 2,
    cantidadPreguntas: 10,
    preguntaId: "p3",
    enunciado: "¿Qué principio de SOLID viola depender de una clase concreta?",
    tipo: "opcion_multiple",
    opciones: ["Liskov", "Inversión de dependencias", "Segregación", "Responsabilidad única"],
    tiempoLimiteSegundos: 20,
    inicioOpcionesMs: Date.now(),
    puntajeAcumulado: 7420,
    resultado: null,
    motivoSinRespuesta: "cierre",
    ranking: null,
    ...extra,
  }
}
