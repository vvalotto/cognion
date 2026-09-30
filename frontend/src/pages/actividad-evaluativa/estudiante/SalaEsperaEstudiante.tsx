import { Card } from "@/components/ui/card"

/** Sala de espera del Estudiante (`#est-sala-espera`, §3.2): pasa sola a la pregunta, sin botón. */
export function SalaEsperaEstudiante({ totalParticipantes }: { totalParticipantes: number }) {
  return (
    <Card className="mx-auto mt-10 max-w-md p-6 text-center">
      <div className="text-4xl" aria-hidden="true">
        🎮
      </div>
      <h1 className="mt-2 text-lg font-semibold">¡Te uniste!</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Esperando que el docente inicie la sesión — mirá la proyección del aula.
      </p>
      <div className="mt-4 rounded-lg bg-green-50 px-4 py-3 text-sm text-green-800">
        <strong>
          {totalParticipantes} {totalParticipantes === 1 ? "participante" : "participantes"}
        </strong>{" "}
        ya en la sala
      </div>
      <p role="status" className="mt-4 text-sm text-muted-foreground">
        Esperando al docente…
      </p>
    </Card>
  )
}
