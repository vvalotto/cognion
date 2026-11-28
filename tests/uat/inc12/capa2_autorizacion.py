"""UAT Capa 2 — autorización de la sesión en vivo y vencimiento del token (Incremento 12, Iteración 1).

Cubre lo que cambió el comportamiento observable de la `1.0.0`:
  - US-12.1.1: el canal WebSocket solo lo abre quien pertenece a la comisión de la sesión.
  - US-12.1.2: unirse, consultar el estado y ver el ranking exigen pertenecer a la comisión (403 si no).
  - US-12.1.3: el token de sesión dura 8 horas (480 minutos).

Uso:  UAT_URL=http://localhost:8010 UAT_ADMIN_EMAIL=... UAT_ADMIN_PASSWORD=... \
      .venv/bin/python tests/uat/inc12/capa2_autorizacion.py

Crea sus propios datos (dos materias con una comisión cada una, un docente y un estudiante por comisión) y
escribe `quality/reports/uat/inc12/capa2-autorizacion.json` (o `UAT_SALIDA`). Solo para una base descartable.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import sys
import time
import uuid

import httpx
import websockets

URL = os.environ.get("UAT_URL", "http://localhost:8010").rstrip("/")
API = URL + "/api"
WS = URL.replace("http", "ws", 1) + "/api"
ADMIN_EMAIL = os.environ["UAT_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["UAT_ADMIN_PASSWORD"]
SALIDA = os.environ.get("UAT_SALIDA", "quality/reports/uat/inc12/capa2-autorizacion.json")

resultados: list[dict[str, object]] = []


def verificar(nombre: str, ok: bool, detalle: str = "") -> None:
    resultados.append({"verificacion": nombre, "ok": bool(ok), "detalle": detalle})
    print(f"{'OK  ' if ok else 'FALLA'} {nombre} {detalle}")


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def clave() -> str:
    return "Uat#" + uuid.uuid4().hex[:10] + "Zz9"


def vencimiento_minutos(token: str) -> float:
    """Minutos que faltan para el `exp` del JWT recién emitido (no trae `iat`; solo se lee el payload)."""
    cuerpo = token.split(".")[1]
    datos = json.loads(base64.urlsafe_b64decode(cuerpo + "=" * (-len(cuerpo) % 4)))
    return (datos["exp"] - time.time()) / 60


async def conexion_canal(sesion_id: str, token: str | None) -> str:
    """Intenta abrir el canal y devuelve 'abierto' o el código de cierre ('cerrado 1008')."""
    destino = f"{WS}/sesiones-en-vivo/{sesion_id}/canal" + (f"?token={token}" if token else "")
    try:
        async with websockets.connect(destino, open_timeout=10) as ws:
            try:
                await asyncio.wait_for(ws.recv(), timeout=1.0)
            except asyncio.TimeoutError:
                return "abierto"
            return "abierto"
    except websockets.exceptions.ConnectionClosed as exc:
        return f"cerrado {exc.rcvd.code if exc.rcvd else '?'}"
    except websockets.exceptions.InvalidStatus as exc:
        return f"rechazado HTTP {exc.response.status_code}"
    except OSError as exc:
        return f"error {exc}"
    return "abierto"


def rechazado(estado: str) -> bool:
    """El servidor cerró antes de aceptar: el cliente lo ve como un 403 del handshake (o un cierre 1008)."""
    return estado in ("rechazado HTTP 403", "cerrado 1008")


async def main() -> int:
    sufijo = uuid.uuid4().hex[:6]
    async with httpx.AsyncClient(base_url=API, timeout=30) as c:
        r = await c.post("/identidad/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        verificar("login del administrador", r.status_code == 200, str(r.status_code))
        admin = r.json()["access_token"]
        lista = (await c.get("/usuarios", headers=auth(admin), params={"rol": "administrador"})).json()
        admin_id = (lista["cuentas"] if isinstance(lista, dict) else lista)[0]["id"]

        async def comision_con_docente(etiqueta: str) -> dict[str, str]:
            materia = (await c.post("/materias", json={"nombre": f"Materia {etiqueta} {sufijo}"}, headers=auth(admin))).json()
            com = (
                await c.post(
                    "/comisiones",
                    json={"materia_id": materia["id"], "horario": "Lu 8-10", "administrador_id": admin_id},
                    headers=auth(admin),
                )
            ).json()["id"]
            pwd, mail = clave(), f"doc.{etiqueta.lower()}.{sufijo}@fiuner.edu.ar"
            doc = (
                await c.post("/usuarios", json={"nombre": f"Docente {etiqueta}", "email": mail, "password": pwd, "perfil": "docente"}, headers=auth(admin))
            ).json()
            await c.post(f"/comisiones/{com}/docentes", json={"docente_id": doc["id"]}, headers=auth(admin))
            tok = (await c.post("/identidad/login", json={"email": mail, "password": pwd})).json()["access_token"]
            inv = (await c.post(f"/comisiones/{com}/invitaciones-grupales", json={"duracion_minutos": 60}, headers=auth(tok))).json()
            for i in range(3):
                await c.post(
                    "/preguntas/opcion-multiple",
                    json={
                        "banco_id": materia["banco_id"],
                        "texto": f"Pregunta {etiqueta}{i} {sufijo}",
                        "opciones": [{"texto": "A", "es_correcta": True}, {"texto": "B", "es_correcta": False}],
                        "unidad_tematica": "U1",
                        "tema": "T1",
                        "dificultad": "medio",
                        "importancia": "alto",
                    },
                    headers=auth(tok),
                )
            pe, me = clave(), f"est.{etiqueta.lower()}.{sufijo}@fiuner.edu.ar"
            reg = await c.post("/identidad/registro", json={"token": inv["token"], "nombre": f"Estudiante {etiqueta}", "email": me, "password": pe})
            assert reg.status_code == 201, reg.text
            est = (await c.post("/identidad/login", json={"email": me, "password": pe})).json()["access_token"]
            return {"comision": com, "docente": tok, "estudiante": est, "materia": materia["id"]}

        a = await comision_con_docente("A")
        b = await comision_con_docente("B")

        # --- US-12.1.3: el token dura una jornada -------------------------------------------------------
        minutos = vencimiento_minutos(a["docente"])
        esperado = float(os.environ.get("UAT_TOKEN_MINUTOS", "480"))
        verificar(
            f"el token de sesión dura {esperado:.0f} minutos (lo configurado en el servidor)",
            abs(minutos - esperado) < 2,
            f"{minutos:.1f} min",
        )

        # --- La sesión en vivo de la comisión A ---------------------------------------------------------
        sesion = await c.post(
            "/sesiones-en-vivo",
            json={"comision_id": a["comision"], "cantidad_preguntas": 1, "tiempo_limite_por_pregunta_segundos": 60},
            headers=auth(a["docente"]),
        )
        verificar("el docente de A crea la sesión en vivo", sesion.status_code == 201, f"{sesion.status_code} {sesion.text[:120]}")
        sid = sesion.json()["id"]

        # --- US-12.1.2: unirse, consultar el estado y ver el ranking -----------------------------------
        r = await c.post(f"/sesiones-en-vivo/{sid}/unirse", headers=auth(b["estudiante"]))
        verificar("un estudiante de OTRA comisión no puede unirse → 403", r.status_code == 403, str(r.status_code))
        r = await c.get(f"/sesiones-en-vivo/{sid}", headers=auth(b["estudiante"]))
        verificar("un estudiante de otra comisión no consulta el estado → 403", r.status_code == 403, str(r.status_code))
        r = await c.get(f"/sesiones-en-vivo/{sid}/ranking", headers=auth(b["estudiante"]))
        verificar("un estudiante de otra comisión no ve el ranking → 403", r.status_code == 403, str(r.status_code))
        r = await c.get(f"/sesiones-en-vivo/{sid}", headers=auth(b["docente"]))
        verificar("un docente de otra comisión no consulta el estado → 403", r.status_code == 403, str(r.status_code))
        r = await c.get(f"/sesiones-en-vivo/{sid}/ranking", headers=auth(b["docente"]))
        verificar("un docente de otra comisión no ve el ranking → 403", r.status_code == 403, str(r.status_code))
        r = await c.get(f"/sesiones-en-vivo/{sid}/participantes", headers=auth(b["docente"]))
        verificar("un docente de otra comisión no ve los participantes → 403", r.status_code == 403, str(r.status_code))
        r = await c.post(f"/sesiones-en-vivo/{sid}/iniciar", headers=auth(b["docente"]))
        verificar("un docente de otra comisión no conduce la sesión → 403", r.status_code == 403, str(r.status_code))
        r = await c.get(f"/sesiones-en-vivo/{uuid.uuid4()}", headers=auth(a["estudiante"]))
        verificar("una sesión inexistente sigue dando 404", r.status_code == 404, str(r.status_code))
        r = await c.post(f"/sesiones-en-vivo/{sid}/unirse", headers=auth(a["estudiante"]))
        verificar("un estudiante de la comisión SÍ se une → 200", r.status_code == 200, str(r.status_code))
        r = await c.get(f"/sesiones-en-vivo/{sid}", headers=auth(a["estudiante"]))
        verificar("el estudiante de la comisión consulta el estado → 200", r.status_code == 200, str(r.status_code))
        r = await c.get(f"/sesiones-en-vivo/{sid}", headers=auth(a["docente"]))
        verificar("el docente de la comisión consulta el estado → 200", r.status_code == 200, str(r.status_code))
        r = await c.get(f"/sesiones-en-vivo/{sid}/participantes", headers=auth(a["docente"]))
        verificar("el docente de la comisión ve a 1 participante y ningún ajeno", r.status_code == 200 and len(r.json()) == 1, f"{r.status_code} {len(r.json()) if r.status_code == 200 else ''}")

    # --- US-12.1.1: el canal WebSocket --------------------------------------------------------------------
    estado = await conexion_canal(sid, None)
    verificar("canal sin token → rechazada", rechazado(estado), estado)
    estado = await conexion_canal(sid, "token.invalido.xyz")
    verificar("canal con token inválido → rechazada", rechazado(estado), estado)
    estado = await conexion_canal(sid, b["estudiante"])
    verificar("canal con un estudiante de OTRA comisión → rechazada", rechazado(estado), estado)
    estado = await conexion_canal(sid, b["docente"])
    verificar("canal con un docente de OTRA comisión → rechazada", rechazado(estado), estado)
    estado = await conexion_canal(str(uuid.uuid4()), a["estudiante"])
    verificar("canal de una sesión inexistente → rechazada", rechazado(estado), estado)
    estado = await conexion_canal(sid, a["estudiante"])
    verificar("canal con un estudiante de la comisión → abierto", estado == "abierto", estado)
    estado = await conexion_canal(sid, a["docente"])
    verificar("canal con el docente de la comisión → abierto", estado == "abierto", estado)

    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=1)
    fallas = [x for x in resultados if not x["ok"]]
    print(f"\n{len(resultados) - len(fallas)}/{len(resultados)} comprobaciones OK")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
