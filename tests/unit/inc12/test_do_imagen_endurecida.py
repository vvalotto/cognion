"""Imagen y composición endurecidas (`DO-01`, `DO-04`, Issue #646)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[3]
DOCKERFILE = (RAIZ / "Dockerfile").read_text(encoding="utf-8")
COMPOSE = yaml.safe_load((RAIZ / "deploy/servidor/docker-compose.yml").read_text(encoding="utf-8"))


class TestDockerfile:
    def test_la_aplicacion_no_corre_como_root(self) -> None:
        assert re.search(r"^USER cognion$", DOCKERFILE, re.MULTILINE)

    def test_uv_tiene_version_fija(self) -> None:
        assert re.search(r"pip install .*uv==\d+\.\d+\.\d+", DOCKERFILE)

    @pytest.mark.parametrize("linea", re.findall(r"^FROM (\S+)", DOCKERFILE, re.MULTILINE))
    def test_las_imagenes_base_fijan_la_version_de_parche(self, linea: str) -> None:
        assert re.search(r":\d+\.\d+\.\d+", linea), linea

    def test_no_confia_en_cabeceras_de_cualquier_origen(self) -> None:
        assert '"*"' not in DOCKERFILE
        assert "--forwarded-allow-ips" not in DOCKERFILE


class TestComposicion:
    def test_la_aplicacion_confia_solo_en_la_red_interna(self) -> None:
        entorno = COMPOSE["services"]["app"]["environment"]
        assert entorno["FORWARDED_ALLOW_IPS"] == "${COGNION_SUBNET:-172.29.77.0/24}"
        subred = COMPOSE["networks"]["default"]["ipam"]["config"][0]["subnet"]
        assert subred == "${COGNION_SUBNET:-172.29.77.0/24}"

    def test_el_healthcheck_de_la_aplicacion_mira_la_base(self) -> None:
        prueba = " ".join(COMPOSE["services"]["app"]["healthcheck"]["test"])
        assert "/api/health/ready" in prueba

    @pytest.mark.parametrize("servicio", ["db", "caddy"])
    def test_las_imagenes_de_terceros_fijan_la_version_de_parche_o_menor(
        self, servicio: str
    ) -> None:
        assert re.search(r":\d+\.\d+(\.\d+)?$", COMPOSE["services"][servicio]["image"])
