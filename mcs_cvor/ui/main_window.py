"""Main application window for MCS CVOR Remote Management System."""
import asyncio
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QToolBar, QTreeWidget, QTreeWidgetItem, QTabWidget,
    QStatusBar, QFileDialog, QMessageBox, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QFont, QAction

from .map_view import CVORMapView
from .base_panel import BasePanel
from .cvor_detail import CVORDetailWidget
from .settings_dialog import AddBaseDialog, SplitBaseDialog
from ..utils.export_manager import ExportManager

STATUS_COLOURS = {
    "ACTIVE": QColor("#28a745"),
    "INACTIVE": QColor("#6c757d"),
    "FAULT": QColor("#dc3545"),
    "STANDBY": QColor("#fd7e14"),
    "MAINTENANCE": QColor("#0d6efd"),
}

TOOLBAR_STYLE = """
QToolBar {
    background: #0a2158;
    spacing: 6px;
    padding: 4px;
}
QToolButton {
    color: white;
    background: #1a3a8a;
    border: none;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 12px;
}
QToolButton:hover { background: #2a5abf; }
QToolButton:pressed { background: #0a2158; }
"""


class PollWorker(QThread):
    poll_complete = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, bases: list, parent=None):
        super().__init__(parent)
        self._bases = bases

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            results = loop.run_until_complete(self._poll_all())
            loop.close()
            self.poll_complete.emit(results)
        except Exception as e:
            self.error.emit(str(e))

    async def _poll_all(self) -> list:
        from ..network.tcp_client import CVORTCPClient
        results = []
        for base in self._bases:
            for cvor in base.cvor_systems:
                if cvor.ip_address:
                    client = CVORTCPClient(cvor.ip_address, cvor.port or 5000, timeout=3.0)
                    status = await client.get_status()
                    results.append((cvor.system_id, status))
        return results


class MainWindow(QMainWindow):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self._poll_timer_id = None
        self._poll_worker: Optional[PollWorker] = None
        self._bases = []
        self.setWindowTitle("MCS CVOR Remote Management System — SAAF")
        self.setMinimumSize(1200, 700)
        self._init_ui()
        self._load_bases()
        self._start_poll_timer()

    def _init_ui(self):
        # Toolbar
        tb = QToolBar("Main")
        tb.setStyleSheet(TOOLBAR_STYLE)
        tb.setMovable(False)
        tb.setIconSize(QSize(16, 16))
        self.addToolBar(tb)

        add_act = QAction("➕ Add Base", self)
        del_act = QAction("🗑 Delete Base", self)
        split_act = QAction("✂ Split Base", self)
        poll_act = QAction("📡 Poll Now", self)
        export_act = QAction("💾 Export All", self)
        import_act = QAction("📂 Import Config", self)

        add_act.triggered.connect(self._add_base)
        del_act.triggered.connect(self._delete_base)
        split_act.triggered.connect(self._split_base)
        poll_act.triggered.connect(self._poll_now)
        export_act.triggered.connect(self._export_all)
        import_act.triggered.connect(self._import_config)

        for act in (add_act, del_act, split_act):
            tb.addAction(act)
        tb.addSeparator()
        for act in (poll_act, export_act, import_act):
            tb.addAction(act)

        # Central
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left tree
        self._tree = QTreeWidget()
        self._tree.setHeaderLabel("Air Force Bases")
        self._tree.setMinimumWidth(220)
        self._tree.setMaximumWidth(300)
        self._tree.setFont(QFont("Arial", 10))
        self._tree.itemClicked.connect(self._on_tree_click)
        splitter.addWidget(self._tree)

        # Right tabs
        self._right_tabs = QTabWidget()
        self._map_view = CVORMapView()
        self._base_panel = BasePanel()
        self._cvor_detail = CVORDetailWidget(self.db)
        self._right_tabs.addTab(self._map_view, "🗺 Map")
        self._right_tabs.addTab(self._base_panel, "🏠 Base Details")
        self._right_tabs.addTab(self._cvor_detail, "📡 CVOR Control")
        splitter.addWidget(self._right_tabs)
        splitter.setStretchFactor(1, 3)

        main_layout.addWidget(splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready — MCS CVOR Remote Management System")

    def _load_bases(self):
        self._bases = self.db.get_all_bases()
        self._refresh_tree()
        self._map_view.refresh_map(self._bases)

    def _refresh_tree(self):
        self._tree.clear()
        for base in self._bases:
            base_item = QTreeWidgetItem([base.name])
            base_item.setData(0, Qt.ItemDataRole.UserRole, ("base", base.id))
            base_item.setFont(0, QFont("Arial", 10, QFont.Weight.Bold))
            for cvor in base.cvor_systems:
                cvor_item = QTreeWidgetItem([f"  {cvor.system_id}"])
                colour = STATUS_COLOURS.get(cvor.status, QColor("#6c757d"))
                cvor_item.setForeground(0, colour)
                cvor_item.setData(0, Qt.ItemDataRole.UserRole, ("cvor", cvor.id, base.id))
                base_item.addChild(cvor_item)
            self._tree.addTopLevelItem(base_item)
        self._tree.expandAll()

    def _on_tree_click(self, item: QTreeWidgetItem, col: int):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        if data[0] == "base":
            base = next((b for b in self._bases if b.id == data[1]), None)
            self._base_panel.load_base(base)
            self._right_tabs.setCurrentIndex(1)
        elif data[0] == "cvor":
            cvor_id = data[1]
            base = next((b for b in self._bases if b.id == data[2]), None)
            if base:
                cvor = next((c for c in base.cvor_systems if c.id == cvor_id), None)
                self._cvor_detail.load_cvor(cvor)
                self._right_tabs.setCurrentIndex(2)

    def _add_base(self):
        dlg = AddBaseDialog(self.db, self)
        if dlg.exec():
            self._load_bases()

    def _delete_base(self):
        item = self._tree.currentItem()
        if not item:
            return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data[0] != "base":
            QMessageBox.information(self, "Delete", "Please select a base.")
            return
        reply = QMessageBox.question(
            self, "Delete Base",
            f"Mark base '{item.text(0)}' as deleted?",
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_base(data[1])
            self._load_bases()

    def _split_base(self):
        item = self._tree.currentItem()
        if not item:
            return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data[0] != "base":
            QMessageBox.information(self, "Split", "Please select a base.")
            return
        base = next((b for b in self._bases if b.id == data[1]), None)
        if base:
            dlg = SplitBaseDialog(self.db, base, self)
            if dlg.exec():
                self._load_bases()

    def _poll_now(self):
        if self._poll_worker and self._poll_worker.isRunning():
            return
        self.status_bar.showMessage("Polling CVOR systems...")
        self._poll_worker = PollWorker(self._bases)
        self._poll_worker.poll_complete.connect(self._on_poll_complete)
        self._poll_worker.error.connect(lambda e: self.status_bar.showMessage(f"Poll error: {e}"))
        self._poll_worker.start()

    def _on_poll_complete(self, results: list):
        for system_id, status_data in results:
            if status_data:
                self.db.update_cvor_status(
                    system_id,
                    status_data.get("status", "INACTIVE"),
                    freq=status_data.get("frequency"),
                    power=status_data.get("power_w"),
                    vswr=status_data.get("vswr"),
                )
        self._load_bases()
        ts = datetime.now().strftime("%H:%M:%S")
        self.status_bar.showMessage(f"Poll complete at {ts} — {len(results)} system(s) polled")

    def _start_poll_timer(self):
        from PyQt6.QtCore import QTimer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_now)
        self._timer.start(30_000)  # 30 seconds

    def _export_all(self):
        output_dir = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if not output_dir:
            return
        exporter = ExportManager(self.db)
        path = exporter.export_all(output_dir)
        QMessageBox.information(self, "Exported", f"Data exported to:\n{path}")

    def _import_config(self):
        item = self._tree.currentItem()
        if not item:
            QMessageBox.information(self, "Import", "Please select a CVOR system first.")
            return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data[0] != "cvor":
            QMessageBox.information(self, "Import", "Please select a CVOR system.")
            return
        self._right_tabs.setCurrentIndex(2)
        self._cvor_detail._import_config()
