"""Prueba de envío de email real con la misma ruta de código que usa la aplicación (`ADR-023`).

Lee las variables SMTP de `.env.smtp` (ignorado por git, ver `.env.smtp.example`) o del entorno,
verifica la conexión paso a paso (red, STARTTLS, login) y envía un email de prueba con
`src.shared.frameworks.smtp.enviar_email`. No imprime nunca la contraseña.

    .venv/bin/python scripts/probar_smtp.py destinatario@ejemplo.com
    .venv/bin/python scripts/probar_smtp.py destinatario@ejemplo.com --archivo otro.env
"""

from __future__ import annotations

import argparse
import asyncio
import os
import smtplib
import socket
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CLAVES_SMTP = ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM")


def cargar_archivo(ruta: Path) -> None:
    """Carga `CLAVE=valor` en `os.environ` sin pisar lo que ya esté definido en el entorno."""
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        os.environ.setdefault(clave.strip(), valor.strip().strip("\"'"))


def preparar_entorno(archivo: Path) -> None:
    """Carga el archivo SMTP y completa los valores obligatorios que esta prueba no usa."""
    if archivo.exists():
        cargar_archivo(archivo)
    elif not os.environ.get("SMTP_HOST"):
        sys.exit(f"No existe {archivo} ni hay SMTP_HOST en el entorno. Copiá .env.smtp.example.")
    # Gmail muestra la contraseña de aplicación en grupos de 4 separados por espacios.
    os.environ["SMTP_PASSWORD"] = os.environ.get("SMTP_PASSWORD", "").replace(" ", "")
    # Estos dos son requeridos por `Settings` pero no intervienen en el envío.
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://prueba:prueba@db.invalido/prueba")
    os.environ.setdefault("SECRET_KEY", "x" * 40)
    os.environ["ENTORNO"] = "desarrollo"
    os.environ["EMAIL_MODO"] = "smtp"


def diagnosticar(host: str, port: int, user: str) -> bool:
    """Prueba red y STARTTLS por separado para dar un mensaje útil si algo falla."""
    print(f"1. Conexión TCP a {host}:{port} ...", end=" ", flush=True)
    try:
        with socket.create_connection((host, port), timeout=10):
            pass
    except OSError as error:
        print(f"FALLÓ ({error}).")
        print("   Revisá SMTP_HOST/SMTP_PORT, el firewall o si la red bloquea ese puerto.")
        return False
    print("ok")
    print("2. STARTTLS ...", end=" ", flush=True)
    try:
        with smtplib.SMTP(host, port, timeout=15) as servidor:
            servidor.ehlo()
            if not servidor.has_extn("starttls"):
                print("el servidor no ofrece STARTTLS.")
                return False
            servidor.starttls()
    except (OSError, smtplib.SMTPException) as error:
        print(f"FALLÓ ({error}).")
        print("   El código solo soporta STARTTLS (puerto 587), no SSL directo (465).")
        return False
    print("ok")
    print(f"3. Login como {user or '(sin usuario)'} se verifica en el envío.")
    return True


async def enviar(destinatario: str) -> bool:
    """Envía el email de prueba por la misma función que usa la aplicación."""
    from src.shared.frameworks.smtp import enviar_email

    try:
        await enviar_email(
            None,
            destinatario,
            "Cognión — prueba de envío",
            "Este es un email de prueba de Cognión.\n\nSi lo recibís, la cuenta SMTP funciona.",
        )
    except (smtplib.SMTPAuthenticationError, smtplib.SMTPServerDisconnected):
        # Gmail corta la conexión tras rechazar las credenciales (535), y smtplib lo informa así.
        print("FALLÓ la autenticación (el servidor rechazó el usuario/contraseña).")
        print("   Con Gmail hace falta una contraseña de aplicación, no la clave de la cuenta,")
        print("   y la verificación en 2 pasos activada: https://myaccount.google.com/apppasswords")
        return False
    except (OSError, smtplib.SMTPException) as error:
        print(f"FALLÓ el envío: {type(error).__name__}: {error}")
        return False
    return True


def main() -> int:
    """Punto de entrada: devuelve 0 si el email salió."""
    parser = argparse.ArgumentParser(description="Prueba de envío SMTP de Cognión.")
    parser.add_argument("destinatario", help="Email al que se envía la prueba.")
    parser.add_argument("--archivo", type=Path, default=RAIZ / ".env.smtp")
    args = parser.parse_args()

    preparar_entorno(args.archivo)
    faltan = [k for k in CLAVES_SMTP if not os.environ.get(k)]
    if faltan:
        print(f"Faltan variables: {', '.join(faltan)}")
        return 2
    sys.path.insert(0, str(RAIZ))
    host, port, user = (
        os.environ["SMTP_HOST"],
        int(os.environ["SMTP_PORT"]),
        os.environ["SMTP_USER"],
    )
    print(f"Remitente: {os.environ['SMTP_FROM']}  ·  Destinatario: {args.destinatario}")
    if not diagnosticar(host, port, user):
        return 1
    print("4. Envío ...", end=" ", flush=True)
    if not asyncio.run(enviar(args.destinatario)):
        return 1
    print("ok. Revisá la bandeja (y spam) de", args.destinatario)
    return 0


if __name__ == "__main__":
    sys.exit(main())
