import json
import os
from datetime import datetime

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import joinedload, sessionmaker
from sqlalchemy.pool import StaticPool

from .models import AirForceBase, Base, BaseSplit, CVORConfigFile, CVORSystem, SettingsHistory, ShelterLayout


class DBManager:
    def __init__(self, db_path=None):
        if db_path is None:
            db_dir = os.path.join(os.path.expanduser("~"), ".mcs_cvor")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "mcs_cvor.db")

        if db_path == ":memory:":
            self.engine = create_engine(
                "sqlite://",
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            if not os.path.isabs(db_path):
                db_path = os.path.abspath(db_path)
            db_dir = os.path.dirname(db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
            self.engine = create_engine(f"sqlite:///{db_path}")

        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        Base.metadata.create_all(self.engine)

        with self.get_session() as session:
            count = session.scalar(select(func.count()).select_from(AirForceBase)) or 0
        if count == 0:
            self._seed_bases()

    def _seed_bases(self):
        base_data = [
            ("AFB Waterkloof", "AFB_WAT", "Pretoria", -25.83, 28.22, 113.8, "WAT"),
            ("AFB Hoedspruit", "AFB_HOE", "Hoedspruit", -24.37, 31.05, 115.2, "HOE"),
            ("AFB Langebaanweg", "AFB_LBW", "Langebaanweg", -32.97, 18.16, 114.5, "LBW"),
            ("AFB Overberg", "AFB_OVB", "Overberg", -34.55, 20.50, 112.3, "OVB"),
            ("AFB Ysterplaat", "AFB_YST", "Cape Town", -33.90, 18.50, 116.0, "YST"),
            ("AFB Makhado", "AFB_MAK", "Makhado", -23.16, 29.70, 117.5, "MAK"),
            ("AFB Bloemspruit", "AFB_BLO", "Bloemfontein", -29.09, 26.30, 111.8, "BLO"),
            ("AFB Port Elizabeth", "AFB_PLZ", "Port Elizabeth", -33.98, 25.62, 109.6, "PLZ"),
            ("AFB Swartkop", "AFB_SWK", "Centurion", -25.81, 28.16, 110.2, "SWK"),
            ("AFB Durban", "AFB_DUR", "Durban", -29.97, 30.95, 108.4, "DUR"),
        ]

        with self.get_session() as session:
            for index, (name, code, location, lat, lon, freq, morse) in enumerate(base_data, start=1):
                base = AirForceBase(
                    name=name,
                    code=code,
                    location=location,
                    latitude=lat,
                    longitude=lon,
                    is_active=True,
                )
                session.add(base)
                session.flush()

                cvor = CVORSystem(
                    base_id=base.id,
                    system_id=f"{code}_CVOR",
                    model="Thales CVOR 432",
                    ip_address=f"192.168.{index}.10",
                    port=5000,
                    frequency_mhz=freq,
                    morse_id=morse,
                    status="INACTIVE",
                )
                session.add(cvor)

                layout = ShelterLayout(
                    base_id=base.id,
                    name=f"{name} Shelter",
                    shelter_type="Standard",
                    width_m=12.0,
                    height_m=3.0,
                    layout_json=json.dumps(self._default_equipment_layout(), indent=2),
                )
                session.add(layout)

            session.commit()

    def _default_equipment_layout(self):
        equipment_names = [
            "CVOR Transmitter",
            "Modulator Unit",
            "Power Amplifier",
            "Antenna Coupler",
            "Monitor Receiver",
            "Control Unit",
            "PSU Main",
            "PSU Backup",
            "Alarm Panel",
            "UPS Unit",
            "Ethernet Switch",
            "Serial Converter",
            "Remote Control Unit",
        ]
        return [
            {
                "name": name,
                "rack": "A",
                "slot": index,
                "status": "OK",
                "icon": "rack",
            }
            for index, name in enumerate(equipment_names, start=1)
        ]

    def get_session(self):
        return self.session_factory()

    def get_all_bases(self):
        with self.get_session() as session:
            result = session.execute(
                select(AirForceBase)
                .where(AirForceBase.is_active.is_(True))
                .options(joinedload(AirForceBase.cvor_systems))
                .order_by(AirForceBase.name)
            )
            return result.unique().scalars().all()

    def add_base(self, name, code, location, lat, lon, cvor_ip, freq, morse):
        with self.get_session() as session:
            base = AirForceBase(
                name=name,
                code=code,
                location=location,
                latitude=lat,
                longitude=lon,
                is_active=True,
            )
            session.add(base)
            session.flush()

            cvor = CVORSystem(
                base_id=base.id,
                system_id=f"{code}_CVOR",
                model="Thales CVOR 432",
                ip_address=cvor_ip,
                port=5000,
                frequency_mhz=freq,
                morse_id=morse,
                status="INACTIVE",
            )
            layout = ShelterLayout(
                base_id=base.id,
                name=f"{name} Shelter",
                shelter_type="Standard",
                width_m=12.0,
                height_m=3.0,
                layout_json=json.dumps(self._default_equipment_layout(), indent=2),
            )
            session.add_all([cvor, layout])
            session.commit()
            return base

    def delete_base(self, base_id):
        with self.get_session() as session:
            base = session.get(AirForceBase, base_id)
            if base is None:
                return False
            base.is_active = False
            session.commit()
            return True

    def split_base(self, parent_id, new_name, new_code, reason, lat, lon):
        with self.get_session() as session:
            parent = session.get(AirForceBase, parent_id)
            if parent is None:
                return None

            child = AirForceBase(
                name=new_name,
                code=new_code,
                location=parent.location,
                latitude=lat,
                longitude=lon,
                is_active=True,
            )
            session.add(child)
            session.flush()

            if parent.cvor_systems:
                source_cvor = parent.cvor_systems[0]
                session.add(
                    CVORSystem(
                        base_id=child.id,
                        system_id=f"{new_code}_CVOR",
                        model=source_cvor.model,
                        ip_address=source_cvor.ip_address,
                        port=source_cvor.port,
                        frequency_mhz=source_cvor.frequency_mhz,
                        morse_id=source_cvor.morse_id,
                        status="INACTIVE",
                    )
                )

            session.add(
                ShelterLayout(
                    base_id=child.id,
                    name=f"{new_name} Shelter",
                    shelter_type="Standard",
                    width_m=12.0,
                    height_m=3.0,
                    layout_json=json.dumps(self._default_equipment_layout(), indent=2),
                )
            )

            split = BaseSplit(
                parent_base_id=parent.id,
                child_base_id=child.id,
                reason=reason,
            )
            session.add(split)
            session.commit()
            return child

    def update_cvor_status(self, system_id, status, freq=None, power=None, vswr=None):
        with self.get_session() as session:
            cvor = session.execute(select(CVORSystem).where(CVORSystem.system_id == system_id)).scalar_one_or_none()
            if cvor is None:
                return False

            cvor.status = status
            cvor.last_polled = datetime.utcnow()
            if freq is not None:
                cvor.frequency_mhz = freq
            session.commit()
            return True

    def save_settings_history(self, cvor_id, param, old_val, new_val, changed_by="user"):
        with self.get_session() as session:
            history = SettingsHistory(
                cvor_id=cvor_id,
                parameter=param,
                old_value=old_val,
                new_value=new_val,
                changed_by=changed_by,
            )
            session.add(history)
            session.commit()
            return history

    def import_config_file(self, cvor_id, filename, file_type, content):
        with self.get_session() as session:
            config_file = CVORConfigFile(
                cvor_id=cvor_id,
                filename=filename,
                file_type=file_type,
                content=content,
            )
            session.add(config_file)
            session.commit()
            return config_file

    def save_shelter_layout(self, base_id, layout_json):
        with self.get_session() as session:
            layout = session.execute(
                select(ShelterLayout).where(ShelterLayout.base_id == base_id)
            ).scalar_one_or_none()
            if layout is None:
                return None
            layout.layout_json = layout_json
            layout.updated_at = datetime.utcnow()
            session.commit()
            return layout

    def get_settings_history(self, cvor_id):
        with self.get_session() as session:
            result = session.execute(
                select(SettingsHistory)
                .where(SettingsHistory.cvor_id == cvor_id)
                .order_by(SettingsHistory.changed_at.desc(), SettingsHistory.id.desc())
            )
            return result.scalars().all()
