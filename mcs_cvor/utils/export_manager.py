"""Export manager: JSON, CSV, raw config files, settings history — all zipped."""
import csv
import io
import json
import os
import zipfile
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..database.db_manager import DBManager


class ExportManager:
    def __init__(self, db_manager: "DBManager"):
        self.db = db_manager

    def export_all(self, output_dir: str) -> str:
        """Export all data to a zip file, return path."""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        zip_path = os.path.join(output_dir, f"mcs_cvor_export_{timestamp}.zip")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            self._write_bases_json(zf)
            self._write_bases_csv(zf)
            self._write_settings_history(zf)
            self._write_config_files(zf)

        return zip_path

    def _write_bases_json(self, zf: zipfile.ZipFile) -> None:
        bases = self.db.get_all_bases()
        data = []
        for base in bases:
            entry = {
                "id": base.id,
                "name": base.name,
                "code": base.code,
                "location": base.location,
                "latitude": base.latitude,
                "longitude": base.longitude,
                "cvor_systems": [],
            }
            for cvor in base.cvor_systems:
                entry["cvor_systems"].append({
                    "system_id": cvor.system_id,
                    "model": cvor.model,
                    "ip_address": cvor.ip_address,
                    "port": cvor.port,
                    "frequency_mhz": cvor.frequency_mhz,
                    "morse_id": cvor.morse_id,
                    "status": cvor.status,
                })
            data.append(entry)
        zf.writestr("bases.json", json.dumps(data, indent=2))

    def _write_bases_csv(self, zf: zipfile.ZipFile) -> None:
        bases = self.db.get_all_bases()
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["Base", "Code", "Location", "Latitude", "Longitude",
                         "System ID", "IP", "Port", "Freq MHz", "Morse", "Status"])
        for base in bases:
            for cvor in base.cvor_systems:
                writer.writerow([
                    base.name, base.code, base.location,
                    base.latitude, base.longitude,
                    cvor.system_id, cvor.ip_address, cvor.port,
                    cvor.frequency_mhz, cvor.morse_id, cvor.status,
                ])
        zf.writestr("bases.csv", buf.getvalue())

    def _write_settings_history(self, zf: zipfile.ZipFile) -> None:
        bases = self.db.get_all_bases()
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["System ID", "Parameter", "Old Value", "New Value", "Changed By", "Changed At"])
        for base in bases:
            for cvor in base.cvor_systems:
                for h in self.db.get_settings_history(cvor.id):
                    writer.writerow([
                        cvor.system_id, h.parameter, h.old_value,
                        h.new_value, h.changed_by, h.changed_at,
                    ])
        zf.writestr("settings_history.csv", buf.getvalue())

    def _write_config_files(self, zf: zipfile.ZipFile) -> None:
        bases = self.db.get_all_bases()
        for base in bases:
            for cvor in base.cvor_systems:
                with self.db.get_session() as session:
                    from ..database.models import CVORConfigFile
                    files = session.query(CVORConfigFile).filter_by(cvor_id=cvor.id).all()
                    for f in files:
                        zf.writestr(f"configs/{base.code}/{f.filename}", f.content or "")
