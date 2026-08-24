"""CVOR Detail Widget with 5 tabs."""
import asyncio
import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QDoubleSpinBox, QSpinBox, QCheckBox, QPushButton,
    QTextEdit, QFormLayout, QGroupBox, QFileDialog
)
from PyQt6.QtCore import QThread, pyqtSignal

from .shelter_editor import ShelterEditorWidget


STATUS_COLOURS = {
    "ACTIVE": ("#155724", "#d4edda"),
    "INACTIVE": ("#383d41", "#e2e3e5"),
    "FAULT": ("#721c24", "#f8d7da"),
    "STANDBY": ("#856404", "#fff3cd"),
    "MAINTENANCE": ("#004085", "#cce5ff"),
}

ALARM_BITS = {
    0: "TX Overtemp", 1: "PA Fault", 2: "VSWR High", 3: "Low Power",
    4: "Monitor Fail", 5: "Ref Fail", 6: "PSU Fault", 7: "Antenna Fault",
    8: "Remote Fault", 9: "Control Fail", 10: "Sync Loss", 11: "Mod Fail",
    12: "Reserved", 13: "Reserved", 14: "Reserved", 15: "Reserved",
}


class ApplyWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, coro, parent=None):
        super().__init__(parent)
        self._coro = coro

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(self._coro)
            loop.close()
            self.finished.emit(bool(result), "")
        except Exception as e:
            self.finished.emit(False, str(e))


class CVORDetailWidget(QWidget):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self._cvor = None
        self._worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.title_lbl = QLabel("Select a CVOR system")
        self.title_lbl.setStyleSheet(
            "font-size:14px;font-weight:bold;color:#0a2158;"
            "padding:4px;background:#e8eef7;border-radius:4px;"
        )
        layout.addWidget(self.title_lbl)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tabs.addTab(self._build_status_tab(), "Status & Alarms")
        self.tabs.addTab(self._build_settings_tab(), "Remote Settings")
        self.tabs.addTab(self._build_config_tab(), "Config Files")
        self._shelter_widget = ShelterEditorWidget(self.db)
        self.tabs.addTab(self._shelter_widget, "Shelter Layout")
        self.tabs.addTab(self._build_history_tab(), "History")

    def _build_status_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        status_group = QGroupBox("System Status")
        status_form = QFormLayout(status_group)
        self.lbl_status = QLabel("—")
        self.lbl_freq = QLabel("—")
        self.lbl_power = QLabel("—")
        self.lbl_vswr = QLabel("—")
        self.lbl_last_poll = QLabel("—")
        status_form.addRow("Status:", self.lbl_status)
        status_form.addRow("Frequency:", self.lbl_freq)
        status_form.addRow("Power:", self.lbl_power)
        status_form.addRow("VSWR:", self.lbl_vswr)
        status_form.addRow("Last Poll:", self.lbl_last_poll)
        layout.addWidget(status_group)

        alarm_group = QGroupBox("Active Alarms")
        alarm_layout = QVBoxLayout(alarm_group)
        self.alarm_table = QTableWidget(0, 3)
        self.alarm_table.setHorizontalHeaderLabels(["Bit", "Description", "State"])
        self.alarm_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.alarm_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        alarm_layout.addWidget(self.alarm_table)
        layout.addWidget(alarm_group)
        return w

    def _build_settings_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        net_group = QGroupBox("Network Configuration")
        net_form = QFormLayout(net_group)
        self.ip_edit = QLineEdit()
        self.mask_edit = QLineEdit()
        self.gw_edit = QLineEdit()
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(5000)
        net_form.addRow("IP Address:", self.ip_edit)
        net_form.addRow("Subnet Mask:", self.mask_edit)
        net_form.addRow("Gateway:", self.gw_edit)
        net_form.addRow("TCP Port:", self.port_spin)
        layout.addWidget(net_group)

        cvor_group = QGroupBox("CVOR Parameters")
        cvor_form = QFormLayout(cvor_group)
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(108.0, 118.0)
        self.freq_spin.setDecimals(2)
        self.freq_spin.setSuffix(" MHz")
        self.power_spin = QSpinBox()
        self.power_spin.setRange(0, 200)
        self.power_spin.setSuffix(" W")
        self.morse_edit = QLineEdit()
        self.morse_edit.setMaxLength(6)
        self.standby_check = QCheckBox("Enable Standby Mode")
        cvor_form.addRow("Frequency:", self.freq_spin)
        cvor_form.addRow("Power:", self.power_spin)
        cvor_form.addRow("Morse ID:", self.morse_edit)
        cvor_form.addRow(self.standby_check)
        layout.addWidget(cvor_group)

        btn_row = QHBoxLayout()
        detect_btn = QPushButton("🔍 Auto-Detect NIC")
        save_db_btn = QPushButton("💾 Save to DB")
        apply_btn = QPushButton("📡 Apply Remote")
        reset_btn = QPushButton("🔄 Reset System")
        detect_btn.clicked.connect(self._auto_detect_nic)
        save_db_btn.clicked.connect(self._save_to_db)
        apply_btn.clicked.connect(self._apply_remote)
        reset_btn.clicked.connect(self._reset_system)
        btn_row.addWidget(detect_btn)
        btn_row.addWidget(save_db_btn)
        btn_row.addWidget(apply_btn)
        btn_row.addWidget(reset_btn)
        layout.addLayout(btn_row)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(100)
        self.log_area.setPlaceholderText("Operation log...")
        layout.addWidget(self.log_area)
        return w

    def _build_config_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        btn_row = QHBoxLayout()
        import_btn = QPushButton("📂 Import Config File")
        import_btn.clicked.connect(self._import_config)
        btn_row.addWidget(import_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        self.config_table = QTableWidget(0, 4)
        self.config_table.setHorizontalHeaderLabels(["Filename", "Type", "Imported", "Size"])
        self.config_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.config_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.config_table)
        return w

    def _build_history_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        self.history_table = QTableWidget(0, 5)
        self.history_table.setHorizontalHeaderLabels(
            ["Parameter", "Old Value", "New Value", "Changed By", "When"]
        )
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)
        layout.addWidget(self.history_table)
        return w

    def load_cvor(self, cvor) -> None:
        self._cvor = cvor
        if cvor is None:
            self.title_lbl.setText("Select a CVOR system")
            return
        self.title_lbl.setText(f"{cvor.system_id}  —  {cvor.model}  |  {cvor.frequency_mhz} MHz")
        self._refresh_status()
        self._refresh_settings()
        self._refresh_config_files()
        self._refresh_history()
        self._shelter_widget.load_cvor(cvor)

    def _refresh_status(self):
        cvor = self._cvor
        if not cvor:
            return
        fg, bg = STATUS_COLOURS.get(cvor.status, ("#000", "#fff"))
        self.lbl_status.setText(cvor.status)
        self.lbl_status.setStyleSheet(
            f"color:{fg};background:{bg};padding:2px 6px;border-radius:3px;"
        )
        self.lbl_freq.setText(f"{cvor.frequency_mhz} MHz")
        self.lbl_power.setText("— W")
        self.lbl_vswr.setText("—")
        self.lbl_last_poll.setText(
            cvor.last_polled.strftime("%Y-%m-%d %H:%M:%S") if cvor.last_polled else "Never"
        )
        self.alarm_table.setRowCount(0)

    def _refresh_settings(self):
        cvor = self._cvor
        if not cvor:
            return
        self.ip_edit.setText(cvor.ip_address or "")
        self.port_spin.setValue(cvor.port or 5000)
        self.freq_spin.setValue(cvor.frequency_mhz or 108.0)
        self.morse_edit.setText(cvor.morse_id or "")

    def _refresh_config_files(self):
        if not self._cvor:
            return
        self.config_table.setRowCount(0)
        with self.db.get_session() as session:
            from ..database.models import CVORConfigFile
            files = session.query(CVORConfigFile).filter_by(cvor_id=self._cvor.id).all()
            for f in files:
                row = self.config_table.rowCount()
                self.config_table.insertRow(row)
                self.config_table.setItem(row, 0, QTableWidgetItem(f.filename))
                self.config_table.setItem(row, 1, QTableWidgetItem(f.file_type))
                self.config_table.setItem(row, 2, QTableWidgetItem(
                    f.imported_at.strftime("%Y-%m-%d %H:%M") if f.imported_at else "—"
                ))
                self.config_table.setItem(row, 3, QTableWidgetItem(
                    f"{len(f.content)} bytes" if f.content else "0"
                ))

    def _refresh_history(self):
        if not self._cvor:
            return
        self.history_table.setRowCount(0)
        for h in self.db.get_settings_history(self._cvor.id):
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            self.history_table.setItem(row, 0, QTableWidgetItem(h.parameter))
            self.history_table.setItem(row, 1, QTableWidgetItem(h.old_value or ""))
            self.history_table.setItem(row, 2, QTableWidgetItem(h.new_value or ""))
            self.history_table.setItem(row, 3, QTableWidgetItem(h.changed_by or ""))
            self.history_table.setItem(row, 4, QTableWidgetItem(
                h.changed_at.strftime("%Y-%m-%d %H:%M") if h.changed_at else "—"
            ))

    def _auto_detect_nic(self):
        from ..network.network_detect import get_local_interfaces
        ifaces = get_local_interfaces()
        if not ifaces:
            self._log("No active network interfaces found.")
            return
        iface = ifaces[0]
        self.ip_edit.setText(iface.get("ip", ""))
        self.mask_edit.setText(iface.get("netmask", ""))
        self.gw_edit.setText(iface.get("gateway", ""))
        self._log(f"Detected: {iface.get('interface')} — IP: {iface.get('ip')}")

    def _save_to_db(self):
        if not self._cvor:
            return
        with self.db.get_session() as session:
            from ..database.models import CVORSystem
            cvor = session.get(CVORSystem, self._cvor.id)
            if cvor:
                old_ip = cvor.ip_address
                old_freq = cvor.frequency_mhz
                cvor.ip_address = self.ip_edit.text()
                cvor.port = self.port_spin.value()
                cvor.frequency_mhz = self.freq_spin.value()
                cvor.morse_id = self.morse_edit.text()
                session.commit()
                self.db.save_settings_history(
                    self._cvor.id, "IP/FREQ",
                    f"{old_ip}/{old_freq}",
                    f"{self.ip_edit.text()}/{self.freq_spin.value()}"
                )
                self._log("Settings saved to database.")

    def _apply_remote(self):
        if not self._cvor or not self._cvor.ip_address:
            self._log("No IP configured.")
            return

        async def _do():
            from ..network.tcp_client import CVORTCPClient
            import struct
            client = CVORTCPClient(self._cvor.ip_address, self._cvor.port or 5000)
            freq_int = int(self.freq_spin.value() * 10)
            return await client.set_parameter(0x01, struct.pack(">H", freq_int))

        self._worker = ApplyWorker(_do())
        self._worker.finished.connect(
            lambda ok, err: self._log(f"Remote apply: {'OK' if ok else 'FAILED ' + err}")
        )
        self._worker.start()

    def _reset_system(self):
        if not self._cvor or not self._cvor.ip_address:
            self._log("No IP configured.")
            return

        async def _do():
            from ..network.tcp_client import CVORTCPClient
            client = CVORTCPClient(self._cvor.ip_address, self._cvor.port or 5000)
            return await client.reset_system()

        self._worker = ApplyWorker(_do())
        self._worker.finished.connect(
            lambda ok, err: self._log(f"Reset: {'OK' if ok else 'FAILED ' + err}")
        )
        self._worker.start()

    def _import_config(self):
        if not self._cvor:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Config File", "",
            "Config Files (*.ini *.sys *.cfg *.lda *.LDA);;All Files (*)"
        )
        if not path:
            return
        ext = os.path.splitext(path)[1].lower()
        file_type = ext.lstrip(".")
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()
        self.db.import_config_file(self._cvor.id, os.path.basename(path), file_type, content)
        self._refresh_config_files()
        self._log(f"Imported: {os.path.basename(path)}")

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_area.append(f"[{ts}] {msg}")
