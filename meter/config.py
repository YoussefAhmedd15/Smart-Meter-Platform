import os
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class CommunicationInterface(str, Enum):
    HDLC = "HDLC"
    HDLC_WITH_MODE_E = "HDLC_WITH_MODE_E"
    WRAPPER = "WRAPPER"


class AuthenticationType(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    HIGH = "HIGH"
    HIGH_MD5 = "HIGH_MD5"
    HIGH_SHA1 = "HIGH_SHA1"
    HIGH_GMAC = "HIGH_GMAC"
    HIGH_SHA256 = "HIGH_SHA256"


class AppMode(str, Enum):
    HARDWARE = "hardware"
    DEMO = "demo"


class MeterConfig(BaseModel):
    """
    Configuration model for Smart Meter DLMS/COSEM communication.
    Reads defaults from environment variables with safe defaults.
    """
    app_mode: AppMode = Field(
        default_factory=lambda: AppMode(os.getenv("APP_MODE", "hardware").lower())
    )
    interface: CommunicationInterface = Field(
        default_factory=lambda: CommunicationInterface(
            os.getenv("METER_INTERFACE", "HDLC_WITH_MODE_E").upper()
        )
    )
    serial_port: str = Field(
        default_factory=lambda: os.getenv("METER_SERIAL_PORT", "COM6")
    )
    baudrate: int = Field(
        default_factory=lambda: int(os.getenv("METER_BAUDRATE", "300"))
    )
    data_bits: int = Field(
        default_factory=lambda: int(os.getenv("METER_DATA_BITS", "7"))
    )
    parity: str = Field(
        default_factory=lambda: os.getenv("METER_PARITY", "EVEN").upper()
    )
    stop_bits: int = Field(
        default_factory=lambda: int(os.getenv("METER_STOP_BITS", "1"))
    )
    client_address: int = Field(
        default_factory=lambda: int(os.getenv("METER_CLIENT_ADDRESS", "1"))
    )
    logical_address: int = Field(
        default_factory=lambda: int(os.getenv("METER_LOGICAL_ADDRESS", "0"))
    )
    physical_address: int = Field(
        default_factory=lambda: int(os.getenv("METER_PHYSICAL_ADDRESS", "11"))
    )
    authentication: AuthenticationType = Field(
        default_factory=lambda: AuthenticationType(
            os.getenv("METER_AUTHENTICATION", "LOW").upper()
        )
    )
    password: str = Field(
        default_factory=lambda: os.getenv("METER_PASSWORD", "")
    )
    timeout_ms: int = Field(
        default_factory=lambda: int(os.getenv("METER_TIMEOUT", "5000"))
    )
    host: Optional[str] = Field(
        default_factory=lambda: os.getenv("METER_HOST", None)
    )
    port: int = Field(
        default_factory=lambda: int(os.getenv("METER_PORT", "4059"))
    )
    use_logical_name_referencing: bool = Field(default=True)

    def calculate_server_address(self) -> int:
        """
        Calculates HDLC server address from logical address and physical address.
        Formula (Gurux DLMS standard):
        Logical Address shifted by 7 bits + Physical Address or physical address alone.
        """
        if self.logical_address == 0:
            return self.physical_address
        return (self.logical_address << 7) | (self.physical_address & 0x7F)

    def sanitized_dict(self) -> dict:
        """Returns configuration dictionary with password masked for safe logging."""
        data = self.model_dump()
        if data.get("password"):
            data["password"] = "******"
        return data
