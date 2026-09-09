import type { ComponentProps } from "react"

import { cn } from "@/lib/utils"

/** Tabla con estilo moderno (borde suave, header tintado, filas con hover) — reemplaza los
 * `<table>` a mano repetidos en Cuentas/Materias/Comisiones/Banco. */
function Table({ className, ...props }: ComponentProps<"table">) {
  return <table className={cn("w-full text-left text-sm", className)} {...props} />
}

function TableHeader({ className, ...props }: ComponentProps<"thead">) {
  return (
    <thead
      className={cn(
        "border-b border-border bg-[color-mix(in_oklch,var(--secondary),var(--primary)_4%)]",
        className,
      )}
      {...props}
    />
  )
}

function TableHeaderCell({ className, ...props }: ComponentProps<"th">) {
  return (
    <th
      className={cn(
        "py-2.5 pr-4 pl-4 text-[11px] font-bold tracking-wide text-muted-foreground uppercase",
        className,
      )}
      {...props}
    />
  )
}

function TableBody({ className, ...props }: ComponentProps<"tbody">) {
  return <tbody className={cn("divide-y divide-border", className)} {...props} />
}

function TableRow({ className, ...props }: ComponentProps<"tr">) {
  return <tr className={cn("transition-colors hover:bg-accent/8", className)} {...props} />
}

function TableCell({ className, ...props }: ComponentProps<"td">) {
  return <td className={cn("py-3.5 pr-4 pl-4", className)} {...props} />
}

function TableEmptyRow({ colSpan, children }: { colSpan: number; children: React.ReactNode }) {
  return (
    <tr>
      <td colSpan={colSpan} className="py-6 pl-4 text-center text-muted-foreground">
        {children}
      </td>
    </tr>
  )
}

export { Table, TableBody, TableCell, TableEmptyRow, TableHeader, TableHeaderCell, TableRow }
