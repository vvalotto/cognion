"""UAT Capa 2 (HTTP) de la v0.10.0 contra un servidor real (US-10.1.1, `PROCEDIMIENTO-UAT.md` §3).

Ejercita sobre un servidor levantado con una base descartable: salud y readiness, link de invitación grupal
(generar, preview, registrar varios estudiantes, contador, revocar), motivos de error del registro, aviso del
último intento del login y que el log de acceso no contenga el token de la invitación.

Uso:  UAT_URL=http://localhost:8010 UAT_ADMIN_EMAIL=... UAT_ADMIN_PASSWORD=... UAT_LOG=logs/uat10/uvicorn-*.log \
      .venv/bin/python tests/uat/inc10/capa2_http.py
La evidencia queda en `quality/reports/uat/inc10/capa2-http.json` (sin tokens ni contraseñas).
"""

from __future__ import annotations

import glob
import json
import os
import secrets
import sys
import time

import httpx

URL = os.environ.get("UAT_URL", "http://localhost:8010").rstrip("/") + "/api"
ADMIN_EMAIL = os.environ["UAT_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["UAT_ADMIN_PASSWORD"]
LOG = os.environ.get("UAT_LOG", "")
SALIDA = "quality/reports/uat/inc10/capa2-http.json"

resultados: list[dict] = []
sufijo = secrets.token_hex(3)


def clave() -> str:
    """Contraseña de prueba válida (12+, mayúscula, número y símbolo)."""
    return f"Uat{secrets.token_hex(5)}!Aa1"


def verificar(nombre: str, ok: bool, detalle: str = "") -> None:
    """Registra un resultado y lo imprime."""
    resultados.append({"verificacion": nombre, "ok": bool(ok), "detalle": detalle})
    print(("✅" if ok else "❌"), nombre, f"— {detalle}" if detalle else "")


def auth(token: str) -> dict[str, str]:
    """Header de autorización."""
    return {"Authorization": f"Bearer {token}"}


def main() -> int:
    """Corre el recorrido y devuelve 0 si todo pasó."""
    c = httpx.Client(base_url=URL, timeout=20)

    r = c.get("/health")
    verificar(
        "GET /health", r.status_code == 200 and r.json().get("status") == "ok", str(r.status_code)
    )
    r = c.get("/health/ready")
    verificar(
        "GET /health/ready (base disponible)",
        r.status_code == 200 and r.json().get("base_de_datos") == "ok",
        str(r.status_code),
    )

    r = c.post("/identidad/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    verificar("login del administrador", r.status_code == 200, str(r.status_code))
    admin = r.json()["access_token"]
    admin_id = httpx.get(
        f"{URL}/usuarios", headers=auth(admin), params={"rol": "administrador"}
    ).json()
    admin_id = (admin_id["cuentas"] if isinstance(admin_id, dict) else admin_id)[0]["id"]

    materia = c.post(
        "/materias", json={"nombre": f"Materia UAT {sufijo}"}, headers=auth(admin)
    ).json()["id"]
    comision = c.post(
        "/comisiones",
        json={"materia_id": materia, "horario": "Lu 10-12", "administrador_id": admin_id},
        headers=auth(admin),
    ).json()["id"]
    pwd_doc = clave()
    docente = c.post(
        "/usuarios",
        json={
            "nombre": "Docente UAT",
            "email": f"doc.{sufijo}@fiuner.edu.ar",
            "password": pwd_doc,
            "perfil": "docente",
        },
        headers=auth(admin),
    )
    verificar(
        "el administrador crea un docente", docente.status_code == 201, str(docente.status_code)
    )
    docente_id = docente.json()["id"]
    r = c.post(
        f"/comisiones/{comision}/docentes", json={"docente_id": docente_id}, headers=auth(admin)
    )
    verificar(
        "asignar el docente a la comisión", r.status_code in (200, 201, 204), str(r.status_code)
    )
    r = c.post(
        "/identidad/login", json={"email": f"doc.{sufijo}@fiuner.edu.ar", "password": pwd_doc}
    )
    doc = r.json()["access_token"]

    # --- Link de invitación grupal -------------------------------------------------------------
    r = c.post(
        f"/comisiones/{comision}/invitaciones-grupales",
        json={"duracion_minutos": 60},
        headers=auth(doc),
    )
    verificar("el docente genera el link grupal (60 min)", r.status_code == 201, str(r.status_code))
    inv = r.json()
    token, inv_id = inv["token"], inv["id"]
    r = c.post(
        f"/comisiones/{comision}/invitaciones-grupales",
        json={"duracion_minutos": 7},
        headers=auth(doc),
    )
    verificar(
        "duración fuera de 15/60/1440 se rechaza", r.status_code in (400, 422), str(r.status_code)
    )
    r = c.post(f"/comisiones/{comision}/invitaciones-grupales", json={}, headers=auth(admin))
    verificar("el administrador NO genera links grupales", r.status_code == 403, str(r.status_code))

    r = c.get(f"/identidad/invitaciones/{token}")
    verificar(
        "preview del link (materia y horario)",
        r.status_code == 200 and "materia" in r.json(),
        str(r.status_code),
    )

    emails = []
    for i in range(3):
        mail = f"est{i}.{sufijo}@fiuner.edu.ar"
        r = c.post(
            "/identidad/registro",
            json={"token": token, "nombre": f"Estudiante {i}", "email": mail, "password": clave()},
        )
        emails.append(mail)
        verificar(
            f"registro #{i + 1} con el MISMO link grupal", r.status_code == 201, str(r.status_code)
        )
    r = c.get(f"/comisiones/{comision}/invitaciones-grupales/ultima", headers=auth(doc)).json()
    verificar(
        "contador de registrados = 3",
        r.get("usos") == 3 and r.get("estado") == "vigente",
        f"usos={r.get('usos')}",
    )
    r = c.get(f"/comisiones/{comision}/estudiantes", headers=auth(doc))
    verificar(
        "la comisión lista a los 3 estudiantes",
        r.status_code == 200 and len(r.json()) == 3,
        str(r.status_code),
    )

    # --- Motivos de error del registro ---------------------------------------------------------
    r = c.post(
        "/identidad/registro",
        json={"token": token, "nombre": "Dup", "email": emails[0], "password": clave()},
    )
    verificar("email repetido se rechaza", r.status_code in (409, 422), str(r.status_code))
    r = c.post(
        "/identidad/registro",
        json={
            "token": token,
            "nombre": "Corta",
            "email": f"corta.{sufijo}@fiuner.edu.ar",
            "password": "corta",
        },
    )
    verificar(
        "contraseña de menos de 8 caracteres → 422 de validación (no 5xx)",
        r.status_code == 422,
        str(r.status_code),
    )
    r = c.post(
        "/identidad/registro",
        json={
            "token": token,
            "nombre": "Floja",
            "email": f"floja.{sufijo}@fiuner.edu.ar",
            "password": "sinmayuscula1",
        },
    )
    detalle = r.json().get("detail")
    codigo = detalle.get("codigo") if isinstance(detalle, dict) else None
    verificar(
        "contraseña de 8+ sin complejidad → codigo password_invalida",
        r.status_code == 422 and codigo == "password_invalida",
        f"{r.status_code} {codigo}",
    )
    r = c.get(f"/comisiones/{comision}/invitaciones-grupales/ultima", headers=auth(doc)).json()
    verificar("un registro rechazado NO suma uso", r.get("usos") == 3, f"usos={r.get('usos')}")

    # --- Revocar --------------------------------------------------------------------------------
    r = c.post(f"/comisiones/{comision}/invitaciones-grupales/{inv_id}/revocar", headers=auth(doc))
    verificar("el docente desactiva el link", r.status_code in (200, 204), str(r.status_code))
    r = c.post(
        "/identidad/registro",
        json={
            "token": token,
            "nombre": "Tarde",
            "email": f"tarde.{sufijo}@fiuner.edu.ar",
            "password": clave(),
        },
    )
    detalle = r.json().get("detail")
    codigo = detalle.get("codigo") if isinstance(detalle, dict) else None
    verificar(
        "registro con link desactivado → invitacion_revocada",
        codigo == "invitacion_revocada",
        f"{r.status_code} {codigo}",
    )
    r = c.post(
        f"/comisiones/{comision}/invitaciones-grupales",
        json={"duracion_minutos": 15},
        headers=auth(doc),
    )
    nuevo = r.json()
    verificar(
        "generar otro link revoca al anterior y emite uno nuevo",
        r.status_code == 201 and nuevo["token"] != token,
        str(r.status_code),
    )

    # --- Aviso del último intento ---------------------------------------------------------------
    mail = emails[1]
    avisos = []
    for n in range(1, 4):
        r = c.post(
            "/identidad/login",
            json={"email": mail, "password": "incorrecta-" + secrets.token_hex(2)},
        )
        d = r.json().get("detail")
        avisos.append((r.status_code, d.get("intentos_restantes") if isinstance(d, dict) else None))
    verificar("1.er fallo sin aviso", avisos[0] == (401, None), str(avisos[0]))
    verificar("2.º fallo avisa intentos_restantes = 1", avisos[1] == (401, 1), str(avisos[1]))
    verificar("3.er fallo sin aviso (bloquea)", avisos[2] == (401, None), str(avisos[2]))
    r = c.post("/identidad/login", json={"email": mail, "password": "otra-" + secrets.token_hex(2)})
    verificar("4.º intento: cuenta bloqueada (403)", r.status_code == 403, str(r.status_code))

    # --- El log no muestra el token -------------------------------------------------------------
    time.sleep(1)
    archivos = sorted(glob.glob(LOG)) if LOG else []
    if archivos:
        texto = open(archivos[-1], encoding="utf-8", errors="replace").read()
        verificar(
            "el log de acceso NO contiene el token de la invitación",
            token not in texto and nuevo["token"] not in texto,
        )
        verificar(
            "el log muestra la ruta enmascarada /invitaciones/***", "/invitaciones/***" in texto
        )
    else:
        verificar("log disponible para revisar", False, "definí UAT_LOG")

    fallos = [x for x in resultados if not x["ok"]]
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(
            {"url": URL, "total": len(resultados), "fallos": len(fallos), "resultados": resultados},
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"\n{len(resultados) - len(fallos)}/{len(resultados)} verificaciones OK")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
