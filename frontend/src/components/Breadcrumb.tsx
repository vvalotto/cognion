import { Link } from "react-router"

export interface BreadcrumbItem {
  label: string
  to?: string
}

/** Ruta de navegación en cabecera de pantalla (§ prototipo `banco-preguntas-carga-filtrado.html`). */
export function Breadcrumb({ items }: { items: BreadcrumbItem[] }) {
  return (
    <p className="mb-1.5 text-xs text-muted-foreground">
      {items.map((item, index) => {
        const esUltimo = index === items.length - 1
        return (
          <span key={`${item.label}-${index}`}>
            {index > 0 && <span className="mx-1.5">›</span>}
            {item.to && !esUltimo ? (
              <Link to={item.to} className="hover:text-foreground">
                {item.label}
              </Link>
            ) : (
              <span className={esUltimo ? "font-medium text-foreground" : undefined}>
                {item.label}
              </span>
            )}
          </span>
        )
      })}
    </p>
  )
}
