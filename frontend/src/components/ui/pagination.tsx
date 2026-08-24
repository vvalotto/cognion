import { Button } from "@/components/ui/button"

export interface PaginationProps {
  pagina: number
  totalPaginas: number
  onCambiarPagina: (pagina: number) => void
}

/** Controles de paginación: números de página + Anterior/Siguiente (US-ADJ-03). */
export function Pagination({ pagina, totalPaginas, onCambiarPagina }: PaginationProps) {
  if (totalPaginas <= 1) return null

  const paginas = Array.from({ length: totalPaginas }, (_, i) => i + 1)

  return (
    <nav aria-label="Paginación" className="mt-4 flex items-center justify-center gap-1">
      <Button
        type="button"
        variant="outline"
        size="sm"
        disabled={pagina <= 1}
        onClick={() => onCambiarPagina(pagina - 1)}
      >
        Anterior
      </Button>
      {paginas.map((numero) => (
        <Button
          key={numero}
          type="button"
          variant={numero === pagina ? "default" : "outline"}
          size="sm"
          aria-current={numero === pagina ? "page" : undefined}
          onClick={() => onCambiarPagina(numero)}
        >
          {numero}
        </Button>
      ))}
      <Button
        type="button"
        variant="outline"
        size="sm"
        disabled={pagina >= totalPaginas}
        onClick={() => onCambiarPagina(pagina + 1)}
      >
        Siguiente
      </Button>
    </nav>
  )
}
