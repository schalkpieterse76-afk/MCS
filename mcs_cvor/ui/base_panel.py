"""Base information panel widget."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QGroupBox, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


STATUS_BADGE_COLOURS = {
    "ACTIVE": ("#155724", "#d4edda"),
    "INACTIVE": ("#383d41", "#e2e3e5"),
    "FAULT": ("#721c24", "#f8d7da"),
    "STANDBY": ("#856404", "#fff3cd"),
    "MAINTENANCE": ("#004085", "#cce5ff"),
}


class BasePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Base info group
        info_group = QGroupBox("Base Information")
        info_layout = QVBoxLayout(info_group)

        self.lbl_name = QLabel("—")
        self.lbl_name.setStyleSheet("font-size:16px;font-weight:bold;")
        self.lbl_code = QLabel("—")
        self.lbl_location = QLabel("—")
        self.lbl_coords = QLabel("—")

        info_layout.addWidget(self.lbl_name)
        info_layout.addWidget(self.lbl_code)
        info_layout.addWidget(self.lbl_location)
        info_layout.addWidget(self.lbl_coords)
        layout.addWidget(info_group)

        # CVOR systems table
        cvor_group = QGroupBox("CVOR Systems")
        cvor_layout = QVBoxLayout(cvor_group)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["System ID", "Model", "IP Address", "Freq (MHz)", "Morse", "Status"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        cvor_layout.addWidget(self.table)
        layout.addWidget(cvor_group)

    def load_base(self, base) -> None:
        if base is None:
            self.lbl_name.setText("—")
            self.lbl_code.setText("—")
            self.lbl_location.setText("—")
            self.lbl_coords.setText("—")
            self.table.setRowCount(0)
            return

        self.lbl_name.setText(base.name)
        self.lbl_code.setText(f"Code: {base.code}")
        self.lbl_location.setText(f"Location: {base.location}")
        self.lbl_coords.setText(f"Coordinates: {base.latitude:.4f}, {base.longitude:.4f}")

        self.table.setRowCount(0)
        for cvor in base.cvor_systems:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(cvor.system_id))
            self.table.setItem(row, 1, QTableWidgetItem(cvor.model))
            self.table.setItem(row, 2, QTableWidgetItem(cvor.ip_address or "—"))
            self.table.setItem(row, 3, QTableWidgetItem(str(cvor.frequency_mhz)))
            self.table.setItem(row, 4, QTableWidgetItem(cvor.morse_id or "—"))
            status_item = QTableWidgetItem(cvor.status)
            fg, bg = STATUS_BADGE_COLOURS.get(cvor.status, ("#000", "#fff"))
            status_item.setForeground(QColor(fg))
            status_item.setBackground(QColor(bg))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 5, status_item)
