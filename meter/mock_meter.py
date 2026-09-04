import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from .config import MeterConfig
from .objects import ReadResult, AssociationView, COSEMObjectDescriptor, AttributeDescriptor
from .obis import COMMON_OBIS_CODES, lookup_obis


class MockMeterAdapter:
    """
    High-fidelity Smart Meter simulator for Iskraemeco meters.
    Generates dynamic physical readings, realistic load profiles,
    and complete COSEM association views without needing physical hardware.
    """

    def __init__(self, config: Optional[MeterConfig] = None):
        self.config = config or MeterConfig()
        self.serial_number = "ISK-2026-984210"
        self.manufacturer = "Iskraemeco"
        self.model = "AM550-TD1"
        self.firmware_version = "v3.14.2"
        self.hardware_revision = "HW-2.1"
        self._connected: bool = False
        self._base_energy = 1245.30

    def connect(self) -> bool:
        """Simulates physical serial/optical connection establishment."""
        time.sleep(0.05)  # Simulate small handshake delay
        self._connected = True
        return True

    def disconnect(self) -> bool:
        """Simulates disconnection."""
        self._connected = False
        return True

    def is_connected(self) -> bool:
        return self._connected

    def initialize(self) -> dict:
        """Simulates SNRM and AARQ handshake."""
        if not self._connected:
            self.connect()
        return {
            "status": "CONNECTED",
            "interface": self.config.interface.value,
            "serial_port": self.config.serial_port,
            "mode_e_handshake": "COMPLETED" if "MODE_E" in self.config.interface.value else "N/A",
            "snrm": "UA_RECEIVED",
            "aarq": "AARE_ACCEPTED",
            "server_address": self.config.calculate_server_address(),
            "client_address": self.config.client_address,
        }

    def get_association_view(self) -> AssociationView:
        """Generates COSEM object association view."""
        objects = []
        for obis_code, defn in COMMON_OBIS_CODES.items():
            attrs = [
                AttributeDescriptor(index=1, name="Logical Name", data_type="OctetString"),
                AttributeDescriptor(index=2, name="Value", data_type="DoubleLongUnsigned" if defn.class_id == 3 else "OctetString"),
            ]
            if defn.class_id == 3:  # Register
                attrs.append(AttributeDescriptor(index=3, name="Scaler Unit", data_type="Structure"))
            objects.append(
                COSEMObjectDescriptor(
                    class_id=defn.class_id,
                    obis=obis_code,
                    version=0,
                    name=defn.name,
                    description=defn.description,
                    attributes=attrs,
                )
            )
        return AssociationView(
            meter_serial=self.serial_number,
            total_objects=len(objects),
            objects=objects,
        )

    def discover_objects(self) -> List[COSEMObjectDescriptor]:
        return self.get_association_view().objects

    def read_obis(self, obis_code: str, attribute_index: int = 2) -> ReadResult:
        """Generates realistic sensor reading for given OBIS code."""
        start_time = time.time()
        time.sleep(random.uniform(0.01, 0.03))  # Simulate reading delay ~20ms
        
        defn = lookup_obis(obis_code)
        value: Any = None
        unit = defn.unit or ""
        data_type = "DoubleLongUnsigned"

        # Generate realistic dynamic data
        if obis_code == "1.0.1.8.0.255":  # Energy Import
            self._base_energy += random.uniform(0.001, 0.005)
            value = round(self._base_energy, 3)
            unit = "kWh"
        elif obis_code == "1.0.2.8.0.255":  # Energy Export
            value = 142.15
            unit = "kWh"
        elif obis_code == "1.0.32.7.0.255":  # Voltage L1
            value = round(230.2 + random.uniform(-1.5, 1.5), 1)
            unit = "V"
        elif obis_code == "1.0.52.7.0.255":  # Voltage L2
            value = round(229.8 + random.uniform(-1.2, 1.2), 1)
            unit = "V"
        elif obis_code == "1.0.72.7.0.255":  # Voltage L3
            value = round(230.8 + random.uniform(-1.4, 1.4), 1)
            unit = "V"
        elif obis_code == "1.0.31.7.0.255":  # Current L1
            value = round(4.31 + random.uniform(-0.3, 0.3), 2)
            unit = "A"
        elif obis_code == "1.0.51.7.0.255":  # Current L2
            value = round(4.12 + random.uniform(-0.25, 0.25), 2)
            unit = "A"
        elif obis_code == "1.0.71.7.0.255":  # Current L3
            value = round(4.45 + random.uniform(-0.35, 0.35), 2)
            unit = "A"
        elif obis_code == "1.0.1.7.0.255":  # Active Power
            value = round(875 + random.uniform(-25, 25), 1)
            unit = "W"
        elif obis_code == "1.0.14.7.0.255":  # Frequency
            value = round(50.01 + random.uniform(-0.03, 0.03), 2)
            unit = "Hz"
        elif obis_code == "1.0.13.7.0.255":  # Power Factor
            value = round(0.96 + random.uniform(-0.01, 0.01), 2)
            unit = ""
        elif obis_code == "0.0.1.0.0.255":  # Clock
            value = datetime.utcnow().isoformat() + "Z"
            data_type = "OctetString"
        elif obis_code == "0.0.96.1.1.255":  # Serial
            value = self.serial_number
            data_type = "OctetString"
        elif obis_code == "0.0.96.1.0.255":  # Firmware
            value = self.firmware_version
            data_type = "OctetString"
        else:
            value = 100.0

        duration_ms = round((time.time() - start_time) * 1000, 2)
        return ReadResult(
            obis=obis_code,
            attribute_index=attribute_index,
            value=value,
            raw_value=str(value),
            unit=unit,
            data_type=data_type,
            timestamp=datetime.utcnow(),
            duration_ms=duration_ms,
            status="PASS",
        )

    def read_all(() -> List[ReadResult]:
        results = []
        for obis_code in COMMON_OBIS_CODES.keys():
            results.append(self.read_obis(obis_code))
        return results

    def read_profile(self, obis_code: str = "1.0.99.1.0.255", limit: int = 10) -> List[dict]:
        """Generates mock load profile history."""
        records = []
        now = datetime.utcnow()
        for i in range(limit):
            ts = now - timedelta(minutes=15 * i)
            records.append({
                "timestamp": ts.isoformat() + "Z",
                "active_energy_import_kwh": round(1245.3 - (i * 0.25), 3),
                "active_power_kw": round(0.875 + random.uniform(-0.1, 0.1), 3),
                "voltage_l1_v": round(230.2 + random.uniform(-1.0, 1.0), 1),
                "current_l1_a": round(4.31 + random.uniform(-0.2, 0.2), 2),
                "status_code": "00000000",
            })
        return records

    def get_meter_information(() -> dict:
        return {
            "serial_number": self.serial_number,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "firmware_version": self.firmware_version,
            "hardware_revision": self.hardware_revision,
            "communication_interface": self.config.interface.value,
            "serial_port": self.config.serial_port,
            "status": "ONLINE",
        }
