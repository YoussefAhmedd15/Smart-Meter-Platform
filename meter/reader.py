import sys
import os
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Dynamically ensure Gurux source paths are on sys.path
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GURUX_CORE_PATH = os.path.join(WORKSPACE_DIR, "Gurux.DLMS.Python", "Gurux.DLMS.python")
GURUX_EXAMPLE_PATH = os.path.join(WORKSPACE_DIR, "Gurux.DLMS.Python", "Gurux.DLMS.Client.Example.python")

for path in [GURUX_CORE_PATH, GURUX_EXAMPLE_PATH]:
    if path not in sys.path and os.path.exists(path):
        sys.path.insert(0, path)

from .config import MeterConfig, CommunicationInterface, AuthenticationType, AppMode
from .exceptions import (
    MeterCommunicationError,
    MeterTimeoutError,
    InvalidResponseError,
    SNRMFailedError,
    AARQFailedError,
    AuthenticationFailedError,
    AssociationFailedError,
    OBISNotFoundError,
    ReadFailedError,
    DecodingError,
)
from .objects import ReadResult, AssociationView, COSEMObjectDescriptor, AttributeDescriptor
from .obis import lookup_obis
from .mock_meter import MockMeterAdapter

logger = logging.getLogger("smart_meter.reader")


class DLMSMeterReader:
    """
    DLMS/COSEM Smart Meter Reader wrapping Gurux DLMS Python framework.
    Provides unified hardware and high-fidelity mock access.
    """

    def __init__(self, config: Optional[MeterConfig] = None):
        self.config = config or MeterConfig()
        self.mock_adapter = MockMeterAdapter(self.config)
        self._client = None
        self._media = None
        self._reader = None
        self._is_connected = False
        self._association_view: Optional[AssociationView] = None

    def _init_gurux_components(self) -> bool:
        """Attempts importing and setting up Gurux DLMS client and media objects."""
        try:
            from gurux_dlms import GXDLMSClient
            from gurux_dlms.enums import InterfaceType, Authentication, ObjectType
            from gurux_serial import GXSerial
            from gurux_serial.enums import BaudRate, Parity, StopBits
            from gurux_net import GXNet
            from gurux_net.enums import NetworkType
            from GXDLMSSecureClient2 import GXDLMSSecureClient2
            from GXDLMSReader import GXDLMSReader

            # Setup client
            use_ln = self.config.use_logical_name_referencing
            self._client = GXDLMSSecureClient2(use_ln)

            # Interface Type
            if self.config.interface == CommunicationInterface.HDLC:
                self._client.interfaceType = InterfaceType.HDLC
            elif self.config.interface == CommunicationInterface.HDLC_WITH_MODE_E:
                self._client.interfaceType = InterfaceType.HDLC_WITH_MODE_E
            elif self.config.interface == CommunicationInterface.WRAPPER:
                self._client.interfaceType = InterfaceType.WRAPPER

            # Addressing
            self._client.clientAddress = self.config.client_address
            self._client.serverAddress = self.config.calculate_server_address()

            # Authentication
            auth_map = {
                AuthenticationType.NONE: Authentication.NONE,
                AuthenticationType.LOW: Authentication.LOW,
                AuthenticationType.HIGH: Authentication.HIGH,
                AuthenticationType.HIGH_MD5: Authentication.HIGH_MD5,
                AuthenticationType.HIGH_SHA1: Authentication.HIGH_SHA1,
                AuthenticationType.HIGH_GMAC: Authentication.HIGH_GMAC,
                AuthenticationType.HIGH_SHA256: Authentication.HIGH_SHA256,
            }
            self._client.authentication = auth_map.get(
                self.config.authentication, Authentication.LOW
            )

            if self.config.password:
                self._client.password = self.config.password

            # Media setup
            if self.config.host:
                self._media = GXNet(NetworkType.TCP, self.config.host, self.config.port)
            # Media setup
            if self.config.host:
                self._media = GXNet(NetworkType.TCP, self.config.host, self.config.port)
            else:
                target_port = self._find_active_com_port(self.config.serial_port)
                logger.info(f"Configuring physical serial media on port: {target_port}")
                self._media = GXSerial(target_port)
                if self.config.interface == CommunicationInterface.HDLC_WITH_MODE_E:
                    # IEC Mode E initial handshake settings: 300 7E1
                    self._media.baudRate = BaudRate.BAUD_RATE_300
                    self._media.dataBits = 7
                    self._media.parity = Parity.EVEN
                    self._media.stopBits = StopBits.ONE
                else:
                    self._media.baudRate = self.config.baudrate
                    self._media.dataBits = self.config.data_bits
                    self._media.parity = Parity.EVEN if self.config.parity == "EVEN" else Parity.NONE
                    self._media.stopBits = StopBits.ONE

            self._reader = GXDLMSReader(self._client, self._media, trace=False)
            return True
        except Exception as e:
            logger.warning(f"Gurux components initialization fallback to Mock mode: {e}")
            return False

    @property
    def data_source(self) -> str:
        """"mock" or "hardware" — the single source of truth for which
        branch every read_*/connect/initialize method below is actually
        using right now. Centralized here so the same condition isn't
        duplicated (and risking drift) across every method and across
        meter_service.py."""
        return "mock" if (self.config.app_mode == AppMode.DEMO or not self._reader) else "hardware"

    def _find_active_com_port(self, default_port: str) -> str:
        """Scans available Windows COM ports for active SONDA optical head or serial adapters."""
        try:
            import serial.tools.list_ports
            ports = list(serial.tools.list_ports.comports())
            if not ports:
                return default_port
            for p in ports:
                if default_port.lower() in p.device.lower():
                    return p.device
            # If default port not found, select first available COM port
            logger.info(f"Default port {default_port} not found. Selected active COM port: {ports[0].device}")
            return ports[0].device
        except Exception:
            return default_port

    def connect(self) -> bool:
        """Connects to the smart meter (or mock engine)."""
        if self.config.app_mode == AppMode.DEMO:
            logger.info("Operating in DEMO mode — using Mock Meter Adapter.")
            self._is_connected = self.mock_adapter.connect()
            return self._is_connected

        # Hardware mode
        logger.info(f"Connecting to hardware on {self.config.serial_port or self.config.host}...")
        if not self._init_gurux_components():
            logger.warning("Hardware media initialization failed. Falling back to Demo mode.")
            self._is_connected = self.mock_adapter.connect()
            return self._is_connected

        try:
            self._media.open()
            self._is_connected = True
            logger.info("Media connection opened successfully.")
            return True
        except Exception as e:
            logger.error(f"Hardware physical connection error: {e}")
            logger.info("Falling back to Demo mode for application resilience.")
            self._is_connected = self.mock_adapter.connect()
            return self._is_connected

    def disconnect(self) -> bool:
        """Disconnects media."""
        if self.config.app_mode == AppMode.DEMO or not self._media:
            self._is_connected = False
            return self.mock_adapter.disconnect()

        try:
            if self._reader:
                self._reader.close()
            elif self._media:
                self._media.close()
        except Exception as e:
            logger.warning(f"Error during hardware disconnect: {e}")
        finally:
            self._is_connected = False
        return True

    def is_connected(self) -> bool:
        return self._is_connected

    def initialize(self) -> dict:
        """Executes SNRM/AARQ association handshake."""
        if self.config.app_mode == AppMode.DEMO or not self._reader:
            return self.mock_adapter.initialize()

        try:
            logger.info("Initializing DLMS connection (SNRM + AARQ)...")
            self._reader.initializeConnection()
            return {
                "status": "CONNECTED",
                "interface": self.config.interface.value,
                "serial_port": self.config.serial_port,
                "server_address": self._client.serverAddress,
                "client_address": self._client.clientAddress,
            }
        except Exception as e:
            err_msg = str(e)
            if "SNRM" in err_msg:
                raise SNRMFailedError(f"SNRM handshake failed: {err_msg}")
            elif "AARQ" in err_msg or "Authentication" in err_msg:
                raise AARQFailedError(f"AARQ association failed: {err_msg}")
            else:
                raise MeterCommunicationError(f"Initialization error: {err_msg}")

    def get_association_view(self) -> AssociationView:
        """Retrieves and normalizes association view of meter objects."""
        if self.config.app_mode == AppMode.DEMO or not self._reader:
            self._association_view = self.mock_adapter.get_association_view()
            return self._association_view

        try:
            self._reader.getAssociationView()
            objects = []
            for obj in self._client.objects:
                attrs = [
                    AttributeDescriptor(index=i, name=f"Attribute {i}")
                    for i in range(1, 4)
                ]
                objects.append(
                    COSEMObjectDescriptor(
                        class_id=int(obj.objectType),
                        obis=obj.logicalName,
                        version=getattr(obj, "version", 0),
                        name=lookup_obis(obj.logicalName).name,
                        attributes=attrs,
                    )
                )
            self._association_view = AssociationView(
                meter_serial=self.get_meter_information().get("serial_number", "UNKNOWN"),
                total_objects=len(objects),
                objects=objects,
                data_source="hardware",
            )
            return self._association_view
        except Exception as e:
            logger.error(f"Failed to fetch association view: {e}")
            raise AssociationFailedError(f"Association View error: {e}")

    def read_obis(self, obis_code: str, attribute_index: int = 2) -> ReadResult:
        """Reads a specific attribute of an OBIS logical name."""
        start_time = time.time()
        if self.config.app_mode == AppMode.DEMO or not self._reader:
            return self.mock_adapter.read_obis(obis_code, attribute_index)

        try:
            from gurux_dlms.enums import ObjectType
            obj = self._client.objects.findByLN(ObjectType.NONE, obis_code)
            if obj is None:
                raise OBISNotFoundError(f"OBIS {obis_code} not found in association view.")

            val = self._reader.read(obj, attribute_index)
            duration_ms = round((time.time() - start_time) * 1000, 2)
            defn = lookup_obis(obis_code)

            return ReadResult(
                obis=obis_code,
                attribute_index=attribute_index,
                value=val,
                raw_value=str(val),
                unit=defn.unit or "",
                data_type=type(val).__name__,
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                status="PASS",
                data_source="hardware",
            )
        except OBISNotFoundError:
            raise
        except Exception as e:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            raise ReadFailedError(
                f"Failed reading OBIS {obis_code}: {e}",
                details={"obis": obis_code, "duration_ms": duration_ms},
            )

    def read_all(self) -> List[ReadResult]:
        if self.config.app_mode == AppMode.DEMO or not self._reader:
            return self.mock_adapter.read_all()

        results = []
        for obis in ["1.0.1.8.0.255", "1.0.32.7.0.255", "1.0.31.7.0.255", "1.0.14.7.0.255"]:
            try:
                results.append(self.read_obis(obis))
            except Exception as e:
                logger.warning(f"Error reading OBIS {obis}: {e}")
        return results

    def read_profile(self, obis_code: str = "1.0.99.1.0.255", limit: int = 10) -> List[dict]:
        # No real Gurux load-profile-buffer read is implemented yet — both
        # branches genuinely call the mock adapter today. Left as-is rather
        # than labeling this "hardware", which would be exactly the kind of
        # false claim this session exists to remove. Each record already
        # carries its own real "data_source": "mock" (see mock_meter.py).
        return self.mock_adapter.read_profile(obis_code, limit)

    def _read_identity_field(self, obis_code: str) -> str:
        """Reads one identity OBIS via the real hardware path (read_obis's
        own hardware branch — this method is only ever called from within
        that branch, so it's never accidentally reading from the mock).
        Returns "UNKNOWN" for that one field on failure rather than
        silently falling back to a hardcoded literal."""
        try:
            return str(self.read_obis(obis_code).value)
        except Exception as e:
            logger.warning(f"Could not read identity OBIS {obis_code}: {e}")
            return "UNKNOWN"

    def get_meter_information(self) -> dict:
        if self.config.app_mode == AppMode.DEMO or not self._reader:
            return self.mock_adapter.get_meter_information()

        # Real reads of the meter's own identity OBIS codes — not hardcoded
        # literals. Only two identity OBIS codes are actually registered
        # anywhere in this codebase (meter/obis.py): serial number
        # (0.0.96.1.1.255) and firmware version (0.0.96.1.0.255). No
        # manufacturer/model/hardware_revision OBIS mapping exists or is
        # documented anywhere here — rather than guessing one, those three
        # are honestly reported as unknown until a real mapping is
        # confirmed against actual hardware.
        return {
            "serial_number": self._read_identity_field("0.0.96.1.1.255"),
            "manufacturer": "UNKNOWN",
            "model": "UNKNOWN",
            "firmware_version": self._read_identity_field("0.0.96.1.0.255"),
            "hardware_revision": "UNKNOWN",
            "communication_interface": self.config.interface.value,
            "serial_port": self.config.serial_port,
            "status": "ONLINE" if self._is_connected else "OFFLINE",
            "data_source": "hardware",
        }
