from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from sqlalchemy.orm import Session
from meter.config import MeterConfig, AppMode
from meter.reader import DLMSMeterReader
from meter.obis import lookup_obis, COMMON_OBIS_CODES
from ..db.models import Meter, MeterReading, MeterObject, Firmware, TestRun, FailureRecord

# A meter counts as "online" only if it has produced real evidence of
# contact (a connect/disconnect call or a real read — see last_seen's
# write path above) within this window. Fixed business decision, not
# inferred: 5 minutes.
ONLINE_STALENESS_THRESHOLD = timedelta(minutes=5)


def _safe_value_str(value: Any) -> str:
    """MeterReading.value/raw_value are String(256) columns. Most OBIS reads
    are short scalars, but the Load Profile buffer (1.0.99.1.0.255) returns a
    list of 10 record dicts — str()'ing that directly overflows the column
    and makes Postgres reject the insert (confirmed: this broke
    read_all_telemetry() entirely once the mock started returning real
    profile data for that OBIS code). Summarize non-scalar values instead of
    stringifying them in full; truncate any string as a last resort."""
    if isinstance(value, (list, dict)):
        return f"{len(value)} record(s)"
    return str(value)[:256]


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

    def get_or_create_meter(self, meter_number: Optional[str] = None) -> Meter:
        """Resolves the meter this reader is talking to. With no meter_number
        given (the normal case — every call site in this file and in main.py
        calls this with no argument), identity comes entirely from the
        reader: real hardware identity once connected, or the mock adapter's
        own identity in demo mode — never a hardcoded fake serial baked into
        this method itself."""
        if meter_number is not None:
            meter = self.db.query(Meter).filter(Meter.meter_number == meter_number).first()
            if meter:
                return meter

        info = self.reader.get_meter_information()
        resolved_number = meter_number or info["serial_number"]

        meter = self.db.query(Meter).filter(Meter.meter_number == resolved_number).first()
        if not meter:
            firmware = self._resolve_firmware(info["firmware_version"])
            meter = Meter(
                meter_number=resolved_number,
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
            "data_source": self.reader.data_source,
        }

    def disconnect_meter(self) -> dict:
        """Mirrors connect_meter()'s pattern: persists the real status change
        instead of only reporting it in the response body, so meter.status is
        a reliable "is this meter connected" signal for callers (e.g. the
        Live Meter frontend) that only have the DB row to check, not a live
        reader instance."""
        disconnected = self.reader.disconnect()
        meter = self.get_or_create_meter()
        meter.last_seen = datetime.utcnow()
        meter.status = "OFFLINE" if disconnected else meter.status
        self.db.commit()
        return {
            "meter_id": meter.meter_id,
            "meter_number": meter.meter_number,
            "disconnected": disconnected,
            "status": meter.status,
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
            value=_safe_value_str(result.value),
            raw_value=(result.raw_value or "")[:256],
            unit=result.unit,
            data_type=result.data_type,
            timestamp=result.timestamp,
            quality="GOOD" if result.status == "PASS" else "BAD",
            source="DLMS_READ",
        )
        self.db.add(reading)
        # A real successful read is itself real evidence of contact with the
        # meter — last_seen must advance here too, not just on explicit
        # connect()/disconnect() calls. Without this, a meter driven purely
        # by ongoing reads (e.g. Live Meter's polling, which never calls
        # /connect again after the first load) would incorrectly go "stale"
        # under the 5-minute is_online threshold despite being actively read.
        meter.last_seen = datetime.utcnow()
        self.db.commit()
        self.db.refresh(reading)
        # Transient — not a mapped column, not persisted. Real per-request
        # value (mock/hardware), not fabricated; set after refresh() since
        # refresh() only touches mapped attributes anyway, but this makes
        # the ordering unambiguous.
        reading.data_source = result.data_source
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
                value=_safe_value_str(res.value),
                raw_value=(res.raw_value or "")[:256],
                unit=res.unit,
                data_type=res.data_type,
                timestamp=res.timestamp,
                quality="GOOD",
                source="DLMS_POLL",
            )
            reading.data_source = res.data_source  # transient, not persisted
            self.db.add(reading)
            readings.append(reading)
        # Same reasoning as read_obis() above — a real successful read is
        # real evidence of contact, so last_seen must advance here too.
        meter.last_seen = datetime.utcnow()
        self.db.commit()
        return readings

    def get_meter_profile(self, meter_id: int) -> Optional[dict]:
        """Real per-meter profile: identity/status fields plus real
        aggregates computed from test_runs/failures/meter_readings scoped
        to this one meter_id — no fleet-wide numbers (see
        AnalyticsService.get_overview_kpis for the fleet-wide version this
        mirrors), no fabricated defaults for a meter with zero history.
        Returns None if no such meter exists — caller maps that to 404."""
        meter = self.db.query(Meter).filter(Meter.meter_id == meter_id).first()
        if not meter:
            return None

        # Postgres returns last_seen as timezone-aware (TIMESTAMPTZ), while
        # datetime.utcnow() (used by every write path to this column) is
        # naive — direct subtraction between the two raises TypeError.
        # Normalize: treat a naive value as UTC (correct, since that's what
        # every writer actually means) rather than assuming both sides
        # already agree.
        last_seen = meter.last_seen
        if last_seen is not None and last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        is_online = last_seen is not None and (now - last_seen) < ONLINE_STALENESS_THRESHOLD

        last_run = (
            self.db.query(TestRun)
            .filter(TestRun.meter_id == meter_id)
            .order_by(TestRun.started_at.desc())
            .first()
        )
        last_test_run = None
        last_run_passed = False
        if last_run:
            last_run_passed = last_run.status == "COMPLETED"
            last_test_run = {
                "test_run_id": last_run.test_run_id,
                "status": last_run.status,
                "started_at": last_run.started_at,
                "finished_at": last_run.finished_at,
                "duration_seconds": last_run.duration_seconds,
            }

        # Certified requires BOTH real signals to agree right now — a
        # meter that passed its last run three days ago but hasn't been
        # heard from since is not "currently" certified, and a meter that's
        # online but never had a clean run isn't either.
        is_certified = is_online and last_run_passed

        total_test_runs = (
            self.db.query(func.count(TestRun.test_run_id))
            .filter(TestRun.meter_id == meter_id)
            .scalar() or 0
        )
        total_tests = (
            self.db.query(func.sum(TestRun.total_tests))
            .filter(TestRun.meter_id == meter_id)
            .scalar() or 0
        )
        passed_tests = (
            self.db.query(func.sum(TestRun.passed_tests))
            .filter(TestRun.meter_id == meter_id)
            .scalar() or 0
        )
        avg_duration = (
            self.db.query(func.avg(TestRun.duration_seconds))
            .filter(TestRun.meter_id == meter_id)
            .scalar() or 0.0
        )
        pass_rate = round((passed_tests / total_tests * 100), 1) if total_tests > 0 else 0.0

        failures_resolved_count = (
            self.db.query(FailureRecord)
            .filter(FailureRecord.meter_id == meter_id, FailureRecord.resolved_date.isnot(None))
            .count()
        )
        total_readings_count = (
            self.db.query(MeterReading)
            .filter(MeterReading.meter_id == meter_id)
            .count()
        )

        return {
            "meter_id": meter.meter_id,
            "meter_number": meter.meter_number,
            "meter_type": meter.meter_type,
            "meter_model": meter.meter_model,
            "manufacturer": meter.manufacturer,
            "firmware_version": meter.firmware_version,
            "hardware_revision": meter.hardware_revision,
            "communication_interface": meter.communication_interface,
            "status": meter.status,
            "first_seen": meter.first_seen,
            "last_seen": meter.last_seen,
            "is_online": is_online,
            "last_test_run": last_test_run,
            "is_certified": is_certified,
            "total_test_runs": total_test_runs,
            "pass_rate": pass_rate,
            "avg_duration_seconds": round(avg_duration, 2),
            "failures_resolved_count": failures_resolved_count,
            "total_readings_count": total_readings_count,
        }
