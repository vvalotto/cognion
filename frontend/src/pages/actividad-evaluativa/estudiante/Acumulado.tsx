/** "Llevás acumulados: X pts" + recordatorio de que el ranking se ve al final (§3.4, H4/H5). */
export function Acumulado({ puntaje }: { puntaje: number }) {
  return (
    <>
      <p className="mt-3 text-sm">
        <span className="text-muted-foreground">Llevás acumulados</span>{" "}
        <strong className="text-[22px] text-primary">{puntaje} pts</strong>
      </p>
      <p className="mt-4 text-xs text-muted-foreground">
        Esperando la próxima pregunta — el ranking se ve recién al final de la sesión.
      </p>
    </>
  )
}
