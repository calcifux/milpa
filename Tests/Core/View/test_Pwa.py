"""Tests de los helpers PWA (Core/View/Pwa.py) — sin BD, sin npm: el build se
materializa en tmp_path (mismo patrón que test_Vite: settings via monkeypatch).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from starlette.requests import Request

from milpa.Core.Config import settings
from milpa.Core.Errors import ResourceNotFoundError
from milpa.Core.View import Pwa


def _request(root_path: str = "") -> Request:
    return Request(scope={"type": "http", "root_path": root_path, "headers": []})


def _setup_dist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, icons: tuple[str, ...] = ()) -> Path:
    """Un build mínimo en modo explícito (VITE_DIST_DIR) con manifest e iconos."""
    dist = tmp_path / "dist"
    (dist / ".vite").mkdir(parents=True)
    (dist / ".vite" / "manifest.json").write_text("{}", encoding="utf-8")
    if icons:
        (dist / "icons").mkdir()
        for name in icons:
            (dist / "icons" / name).write_bytes(b"\x89PNG\r\n\x1a\nfake")
    monkeypatch.setattr(settings, "vite_dist_dir", str(dist))
    return dist


def test_webmanifest_arma_start_url_y_scope_con_el_prefijo_del_deploy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup_dist(tmp_path, monkeypatch)

    response = Pwa.webmanifest(
        _request("/nombre-reverse"), prefix="/spa", theme_color="#FF6B1A", background_color="#0A0A0A"
    )

    assert response.media_type == "application/manifest+json"
    manifest = json.loads(bytes(response.body).decode("utf-8"))
    assert manifest["start_url"] == "/nombre-reverse/spa"
    assert manifest["scope"] == "/nombre-reverse/spa/"  # start_url ⊂ scope (MDN)
    assert manifest["theme_color"] == "#FF6B1A"


def test_webmanifest_descubre_iconos_por_convencion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _setup_dist(
        tmp_path,
        monkeypatch,
        icons=("icon-192.png", "icon-512.png", "icon-512-maskable.png", "apple-touch-icon.png"),
    )

    manifest = json.loads(
        bytes(Pwa.webmanifest(_request(), prefix="/spa", theme_color="#fff", background_color="#000").body).decode(
            "utf-8"
        )
    )

    icons = manifest["icons"]
    assert [icon["sizes"] for icon in icons] == ["192x192", "512x512", "512x512"]  # apple-touch NO va al manifest
    assert icons[0]["src"] == "/vite/icons/icon-192.png"  # vite_asset: hereda ASSET_URL/namespacing
    assert icons[-1]["purpose"] == "maskable"  # los maskable van al final, con purpose
    assert "purpose" not in icons[0]


def test_webmanifest_extra_sobrescribe(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _setup_dist(tmp_path, monkeypatch)

    manifest = json.loads(
        bytes(
            Pwa.webmanifest(
                _request(),
                prefix="/spa",
                theme_color="#fff",
                background_color="#000",
                extra={"orientation": "portrait", "display": "fullscreen"},
            ).body
        ).decode("utf-8")
    )

    assert manifest["orientation"] == "portrait"
    assert manifest["display"] == "fullscreen"  # extra GANA al default


def test_service_worker_sirve_con_no_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dist = _setup_dist(tmp_path, monkeypatch)
    (dist / "sw.js").write_text("// sw", encoding="utf-8")

    response = Pwa.service_worker()

    assert response.headers["cache-control"] == "no-cache"  # un SW cacheado = updates que nunca llegan
    assert response.media_type == "text/javascript"


def test_service_worker_sin_build_truena_con_instruccion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _setup_dist(tmp_path, monkeypatch)  # dist sin sw.js

    with pytest.raises(ResourceNotFoundError, match="npm run build"):
        Pwa.service_worker()
