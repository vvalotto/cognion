import { Link, useSearchParams } from "react-router"

import { Button } from "@/components/ui/button"
import type { MotivoInvitacion } from "@/lib/invitacion-motivos"

interface TextosMotivo {
  titulo: string
  subtitulo: string
  alertaTitulo: string
  alertaTexto: string
}

const PEDIR_NUEVO = "Pedile a tu docente que te genere un link nuevo para la comisión."

const TEXTOS: Record<MotivoInvitacion, TextosMotivo> = {
  vencida: {
    titulo: "Este link venció",
    subtitulo: "El docente lo generó con una duración limitada y ya terminó.",
    alertaTitulo: "Invitación vencida",
    alertaTexto: PEDIR_NUEVO,
  },
  revocada: {
    titulo: "Este link fue desactivado",
    subtitulo: "Tu docente lo desactivó y ya no se puede usar.",
    alertaTitulo: "Invitación desactivada",
    alertaTexto: PEDIR_NUEVO,
  },
  usada: {
    titulo: "Este link ya fue utilizado",
    subtitulo: "Es una invitación individual que ya se usó para registrar una cuenta.",
    alertaTitulo: "Invitación ya utilizada",
    alertaTexto: "Si ya te registraste, iniciá sesión. Si no, pedile un link nuevo a tu docente.",
  },
  invalida: {
    titulo: "Este link no es correcto",
    subtitulo: "No encontramos una invitación con este link.",
    alertaTitulo: "Invitación no válida",
    alertaTexto: "Revisá que hayas copiado el link completo o pedile uno nuevo a tu docente.",
  },
}

function motivoDeLaUrl(valor: string | null): MotivoInvitacion {
  return valor !== null && valor in TEXTOS ? (valor as MotivoInvitacion) : "invalida"
}

/**
 * Pantalla de link de invitación que no sirve (§2.4 `wireframes-identidad.md`).
 *
 * Desde `US-ADJ-67` distingue el motivo (`?motivo=vencida|revocada|usada|invalida`), porque con el link
 * grupal cambia lo que el estudiante debe hacer; sin motivo reconocible muestra "no es correcto".
 */
export function RegistroError() {
  const [searchParams] = useSearchParams()
  const textos = TEXTOS[motivoDeLaUrl(searchParams.get("motivo"))]

  return (
    <div className="text-center">
      <p className="mb-2 text-4xl" aria-hidden="true">
        ⏱
      </p>
      <h1 className="text-lg font-semibold">{textos.titulo}</h1>
      <p className="mt-2 text-sm text-muted-foreground">{textos.subtitulo}</p>

      <div
        role="alert"
        className="mt-4 flex gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-left text-sm text-destructive"
      >
        <span aria-hidden="true">⚠</span>
        <div>
          <p className="font-medium">{textos.alertaTitulo}</p>
          <p>{textos.alertaTexto}</p>
        </div>
      </div>

      <Button render={<Link to="/login" />} variant="outline" className="mt-4 w-full">
        Ir a iniciar sesión
      </Button>
    </div>
  )
}
