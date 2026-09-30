import { Link, useNavigate } from "react-router"

import { Card } from "@/components/ui/card"

interface PerfilOpcion {
  icono: string
  titulo: string
  descripcion: string
  to: string
}

const PERFILES: PerfilOpcion[] = [
  {
    icono: "🧑‍🏫",
    titulo: "Soy Docente",
    descripcion: "Voy a crear materias y evaluar",
    to: "/autoregistro/docente",
  },
  {
    icono: "🎓",
    titulo: "Soy Estudiante",
    descripcion: "Voy a rendir evaluaciones",
    to: "/autoregistro/estudiante",
  },
]

/**
 * Pantalla de elección de perfil para autoregistro (`#autoregistro-perfil`,
 * `wireframes-identidad-autoservicio.md` §5.1) — sin tercera opción de Administrador
 * (INV-ID-15).
 */
export function AutoregistroPerfil() {
  const navigate = useNavigate()

  return (
    <div>
      <h1 className="text-lg font-semibold">Creá tu cuenta</h1>
      <p className="mb-4 text-sm text-muted-foreground">¿Cómo vas a usar Cognión?</p>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {PERFILES.map((perfil) => (
          <Card
            key={perfil.to}
            role="button"
            tabIndex={0}
            className="cursor-pointer p-5 text-center transition-colors hover:border-primary"
            onClick={() => navigate(perfil.to)}
            onKeyDown={(event) => {
              if (event.key === "Enter") navigate(perfil.to)
            }}
          >
            <p className="mb-2 text-2xl">{perfil.icono}</p>
            <p className="font-semibold">{perfil.titulo}</p>
            <p className="mt-1 text-xs text-muted-foreground">{perfil.descripcion}</p>
          </Card>
        ))}
      </div>

      <p className="mt-4 text-center text-sm text-muted-foreground">
        ¿Ya tenés cuenta?{" "}
        <Link to="/login" className="font-medium text-foreground underline-offset-2 hover:underline">
          Iniciar sesión
        </Link>
      </p>
    </div>
  )
}
