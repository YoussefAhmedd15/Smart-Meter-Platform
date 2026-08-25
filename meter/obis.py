from typing import Dict, Optional, NamedTuple


class OBISDefinition(NamedTuple):
    obis: str
    class_id: int
    name: str
    description: str
    unit: Optional[str]
    scaler: float = 1.0


COMMON_OBIS_CODES: Dict[str, OBISDefinition] = {
    "1.0.1.8.0.255": OBISDefinition(
        obis="1.0.1.8.0.255",
        class_id=3,  # Register
        name="Active Energy Import (+A)",
        description="Total cumulative active energy imported from grid",
        unit="kWh",
    ),
    "1.0.2.8.0.255": OBISDefinition(
        obis="1.0.2.8.0.255",
        class_id=3,
        name="Active Energy Export (-A)",
        description="Total cumulative active energy exported to grid",
        unit="kWh",
    ),
    "1.0.32.7.0.255": OBISDefinition(
        obis="1.0.32.7.0.255",
        class_id=3,
        name="Instantaneous Voltage L1",
        description="RMS Voltage on Phase L1",
        unit="V",
    ),
    "1.0.52.7.0.255": OBISDefinition(
        obis="1.0.52.7.0.255",
        class_id=3,
        name="Instantaneous Voltage L2",
        description="RMS Voltage on Phase L2",
        unit="V",
    ),
    "1.0.72.7.0.255": OBISDefinition(
        obis="1.0.72.7.0.255",
        class_id=3,
        name="Instantaneous Voltage L3",
        description="RMS Voltage on Phase L3",
        unit="V",
    ),
    "1.0.31.7.0.255": OBISDefinition(
        obis="1.0.31.7.0.255",
        class_id=3,
        name="Instantaneous Current L1",
        description="RMS Current on Phase L1",
        unit="A",
    ),
    "1.0.51.7.0.255": OBISDefinition(
        obis="1.0.51.7.0.255",
        class_id=3,
        name="Instantaneous Current L2",
        description="RMS Current on Phase L2",
        unit="A",
    ),
    "1.0.71.7.0.255": OBISDefinition(
        obis="1.0.71.7.0.255",
        class_id=3,
        name="Instantaneous Current L3",
        description="RMS Current on Phase L3",
        unit="A",
    ),
    "1.0.1.7.0.255": OBISDefinition(
        obis="1.0.1.7.0.255",
        class_id=3,
        name="Active Power (+P)",
        description="Total instantaneous active power",
        unit="W",
    ),
    "1.0.14.7.0.255": OBISDefinition(
        obis="1.0.14.7.0.255",
        class_id=3,
        name="Grid Frequency",
        description="Network frequency",
        unit="Hz",
    ),
    "1.0.13.7.0.255": OBISDefinition(
        obis="1.0.13.7.0.255",
        class_id=3,
        name="Power Factor Total",
        description="Total displacement power factor",
        unit="",
    ),
    "0.0.1.0.0.255": OBISDefinition(
        obis="0.0.1.0.0.255",
        class_id=8,  # Clock
        name="Clock / Real Time",
        description="Internal meter real-time clock",
        unit="",
    ),
    "1.0.99.1.0.255": OBISDefinition(
        obis="1.0.99.1.0.255",
        class_id=7,  # Profile Generic
        name="Load Profile 1",
        description="Periodic load profile record table",
        unit="",
    ),
    "0.0.96.1.1.255": OBISDefinition(
        obis="0.0.96.1.1.255",
        class_id=1,  # Data
        name="Serial Number / Meter ID",
        description="Device serial number identifier",
        unit="",
    ),
    "0.0.96.1.0.255": OBISDefinition(
        obis="0.0.96.1.0.255",
        class_id=1,
        name="Firmware Version",
        description="Installed meter firmware identifier",
        unit="",
    ),
}


def lookup_obis(obis_code: str) -> OBISDefinition:
    """
    Looks up an OBIS code in the registry.
    If unknown, returns a generic fallback OBISDefinition without failing.
    """
    if obis_code in COMMON_OBIS_CODES:
        return COMMON_OBIS_CODES[obis_code]
    return OBISDefinition(
        obis=obis_code,
        class_id=1,
        name=f"Vendor Specific OBIS ({obis_code})",
        description="Manufacturer specific or custom OBIS code",
        unit="",
    )
