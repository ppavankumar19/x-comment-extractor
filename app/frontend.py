from __future__ import annotations

from functools import lru_cache
from pathlib import Path


CSS_LINK = '<link rel="stylesheet" href="/static/style.css" />'
JS_SCRIPT = '<script src="/static/app.js" defer></script>'


@lru_cache(maxsize=1)
def render_frontend(frontend_dir: Path) -> str:
    index_html = (frontend_dir / "index.html").read_text(encoding="utf-8")
    style_css = (frontend_dir / "style.css").read_text(encoding="utf-8")
    app_js = (frontend_dir / "app.js").read_text(encoding="utf-8")

    missing_markers: list[str] = []
    if CSS_LINK not in index_html:
        missing_markers.append(CSS_LINK)
    if JS_SCRIPT not in index_html:
        missing_markers.append(JS_SCRIPT)
    if missing_markers:
        raise ValueError(
            "frontend/index.html is missing the expected asset markers: "
            + ", ".join(missing_markers)
        )

    bundled_html = index_html.replace(CSS_LINK, f"<style>\n{style_css}\n</style>", 1)
    bundled_html = bundled_html.replace(JS_SCRIPT, f"<script>\n{app_js}\n</script>", 1)
    return bundled_html
