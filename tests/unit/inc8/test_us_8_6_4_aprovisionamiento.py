"""Scripts de aprovisionamiento y destrucción de la VM de GCP (US-8.6.4), con `gcloud` simulado.

`gcloud` es un ejecutable falso (`_gcloud_falso.py`) que lleva un estado (qué recursos existen),
registra cada llamada y muta ese estado al "crear" o "borrar". Así se verifican el orden, la
idempotencia y las confirmaciones sin tocar la nube.
"""

import json
from pathlib import Path

import pytest

from tests.unit.inc8._simuladores import (
    buscar_indice,
    correr_script,
    escribir_estado,
    estado_completo,
    estado_con_proyecto,
    leer_llamadas,
    llamadas_que_mutan,
)

# ---------------------------------------------------------------- aprovisionar.sh


def test_sin_gcloud_falla_con_mensaje_claro(tmp_path: Path) -> None:
    """Escenario 7: sin gcloud sale con código ≠ 0, sin traza."""
    escribir_estado(tmp_path)
    r = correr_script(tmp_path, "aprovisionar.sh", "--si", con_gcloud=False)
    assert r.returncode != 0
    assert "Falta gcloud" in r.stderr
    assert "Traceback" not in r.stderr


@pytest.mark.parametrize("falta", ["PROYECTO", "CUENTA_FACTURACION"])
def test_exige_proyecto_y_cuenta_de_facturacion(tmp_path: Path, falta: str) -> None:
    """Sin el proyecto o la cuenta de facturación no hace nada."""
    escribir_estado(tmp_path)
    r = correr_script(tmp_path, "aprovisionar.sh", "--si", extra={falta: ""})
    assert r.returncode != 0
    assert f"Falta {falta}" in r.stderr
    assert llamadas_que_mutan(leer_llamadas(tmp_path)) == []


def test_rechaza_un_identificador_de_proyecto_invalido(tmp_path: Path) -> None:
    """Mayúsculas o espacios no son un ID de proyecto válido."""
    escribir_estado(tmp_path)
    r = correr_script(tmp_path, "aprovisionar.sh", "--si", extra={"PROYECTO": "Proyecto Raro"})
    assert r.returncode != 0
    assert "PROYECTO inválido" in r.stderr


def test_sin_sesion_de_gcloud_falla(tmp_path: Path) -> None:
    """Sin sesión activa pide `gcloud auth login`."""
    escribir_estado(tmp_path, cuenta="")
    r = correr_script(tmp_path, "aprovisionar.sh", "--si")
    assert r.returncode != 0
    assert "gcloud auth login" in r.stderr


def test_sobre_un_proyecto_vacio_crea_todo_en_orden(tmp_path: Path) -> None:
    """Escenario 1: crea lo que falta, en el orden que funcionó en la prueba manual."""
    escribir_estado(tmp_path, proyecto=False, facturacion=False)
    r = correr_script(tmp_path, "aprovisionar.sh", "--si")
    assert r.returncode == 0, r.stderr
    ll = leer_llamadas(tmp_path)
    orden = [
        "projects create cognion-prueba-2410",
        "billing projects link cognion-prueba-2410",
        "services enable",
        "billing budgets create",
        "firewall-rules create cognion-web",
        "instances create cognion-vm",
        "compute ssh cognion-vm",
    ]
    posiciones = [buscar_indice(ll, x) for x in orden]
    assert posiciones == sorted(posiciones)
    assert buscar_indice(ll, "addresses create cognion-ip") < buscar_indice(
        ll, "instances create cognion-vm"
    )
    assert "34.30.252.89" in r.stdout


def test_la_regla_de_firewall_solo_abre_80_y_443(tmp_path: Path) -> None:
    """Escenario 2: ningún otro puerto, y solo hacia la etiqueta de la VM."""
    escribir_estado(tmp_path)
    correr_script(tmp_path, "aprovisionar.sh", "--si")
    regla = next(x for x in leer_llamadas(tmp_path) if "firewall-rules create cognion-web" in x)
    assert "--rules=tcp:80,tcp:443" in regla
    assert "--target-tags=cognion-web" in regla
    assert (
        "tcp:22" not in regla
        and "tcp:5432" not in regla
        and "all" not in regla.split("--rules=")[1].split()[0]
    )


def test_la_vm_usa_la_ip_reservada_y_la_capa_gratuita(tmp_path: Path) -> None:
    """La IP queda asignada a la VM (sin asignar se cobra) y el tipo es el de la capa gratuita."""
    escribir_estado(tmp_path)
    correr_script(tmp_path, "aprovisionar.sh", "--si")
    vm = next(x for x in leer_llamadas(tmp_path) if "instances create cognion-vm" in x)
    for esperado in (
        "--address=cognion-ip",
        "--machine-type=e2-micro",
        "--zone=us-central1-a",
        "--boot-disk-size=30GB",
        "--boot-disk-type=pd-standard",
        "--image-family=debian-12",
        "--tags=cognion-web",
    ):
        assert esperado in vm


def test_el_presupuesto_es_de_5_usd_con_alertas_al_50_y_100(tmp_path: Path) -> None:
    """El presupuesto queda acotado al proyecto por su número."""
    escribir_estado(tmp_path)
    correr_script(tmp_path, "aprovisionar.sh", "--si")
    pres = next(x for x in leer_llamadas(tmp_path) if "billing budgets create" in x)
    assert "--budget-amount=5USD" in pres
    assert "--filter-projects=projects/888211184158" in pres
    assert "--threshold-rule=percent=0.5" in pres and "--threshold-rule=percent=1.0" in pres


def test_cierra_el_rdp_abierto_a_internet(tmp_path: Path) -> None:
    """Elimina `default-allow-rdp` si el proyecto ya existía con esa regla."""
    estado_con_proyecto(tmp_path)
    correr_script(tmp_path, "aprovisionar.sh", "--si")
    assert any("firewall-rules delete default-allow-rdp" in x for x in leer_llamadas(tmp_path))


def test_en_un_proyecto_nuevo_cierra_el_rdp_que_crea_google_al_habilitar_compute(
    tmp_path: Path,
) -> None:
    """Regresión: default-allow-rdp nace con Compute Engine y se cierra en la misma corrida."""
    escribir_estado(
        tmp_path, proyecto=False, facturacion=False, reglas=[], rdp_al_habilitar_compute=True
    )
    r = correr_script(tmp_path, "aprovisionar.sh", "--si")
    assert r.returncode == 0, r.stderr
    ll = leer_llamadas(tmp_path)
    assert buscar_indice(ll, "services enable") < buscar_indice(
        ll, "firewall-rules delete default-allow-rdp"
    )
    datos = json.loads((tmp_path / "estado.json").read_text())
    assert "default-allow-rdp" not in datos["reglas"]
    (tmp_path / "llamadas.log").unlink()
    assert "Nada que crear" in correr_script(tmp_path, "aprovisionar.sh", "--si").stdout


def test_todos_los_comandos_llevan_project_y_no_cambian_la_configuracion_activa(
    tmp_path: Path,
) -> None:
    """No toca `gcloud config` ni activa configuraciones: la terminal queda como estaba."""
    escribir_estado(tmp_path)
    correr_script(tmp_path, "aprovisionar.sh", "--si")
    ll = leer_llamadas(tmp_path)
    assert not any(" config " in x or "configurations" in x for x in ll)
    for x in ll:
        if "compute " in x and " ssh " not in x:
            assert "--project=cognion-prueba-2410" in x, x


def test_es_idempotente_la_segunda_corrida_no_crea_nada(tmp_path: Path) -> None:
    """Escenario: ejecutarlo dos veces no duplica recursos."""
    escribir_estado(tmp_path)
    assert correr_script(tmp_path, "aprovisionar.sh", "--si").returncode == 0
    (tmp_path / "llamadas.log").unlink()
    r = correr_script(tmp_path, "aprovisionar.sh", "--si")
    assert r.returncode == 0
    assert "Nada que crear" in r.stdout
    assert llamadas_que_mutan(leer_llamadas(tmp_path)) == []


def test_solo_crea_lo_que_falta(tmp_path: Path) -> None:
    """Con todo creado salvo la regla de firewall, solo crea esa regla."""
    estado_completo(tmp_path)
    datos = json.loads((tmp_path / "estado.json").read_text())
    datos["reglas"] = ["default-allow-ssh", "default-allow-icmp"]
    (tmp_path / "estado.json").write_text(json.dumps(datos))
    r = correr_script(tmp_path, "aprovisionar.sh", "--si")
    assert r.returncode == 0
    mutaciones = llamadas_que_mutan(leer_llamadas(tmp_path))
    assert len(mutaciones) == 1 and "firewall-rules create cognion-web" in mutaciones[0]


def test_si_no_puede_consultar_los_presupuestos_no_crea_un_duplicado(tmp_path: Path) -> None:
    """Regresión: un error de la consulta no se toma por 'no existe' (duplicaba el presupuesto)."""
    estado_completo(tmp_path)
    r = correr_script(tmp_path, "aprovisionar.sh", "--si", extra={"FAKE_PRESUPUESTOS_FALLA": "1"})
    assert r.returncode != 0
    assert "No pude consultar los presupuestos" in r.stderr
    assert not any("budgets create" in x for x in leer_llamadas(tmp_path))


def test_los_comandos_de_presupuestos_indican_el_proyecto_de_cuota(tmp_path: Path) -> None:
    """No dependen de la configuración activa de gcloud: llevan `--billing-project`."""
    escribir_estado(tmp_path)
    correr_script(tmp_path, "aprovisionar.sh", "--si")
    presupuestos = [x for x in leer_llamadas(tmp_path) if "billing budgets" in x]
    assert presupuestos and all("--billing-project=cognion-prueba-2410" in x for x in presupuestos)


def test_sin_confirmacion_no_crea_nada(tmp_path: Path) -> None:
    """Sin `--si`, cualquier respuesta distinta de SI cancela."""
    escribir_estado(tmp_path)
    r = correr_script(tmp_path, "aprovisionar.sh", entrada="no\n")
    assert r.returncode != 0
    assert "Cancelado" in r.stderr
    assert llamadas_que_mutan(leer_llamadas(tmp_path)) == []


def test_con_confirmacion_escrita_crea(tmp_path: Path) -> None:
    """Escribir SI confirma el plan y se muestra qué se va a hacer."""
    escribir_estado(tmp_path)
    r = correr_script(tmp_path, "aprovisionar.sh", entrada="SI\n")
    assert r.returncode == 0, r.stderr
    assert "crear la VM cognion-vm" in r.stdout
    assert any("instances create" in x for x in leer_llamadas(tmp_path))


def test_advierte_del_costo_antes_de_crear(tmp_path: Path) -> None:
    """El plan avisa que la IPv4 pública en uso se cobra."""
    escribir_estado(tmp_path)
    r = correr_script(tmp_path, "aprovisionar.sh", entrada="no\n")
    assert "IPv4" in r.stdout


# ---------------------------------------------------------------- destruir.sh


def test_destruir_borra_solo_vm_regla_e_ip_por_nombre(tmp_path: Path) -> None:
    """Escenario 3: la VM primero, y ni el proyecto ni nada más."""
    estado_completo(tmp_path)
    r = correr_script(tmp_path, "destruir.sh", "--si")
    assert r.returncode == 0, r.stderr
    ll = leer_llamadas(tmp_path)
    borrados = [x for x in ll if " delete " in x]
    assert [x.split(" delete ")[0].split()[-1] for x in borrados] == [
        "instances",
        "firewall-rules",
        "addresses",
    ]
    assert "instances delete cognion-vm" in borrados[0]
    assert not any("projects delete" in x for x in ll)
    assert not any("default-allow" in x and " delete " in x for x in ll)
    assert not any("budgets" in x and " delete" in x for x in ll)


def test_destruir_el_proyecto_exige_escribir_su_id(tmp_path: Path) -> None:
    """Con `--proyecto` y el ID correcto borra el proyecto; con otro ID no borra nada."""
    estado_completo(tmp_path)
    mal = correr_script(tmp_path, "destruir.sh", "--si", "--proyecto", entrada="otro-proyecto\n")
    assert mal.returncode != 0
    assert "no coincide" in mal.stderr
    assert not any("projects delete" in x for x in leer_llamadas(tmp_path))
    assert not any(" delete " in x for x in leer_llamadas(tmp_path))
    bien = correr_script(
        tmp_path, "destruir.sh", "--si", "--proyecto", entrada="cognion-prueba-2410\n"
    )
    assert bien.returncode == 0, bien.stderr
    assert any("projects delete cognion-prueba-2410" in x for x in leer_llamadas(tmp_path))
    assert "projects undelete" in bien.stdout


def test_destruir_sin_confirmacion_no_borra_nada(tmp_path: Path) -> None:
    """Sin `--si`, solo SI confirma."""
    estado_completo(tmp_path)
    r = correr_script(tmp_path, "destruir.sh", entrada="quizas\n")
    assert r.returncode != 0
    assert not any(" delete " in x for x in leer_llamadas(tmp_path))


def test_destruir_sin_recursos_no_falla(tmp_path: Path) -> None:
    """Si ya no existe nada, lo dice y sale bien sin borrar."""
    escribir_estado(tmp_path, proyecto=True, reglas=[])
    r = correr_script(tmp_path, "destruir.sh", "--si")
    assert r.returncode == 0
    assert "Nada que borrar" in r.stdout
    assert not any(" delete " in x for x in leer_llamadas(tmp_path))


def test_destruir_sin_gcloud_falla_sin_traza(tmp_path: Path) -> None:
    """Error claro cuando falta gcloud."""
    escribir_estado(tmp_path)
    r = correr_script(tmp_path, "destruir.sh", "--si", con_gcloud=False)
    assert r.returncode != 0 and "Falta gcloud" in r.stderr and "Traceback" not in r.stderr
