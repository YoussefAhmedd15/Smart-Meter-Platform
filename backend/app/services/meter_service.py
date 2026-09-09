from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from meter.config import MeterConfig, AppMode
from meter.reader import DLMSMeterReader
from meter.obis import lookup_obis, COMMON_OBIS_CODES
from ..db.models import Meter, MeterReading, MeterObject, Firmware


class MeterService:

    def __init__(self, db: Session, config: Optional[MeterConfig] = None):
        self.db = db
        self.config = config or MeterConfig()
        self.reader = DLMSMeterReader(self.config)

    def _resolve_firmware(self, version_string: str) -> Firmware:
        """Gets-or-creates the `firmwares` row for a version string. Meters store a
        firmware_id FK, not a raw version string, so every write path that only has
        a version string (e.g. from the meter/reader layer) goes through this."""
        firmware = self.db.query(Firmware).filter(Firmware.version == version_string).first()
        if not firmware:
            firmware = Firmware(version=version_string, status="RELEASED")
            self.db.add(firmware)
            self.db.commit()
            self.db.refresh(firmware)
        return firmware

    def get_or_create_meter(self, meter_number: str = "ISK-2026-984210") -> Meter:
        meter = self.db.query(Meter).filter(Meter.meter_number == meter_number).first()
        if not meter:
            info = self.reader.get_meter_information()
            firmware = self._resolve_firmware(info["firmware_version"])
            meter = Meter(
                meter_number=info["serial_number"],
                manufacturer=info["manufacturer"],
                meter_model=info["model"],
                firmware_id=firmware.firmware_id,
                hardware_revision=info["hardware_revision"],
                communication_interface=info["communication_interface"],
                status="ONLINE",
            )
            self.db.add(meter)
            self.db.commit()
            self.db.refresh(meter)
        return meter

    def connect_meter(self, meter_id: Optional[int] = None) -> dict:
        connected = self.reader.connect()
        init_res = self.reader.initialize()
        meter = None
        if meter_id:
            meter = self.db.query(Meter).filter(Meter.meter_id == meter_id).first()
        if not meter:
            meter = self.get_or_create_meter()
        meter.last_seen = datetime.utcnow()
        meter.status = "ONLINE" if connected else "ERROR"
        self.db.commit()
        return {
            "meter_id": meter.meter_id,
            "meter_number": meter.meter_number,
            "connected": connected,
            "handshake": init_res,
        }

    def discover_objects(self) -> List[MeterObject]:
        meter = self.get_or_create_meter()
        self.reader.connect()
        assoc = self.reader.get_association_view()

        db_objects = []
        for obj in assoc.objects:
            existing = (
                self.db.query(MeterObject)
                .filter(MeterObject.meter_id == meter.meter_id, MeterObject.obis == obj.obis)
                .first()
            )
            if not existing:
                existing = MeterObject(
                    meter_id=meter.meter_id,
                    obis=obj.obis,
                    class_id=obj.class_id,
                    name=obj.name,
                    description=obj.description,
                    attributes=[a.model_dump() for a in obj.attributes],
                )
                self.db.add(existing)
            db_objects.append(existing)
        self.db.commit()
        return db_objects

    def read_obis(self, obis_code: str, attribute_index: int = 2) -> MeterReading:
        meter = self.get_or_create_meter()
        self.reader.connect()
        result = self.reader.read_obis(obis_code, attribute_index)

        reading = MeterReading(
            meter_id=meter.meter_id,
            obis=result.obis,
            attribute_index=result.attribute_index,
            value=str(result.value),
            raw_value=result.raw_value,
            unit=result.unit,
            data_type=result.data_type,
            timestamp=result.timestamp,
            quality="GOOD" if result.status == "PASS" else "BAD",
            source="DLMS_READ",
        )
        self.db.add(reading)
        self.db.commit()
        self.db.refresh(reading)
        return reading

    def read_all_telemetry(self) -> List[MeterReading]:
        meter = self.get_or_create_meter()
        self.reader.connect()
        results = self.reader.read_all()
        readings = []
        for res in results:
            reading = MeterReading(
                meter_id=meter.meter_id,
                obis=res.obis,
                attribute_index=res.attribute_index,
                value=str(res.value),
                raw_value=res.raw_value,
                unit=res.unit,
                data_type=res.data_type,
                timestamp=res.timestamp,
                quality="GOOD",
                source="DLMS_POLL",
            )
            self.db.add(reading)
            readings.append(reading)
        self.db.commit()
        return readings
