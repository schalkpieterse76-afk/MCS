"""Dialogs for adding and splitting bases."""
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
    QDialogButtonBox, QVBoxLayout, QLabel, QTextEdit
)


class AddBaseDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle("Add Air Force Base")
        self.setMinimumWidth(400)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.code_edit = QLineEdit()
        self.location_edit = QLineEdit()
        self.lat_spin = QDoubleSpinBox()
        self.lat_spin.setRange(-90, 90)
        self.lat_spin.setDecimals(4)
        self.lon_spin = QDoubleSpinBox()
        self.lon_spin.setRange(-180, 180)
        self.lon_spin.setDecimals(4)
        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("e.g. 192.168.1.100")
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(108.0, 118.0)
        self.freq_spin.setDecimals(1)
        self.freq_spin.setSuffix(" MHz")
        self.morse_edit = QLineEdit()
        self.morse_edit.setMaxLength(6)
        self.morse_edit.setPlaceholderText("3-letter ID")

        form.addRow("Base Name:", self.name_edit)
        form.addRow("Base Code:", self.code_edit)
        form.addRow("Location:", self.location_edit)
        form.addRow("Latitude:", self.lat_spin)
        form.addRow("Longitude:", self.lon_spin)
        form.addRow("CVOR IP:", self.ip_edit)
        form.addRow("Frequency:", self.freq_spin)
        form.addRow("Morse ID:", self.morse_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _accept(self):
        if not self.name_edit.text().strip():
            return
        if not self.code_edit.text().strip():
            return
        self.db.add_base(
            self.name_edit.text().strip(),
            self.code_edit.text().strip().upper(),
            self.location_edit.text().strip(),
            self.lat_spin.value(),
            self.lon_spin.value(),
            self.ip_edit.text().strip(),
            self.freq_spin.value(),
            self.morse_edit.text().strip().upper(),
        )
        self.accept()


class SplitBaseDialog(QDialog):
    def __init__(self, db_manager, parent_base, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.parent_base = parent_base
        self.setWindowTitle(f"Split Base: {parent_base.name}")
        self.setMinimumWidth(400)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<b>Splitting:</b> {self.parent_base.name} ({self.parent_base.code})"))

        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.code_edit = QLineEdit()
        self.reason_edit = QTextEdit()
        self.reason_edit.setMaximumHeight(80)
        self.lat_spin = QDoubleSpinBox()
        self.lat_spin.setRange(-90, 90)
        self.lat_spin.setDecimals(4)
        self.lat_spin.setValue(self.parent_base.latitude)
        self.lon_spin = QDoubleSpinBox()
        self.lon_spin.setRange(-180, 180)
        self.lon_spin.setDecimals(4)
        self.lon_spin.setValue(self.parent_base.longitude)

        form.addRow("New Base Name:", self.name_edit)
        form.addRow("New Code:", self.code_edit)
        form.addRow("Reason:", self.reason_edit)
        form.addRow("Latitude:", self.lat_spin)
        form.addRow("Longitude:", self.lon_spin)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _accept(self):
        if not self.name_edit.text().strip() or not self.code_edit.text().strip():
            return
        self.db.split_base(
            self.parent_base.id,
            self.name_edit.text().strip(),
            self.code_edit.text().strip().upper(),
            self.reason_edit.toPlainText().strip(),
            self.lat_spin.value(),
            self.lon_spin.value(),
        )
        self.accept()
