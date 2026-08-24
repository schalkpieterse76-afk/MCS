"""CVOR Map View using PyQt6 WebEngine + folium."""
import tempfile
import os
from typing import List

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtCore import QUrl
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False


STATUS_COLOURS = {
    "ACTIVE": "#28a745",
    "INACTIVE": "#6c757d",
    "FAULT": "#dc3545",
    "STANDBY": "#fd7e14",
    "MAINTENANCE": "#0d6efd",
}


def build_map_html(bases: List) -> str:
    """Build folium map HTML for given bases."""
    try:
        import folium
    except ImportError:
        return "<html><body><p>folium not installed</p></body></html>"

    m = folium.Map(location=[-29, 25], zoom_start=6, tiles="CartoDB positron")

    for base in bases:
        for cvor in base.cvor_systems:
            colour = STATUS_COLOURS.get(cvor.status, "#6c757d")
            popup_html = (
                f"<b>{cvor.system_id}</b><br>"
                f"Status: {cvor.status}<br>"
                f"Freq: {cvor.frequency_mhz} MHz<br>"
                f"Base: {base.name}"
            )
            folium.CircleMarker(
                location=[base.latitude, base.longitude],
                radius=10,
                color=colour,
                fill=True,
                fill_color=colour,
                fill_opacity=0.8,
                popup=folium.Popup(popup_html, max_width=200),
                tooltip=f"{base.code}: {cvor.status}",
            ).add_to(m)

            if cvor.status == "ACTIVE":
                folium.CircleMarker(
                    location=[base.latitude, base.longitude],
                    radius=16,
                    color=colour,
                    fill=False,
                    weight=2,
                    opacity=0.5,
                ).add_to(m)

    # Legend
    legend_html = """
    <div style="position:fixed;bottom:30px;right:30px;z-index:9999;background:white;
    padding:10px;border:1px solid #ccc;border-radius:5px;font-size:12px;">
    <b>CVOR Status</b><br>
    <span style="color:#28a745">&#9679;</span> ACTIVE<br>
    <span style="color:#6c757d">&#9679;</span> INACTIVE<br>
    <span style="color:#dc3545">&#9679;</span> FAULT<br>
    <span style="color:#fd7e14">&#9679;</span> STANDBY<br>
    <span style="color:#0d6efd">&#9679;</span> MAINTENANCE
    </div>"""
    m.get_root().html.add_child(folium.Element(legend_html))

    # Title banner
    title_html = """
    <div style="position:fixed;top:10px;left:50%;transform:translateX(-50%);z-index:9999;
    background:#0a2158;color:white;padding:8px 20px;border-radius:5px;font-size:14px;font-weight:bold;">
    SAAF CVOR Network — Remote Management System
    </div>"""
    m.get_root().html.add_child(folium.Element(title_html))

    return m._repr_html_()


if HAS_WEBENGINE:
    class CVORMapView(QWebEngineView):
        def __init__(self, parent=None):
            super().__init__(parent)
            self._tmp_file = None

        def refresh_map(self, bases: List) -> None:
            html = build_map_html(bases)
            # Write to temp file for proper resource loading
            if self._tmp_file and os.path.exists(self._tmp_file):
                os.unlink(self._tmp_file)
            fd, path = tempfile.mkstemp(suffix=".html")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(html)
            self._tmp_file = path
            self.load(QUrl.fromLocalFile(path))

        def closeEvent(self, event):
            if self._tmp_file and os.path.exists(self._tmp_file):
                os.unlink(self._tmp_file)
            super().closeEvent(event)
else:
    from PyQt6.QtWidgets import QLabel

    class CVORMapView(QLabel):  # type: ignore[no-redef]
        def __init__(self, parent=None):
            super().__init__("Map view requires PyQt6-WebEngine", parent)

        def refresh_map(self, bases):
            pass
