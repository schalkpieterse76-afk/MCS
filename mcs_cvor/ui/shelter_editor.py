"""Interactive shelter floor-plan editor for CVOR systems."""
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from PyQt6.QtCore import (
    Qt, QPointF, QRectF, pyqtSignal
)
from PyQt6.QtGui import (
    QBrush, QColor, QPen, QFont, QPainter
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QGraphicsView,
    QGraphicsScene, QGraphicsRectItem, QGraphicsItem,
    QListWidget, QListWidgetItem, QFormLayout, QLineEdit,
    QComboBox, QTextEdit, QPushButton, QLabel, QMenu,
    QGroupBox, QSplitter, QFileDialog,
    QMessageBox, QInputDialog
)
try:
    from PyQt6.QtPrintSupport import QPdfWriter, QPageSize
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

try:
    from PyQt6.QtSvg import QSvgGenerator
    HAS_SVG = True
except ImportError:
    HAS_SVG = False


RACK_COLOURS = {
    "OK": ("#1a6b2e", "#c8f0d0"),
    "FAULT": ("#991100", "#ffe0dc"),
    "WARN": ("#996600", "#fff3cc"),
    "MAINTENANCE": ("#004499", "#cce0ff"),
    "INACTIVE": ("#555555", "#e8e8e8"),
}

SNAP_GRID = 20

PALETTE_ITEMS = [
    ("CVOR Transmitter", "rack"),
    ("Modulator Unit", "rack"),
    ("Power Amplifier", "rack"),
    ("Antenna Coupler", "rack"),
    ("Monitor Receiver", "rack"),
    ("Control Unit", "rack"),
    ("PSU Main", "psu"),
    ("PSU Backup", "psu"),
    ("Alarm Panel", "panel"),
    ("UPS Unit", "ups"),
    ("Ethernet Switch", "network"),
    ("Serial Converter", "network"),
    ("Remote Control Unit", "rack"),
    ("Patch Panel", "panel"),
    ("Custom Equipment", "rack"),
]


def _snap(value: float) -> float:
    return round(value / SNAP_GRID) * SNAP_GRID


class RackItem(QGraphicsRectItem):
    def __init__(self, item_data: Dict[str, Any], rect: QRectF = None, parent=None):
        if rect is None:
            rect = QRectF(0, 0, 120, 60)
        super().__init__(rect, parent)
        self.item_data = dict(item_data)
        self._hover = False
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            scene = self.scene()
            if scene and getattr(scene, "_snap_enabled", True):
                return QPointF(_snap(value.x()), _snap(value.y()))
        return super().itemChange(change, value)

    def paint(self, painter: QPainter, option, widget=None):
        status = self.item_data.get("status", "OK")
        fg_hex, bg_hex = RACK_COLOURS.get(status, RACK_COLOURS["OK"])
        fg = QColor(fg_hex)
        bg = QColor(bg_hex)

        rect = self.rect()

        # Background
        painter.setBrush(QBrush(bg))
        if self._hover:
            painter.setPen(QPen(fg, 2))
        else:
            painter.setPen(QPen(fg, 1))
        painter.drawRect(rect)

        # Selection glow
        if self.isSelected():
            pen = QPen(QColor("#0066ff"), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect.adjusted(-3, -3, 3, 3))

        # Status LED top-right
        led_r = 8
        led_x = rect.right() - led_r - 4
        led_y = rect.top() + 4
        painter.setBrush(QBrush(fg))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(led_x, led_y + led_r / 2), led_r / 2, led_r / 2)

        # Name label centred
        painter.setPen(QPen(fg))
        font = QFont("Arial", 8, QFont.Weight.Bold)
        painter.setFont(font)
        name = self.item_data.get("name", "?")
        painter.drawText(rect.adjusted(4, 4, -16, -16), Qt.AlignmentFlag.AlignCenter, name)

        # Rack label bottom-right
        rack = self.item_data.get("rack", "")
        slot = self.item_data.get("slot", "")
        if rack or slot:
            small_font = QFont("Arial", 7)
            painter.setFont(small_font)
            painter.setPen(QPen(fg.darker(120)))
            lbl = f"{rack}/{slot}" if slot else rack
            painter.drawText(
                rect.adjusted(2, 0, -4, -2),
                Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight,
                lbl,
            )

    def hoverEnterEvent(self, event):
        self._hover = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._hover = False
        self.update()
        super().hoverLeaveEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu()
        edit_act = menu.addAction("Edit Properties")
        rotate_act = menu.addAction("Rotate 90°")
        resize_menu = menu.addMenu("Resize")
        wider = resize_menu.addAction("Wider (+20px)")
        narrower = resize_menu.addAction("Narrower (-20px)")
        taller = resize_menu.addAction("Taller (+20px)")
        shorter = resize_menu.addAction("Shorter (-20px)")
        menu.addSeparator()
        del_act = menu.addAction("Delete")

        action = menu.exec(event.screenPos())
        rect = self.rect()
        if action == rotate_act:
            cx = rect.center().x()
            cy = rect.center().y()
            self.setTransformOriginPoint(cx, cy)
            self.setRotation((self.rotation() + 90) % 360)
        elif action == wider:
            self.setRect(QRectF(rect.x(), rect.y(), max(40, rect.width() + 20), rect.height()))
        elif action == narrower:
            self.setRect(QRectF(rect.x(), rect.y(), max(40, rect.width() - 20), rect.height()))
        elif action == taller:
            self.setRect(QRectF(rect.x(), rect.y(), rect.width(), max(40, rect.height() + 20)))
        elif action == shorter:
            self.setRect(QRectF(rect.x(), rect.y(), rect.width(), max(40, rect.height() - 20)))
        elif action == del_act:
            scene = self.scene()
            if scene:
                scene.removeItem(self)
        elif action == edit_act:
            scene = self.scene()
            if scene and hasattr(scene, "request_edit"):
                scene.request_edit.emit(self)

    def to_dict(self) -> Dict[str, Any]:
        pos = self.scenePos()
        return {
            **self.item_data,
            "x": pos.x(),
            "y": pos.y(),
            "width": self.rect().width(),
            "height": self.rect().height(),
            "rotation": self.rotation(),
        }


class ShelterScene(QGraphicsScene):
    request_edit = pyqtSignal(object)
    selection_changed_item = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(0, 0, 800, 600)
        self._snap_enabled = True
        self._grid_visible = True
        self.selectionChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self):
        items = self.selectedItems()
        if items and isinstance(items[0], RackItem):
            self.selection_changed_item.emit(items[0])
        else:
            self.selection_changed_item.emit(None)

    def drawBackground(self, painter: QPainter, rect: QRectF):
        super().drawBackground(painter, rect)
        painter.fillRect(rect, QColor("#f0f0f0"))
        if self._grid_visible:
            pen = QPen(QColor("#cccccc"), 1)
            painter.setPen(pen)
            left = int(rect.left()) - (int(rect.left()) % SNAP_GRID)
            top = int(rect.top()) - (int(rect.top()) % SNAP_GRID)
            x = left
            while x < rect.right():
                y = top
                while y < rect.bottom():
                    painter.drawPoint(int(x), int(y))
                    y += SNAP_GRID
                x += SNAP_GRID

    def _draw_shelter_outline(self, width: float = 700, height: float = 500):
        from PyQt6.QtWidgets import QGraphicsTextItem
        pen = QPen(QColor("#2c3e50"), 4)
        # Outer walls
        wall = self.addRect(QRectF(50, 50, width, height), pen, QBrush(Qt.BrushStyle.NoBrush))
        wall.setZValue(-1)
        # Door gap (bottom wall)
        door_pen = QPen(QColor("#f0f0f0"), 6)
        self.addLine(50 + width / 2 - 25, 50 + height, 50 + width / 2 + 25, 50 + height, door_pen).setZValue(0)
        # Door arc
        arc_pen = QPen(QColor("#2c3e50"), 2, Qt.PenStyle.DashLine)
        arc_item = self.addEllipse(
            QRectF(50 + width / 2 - 30, 50 + height - 30, 60, 60), arc_pen
        )
        arc_item.setZValue(0)
        # Shelter label
        lbl = QGraphicsTextItem("CVOR SHELTER")
        lbl.setDefaultTextColor(QColor("#2c3e50"))
        lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        lbl.setPos(50 + width / 2 - 50, 55)
        lbl.setZValue(0)
        self.addItem(lbl)

    def load_from_list(self, equipment_list: List[Dict]):
        self.clear()
        self._draw_shelter_outline()
        rack_groups: Dict[str, List] = {}
        for eq in equipment_list:
            rack = eq.get("rack", "A")
            rack_groups.setdefault(rack, []).append(eq)

        x_start, y_start = 80, 100
        col_width = 140
        col = 0
        for rack_name in sorted(rack_groups.keys()):
            y = y_start
            for eq in rack_groups[rack_name]:
                stored_x = eq.get("x")
                stored_y = eq.get("y")
                item = RackItem(eq, QRectF(0, 0, eq.get("width", 120), eq.get("height", 60)))
                if stored_x is not None and stored_y is not None:
                    item.setPos(stored_x, stored_y)
                else:
                    item.setPos(x_start + col * col_width, y)
                    y += 80
                if eq.get("rotation"):
                    item.setRotation(eq["rotation"])
                self.addItem(item)
            col += 1

    def to_layout_json(self) -> str:
        data = [item.to_dict() for item in self.items() if isinstance(item, RackItem)]
        return json.dumps(data, indent=2)


class RackPropertiesPanel(QWidget):
    apply_requested = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_item: Optional[RackItem] = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        group = QGroupBox("Equipment Properties")
        form = QFormLayout(group)

        self.name_edit = QLineEdit()
        self.rack_edit = QLineEdit()
        self.slot_edit = QLineEdit()
        self.status_combo = QComboBox()
        self.status_combo.addItems(list(RACK_COLOURS.keys()))
        self.icon_edit = QLineEdit()
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)

        form.addRow("Name:", self.name_edit)
        form.addRow("Rack:", self.rack_edit)
        form.addRow("Slot:", self.slot_edit)
        form.addRow("Status:", self.status_combo)
        form.addRow("Icon:", self.icon_edit)
        form.addRow("Notes:", self.notes_edit)

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self._apply)
        form.addRow(self.apply_btn)

        layout.addWidget(group)
        layout.addStretch()

    def load_item(self, item: Optional[RackItem]):
        self._current_item = item
        if item is None:
            self.name_edit.clear()
            self.rack_edit.clear()
            self.slot_edit.clear()
            self.status_combo.setCurrentIndex(0)
            self.icon_edit.clear()
            self.notes_edit.clear()
            return
        d = item.item_data
        self.name_edit.setText(d.get("name", ""))
        self.rack_edit.setText(d.get("rack", ""))
        self.slot_edit.setText(d.get("slot", ""))
        idx = self.status_combo.findText(d.get("status", "OK"))
        self.status_combo.setCurrentIndex(max(0, idx))
        self.icon_edit.setText(d.get("icon", ""))
        self.notes_edit.setPlainText(d.get("notes", ""))

    def _apply(self):
        if self._current_item is None:
            return
        self._current_item.item_data.update({
            "name": self.name_edit.text(),
            "rack": self.rack_edit.text(),
            "slot": self.slot_edit.text(),
            "status": self.status_combo.currentText(),
            "icon": self.icon_edit.text(),
            "notes": self.notes_edit.toPlainText(),
        })
        self._current_item.update()
        self.apply_requested.emit(self._current_item.item_data)


class EquipmentPalette(QWidget):
    add_equipment = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Equipment Palette</b>"))
        self.list_widget = QListWidget()
        for name, icon in PALETTE_ITEMS:
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, {"name": name, "icon": icon, "status": "OK"})
            self.list_widget.addItem(item)
        self.list_widget.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.list_widget)
        add_btn = QPushButton("Add to Layout")
        add_btn.clicked.connect(self._on_add)
        layout.addWidget(add_btn)

    def _on_double_click(self, item: QListWidgetItem):
        self.add_equipment.emit(dict(item.data(Qt.ItemDataRole.UserRole)))

    def _on_add(self):
        item = self.list_widget.currentItem()
        if item:
            self.add_equipment.emit(dict(item.data(Qt.ItemDataRole.UserRole)))


class ShelterPDFExporter:
    def __init__(self, scene: ShelterScene, cvor=None):
        self.scene = scene
        self.cvor = cvor

    def export_pdf(self, filepath: str) -> bool:
        if not HAS_PDF:
            return False
        writer = QPdfWriter(filepath)
        writer.setPageSize(QPageSize(QPageSize.PageSizeId.A3))
        orientation = QPageSize.Orientation.Landscape if hasattr(QPageSize, "Orientation") else 1
        writer.setPageOrientation(orientation)  # type: ignore
        writer.setResolution(150)
        painter = QPainter(writer)

        page_rect = writer.pageLayout().paintRectPixels(writer.resolution())
        pw = page_rect.width()
        ph = page_rect.height()

        # Title block
        painter.fillRect(0, 0, pw, 60, QColor("#0a2158"))
        painter.setPen(QColor("white"))
        title_font = QFont("Arial", 14, QFont.Weight.Bold)
        painter.setFont(title_font)
        sys_id = self.cvor.system_id if self.cvor else "UNKNOWN"
        base = self.cvor.base.name if self.cvor and self.cvor.base else "—"
        freq = str(self.cvor.frequency_mhz) if self.cvor else "—"
        painter.drawText(10, 5, pw - 20, 55, Qt.AlignmentFlag.AlignVCenter,
                         f"SAAF CVOR Remote Management System  |  {sys_id}  |  {base}  |  {freq} MHz")

        # Classification bar
        painter.fillRect(0, ph - 30, pw, 30, QColor("#cc0000"))
        painter.setPen(QColor("white"))
        cls_font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(cls_font)
        painter.drawText(0, ph - 30, pw, 30, Qt.AlignmentFlag.AlignCenter,
                         "UNCLASSIFIED — FOR OFFICIAL USE ONLY")

        # Scene render
        render_rect = QRectF(0, 65, pw, ph - 100)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.scene.render(painter, render_rect, self.scene.sceneRect())

        # Footer
        painter.setPen(QColor("#333"))
        footer_font = QFont("Arial", 8)
        painter.setFont(footer_font)
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        painter.drawText(0, ph - 55, pw, 25, Qt.AlignmentFlag.AlignCenter,
                         f"Generated: {ts}  |  MCS CVOR Remote Management System")

        # Page 2: Equipment inventory
        writer.newPage()
        painter.fillRect(0, 0, pw, 40, QColor("#0a2158"))
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(0, 0, pw, 40, Qt.AlignmentFlag.AlignCenter, "Equipment Inventory")

        items = [i for i in self.scene.items() if isinstance(i, RackItem)]
        row_h = 28
        y = 50
        headers = ["Name", "Rack", "Slot", "Status", "Notes"]
        col_widths = [int(pw * 0.3), int(pw * 0.1), int(pw * 0.1), int(pw * 0.15), int(pw * 0.35)]
        # Header
        painter.fillRect(0, y, pw, row_h, QColor("#0a2158"))
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        x = 0
        for h, cw in zip(headers, col_widths):
            painter.drawText(x + 4, y, cw, row_h, Qt.AlignmentFlag.AlignVCenter, h)
            x += cw
        y += row_h

        for rack_item in items:
            d = rack_item.item_data
            fg_hex, bg_hex = RACK_COLOURS.get(d.get("status", "OK"), RACK_COLOURS["OK"])
            painter.fillRect(0, y, pw, row_h, QColor(bg_hex))
            painter.setPen(QColor(fg_hex))
            painter.setFont(QFont("Arial", 9))
            row_vals = [d.get("name", ""), d.get("rack", ""), d.get("slot", ""),
                        d.get("status", ""), d.get("notes", "")]
            x = 0
            for val, cw in zip(row_vals, col_widths):
                painter.drawText(x + 4, y, cw, row_h, Qt.AlignmentFlag.AlignVCenter, str(val))
                x += cw
            y += row_h
            if y > ph - 40:
                writer.newPage()
                y = 10

        painter.end()
        return True


class ShelterEditorWidget(QWidget):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self._cvor = None
        self._snap_enabled = True
        self._grid_visible = True
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = QToolBar()
        toolbar.setStyleSheet("QToolBar { background: #2c3e50; }")
        add_act = toolbar.addAction("➕ Add")
        del_act = toolbar.addAction("🗑 Delete")
        fwd_act = toolbar.addAction("⬆ Bring Forward")
        bwd_act = toolbar.addAction("⬇ Send Backward")
        toolbar.addSeparator()
        self.grid_act = toolbar.addAction("⊞ Grid")
        self.grid_act.setCheckable(True)
        self.grid_act.setChecked(True)
        self.snap_act = toolbar.addAction("🔲 Snap")
        self.snap_act.setCheckable(True)
        self.snap_act.setChecked(True)
        toolbar.addSeparator()
        clear_act = toolbar.addAction("✖ Clear All")
        save_act = toolbar.addAction("💾 Save to DB")
        pdf_act = toolbar.addAction("📄 Export PDF")
        svg_act = toolbar.addAction("🖼 Export SVG")
        legend_act = toolbar.addAction("ℹ Legend")
        layout.addWidget(toolbar)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: palette
        self._palette = EquipmentPalette()
        self._palette.setFixedWidth(210)
        self._palette.add_equipment.connect(self._add_from_palette)
        splitter.addWidget(self._palette)

        # Centre: canvas
        canvas_widget = QWidget()
        canvas_layout = QVBoxLayout(canvas_widget)
        canvas_layout.setContentsMargins(0, 0, 0, 0)

        zoom_bar = QHBoxLayout()
        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedWidth(30)
        zoom_out_btn = QPushButton("−")
        zoom_out_btn.setFixedWidth(30)
        fit_btn = QPushButton("Fit")
        fit_btn.setFixedWidth(50)
        zoom_bar.addStretch()
        zoom_bar.addWidget(zoom_out_btn)
        zoom_bar.addWidget(zoom_in_btn)
        zoom_bar.addWidget(fit_btn)
        canvas_layout.addLayout(zoom_bar)

        self._scene = ShelterScene()
        self._view = QGraphicsView(self._scene)
        self._view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        canvas_layout.addWidget(self._view)
        splitter.addWidget(canvas_widget)

        # Right: properties
        self._props = RackPropertiesPanel()
        self._props.setFixedWidth(230)
        splitter.addWidget(self._props)

        layout.addWidget(splitter)

        # Connect scene signals
        self._scene.request_edit.connect(self._props.load_item)
        self._scene.selection_changed_item.connect(self._props.load_item)

        # Connect toolbar actions
        add_act.triggered.connect(self._add_custom)
        del_act.triggered.connect(self._delete_selected)
        fwd_act.triggered.connect(self._bring_forward)
        bwd_act.triggered.connect(self._send_backward)
        self.grid_act.toggled.connect(self._toggle_grid)
        self.snap_act.toggled.connect(self._toggle_snap)
        clear_act.triggered.connect(self._clear_all)
        save_act.triggered.connect(self._save_layout)
        pdf_act.triggered.connect(self._export_pdf)
        svg_act.triggered.connect(self._export_svg)
        legend_act.triggered.connect(self._show_legend)
        zoom_in_btn.clicked.connect(lambda: self._view.scale(1.2, 1.2))
        zoom_out_btn.clicked.connect(lambda: self._view.scale(1 / 1.2, 1 / 1.2))
        fit_btn.clicked.connect(
            lambda: self._view.fitInView(
                self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio
            )
        )

    def load_cvor(self, cvor):
        self._cvor = cvor
        if cvor is None:
            return
        with self.db.get_session() as session:
            from ..database.models import ShelterLayout
            layout = session.query(ShelterLayout).filter_by(base_id=cvor.base_id).first()
            if layout and layout.layout_json:
                try:
                    eq_list = json.loads(layout.layout_json)
                    self._scene.load_from_list(eq_list)
                    return
                except Exception:
                    pass
        self._scene.load_from_list([])

    def _add_from_palette(self, item_data: dict):
        item = RackItem(item_data, QRectF(0, 0, 120, 60))
        item.setPos(100, 100)
        self._scene.addItem(item)

    def _add_custom(self):
        name, ok = QInputDialog.getText(self, "Add Equipment", "Equipment name:")
        if ok and name:
            item = RackItem({"name": name, "status": "OK", "icon": "rack"})
            item.setPos(100, 100)
            self._scene.addItem(item)

    def _delete_selected(self):
        for item in self._scene.selectedItems():
            self._scene.removeItem(item)

    def _bring_forward(self):
        for item in self._scene.selectedItems():
            item.setZValue(item.zValue() + 1)

    def _send_backward(self):
        for item in self._scene.selectedItems():
            item.setZValue(item.zValue() - 1)

    def _toggle_grid(self, checked: bool):
        self._scene._grid_visible = checked
        self._scene.update()

    def _toggle_snap(self, checked: bool):
        self._scene._snap_enabled = checked

    def _clear_all(self):
        reply = QMessageBox.question(self, "Clear All", "Remove all equipment from the layout?")
        if reply == QMessageBox.StandardButton.Yes:
            self._scene.clear()
            self._scene._draw_shelter_outline()

    def _save_layout(self):
        if self._cvor is None:
            return
        layout_json = self._scene.to_layout_json()
        self.db.save_shelter_layout(self._cvor.base_id, layout_json)
        QMessageBox.information(self, "Saved", "Shelter layout saved to database.")

    def _export_pdf(self):
        if not HAS_PDF:
            QMessageBox.warning(self, "PDF", "PDF export requires PyQt6.QtPrintSupport.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "", "PDF Files (*.pdf)")
        if path:
            exporter = ShelterPDFExporter(self._scene, self._cvor)
            ok = exporter.export_pdf(path)
            if ok:
                QMessageBox.information(self, "Exported", f"PDF saved to:\n{path}")

    def _export_svg(self):
        if not HAS_SVG:
            QMessageBox.warning(self, "SVG", "SVG export requires PyQt6.QtSvg.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export SVG", "", "SVG Files (*.svg)")
        if path:
            generator = QSvgGenerator()
            generator.setFileName(path)
            sz = self._scene.sceneRect().size().toSize()
            generator.setSize(sz)
            generator.setViewBox(self._scene.sceneRect().toRect())
            painter = QPainter(generator)
            self._scene.render(painter)
            painter.end()
            QMessageBox.information(self, "Exported", f"SVG saved to:\n{path}")

    def _show_legend(self):
        msg = "<b>Shelter Status Legend</b><br>"
        for status, (fg, bg) in RACK_COLOURS.items():
            msg += f'<span style="background:{bg};color:{fg};padding:2px 8px;">{status}</span><br>'
        QMessageBox.information(self, "Legend", msg)
