from pathlib import Path

import pytest

from app.frontend import render_frontend


def test_render_frontend_bundles_assets() -> None:
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    bundled_html = render_frontend(frontend_dir)

    assert '<style>' in bundled_html
    assert '<script>' in bundled_html
    assert '/static/style.css' not in bundled_html
    assert '/static/app.js' not in bundled_html


def test_render_frontend_requires_known_asset_markers(tmp_path: Path) -> None:
    frontend_dir = tmp_path / "frontend"
    frontend_dir.mkdir()
    (frontend_dir / "index.html").write_text("<html><body><main>broken</main></body></html>", encoding="utf-8")
    (frontend_dir / "style.css").write_text("body { color: black; }", encoding="utf-8")
    (frontend_dir / "app.js").write_text("console.log('ok');", encoding="utf-8")

    with pytest.raises(ValueError, match="missing the expected asset markers"):
        render_frontend(frontend_dir)
