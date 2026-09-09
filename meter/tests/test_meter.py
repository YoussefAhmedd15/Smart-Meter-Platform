import unittest
from meter.config import MeterConfig, CommunicationInterface, AppMode
from meter.obis import lookup_obis, COMMON_OBIS_CODES
from meter.mock_meter import MockMeterAdapter
from meter.reader import DLMSMeterReader
from meter.exceptions import OBISNotFoundError


class TestMeterPackage(unittest.TestCase):

    def test_config_defaults(self):
        config = MeterConfig()
        self.assertEqual(config.serial_port, "COM6")
        self.assertEqual(config.baudrate, 300)
        self.assertEqual(config.client_address, 1)
        self.assertEqual(config.physical_address, 11)

    def test_server_address_calculation(self):
        config = MeterConfig(logical_address=0, physical_address=11)
        self.assertEqual(config.calculate_server_address(), 11)

        config_shifted = MeterConfig(logical_address=1, physical_address=11)
        self.assertEqual(config_shifted.calculate_server_address(), (1 << 7) | 11)

    def test_obis_lookup(self):
        defn = lookup_obis("1.0.1.8.0.255")
        self.assertEqual(defn.name, "Active Energy Import (+A)")
        self.assertEqual(defn.unit, "kWh")

        unknown = lookup_obis("9.9.9.9.9.255")
        self.assertTrue("Vendor Specific" in unknown.name)

    def test_mock_meter_adapter(self):
        adapter = MockMeterAdapter()
        self.assertTrue(adapter.connect())
        self.assertTrue(adapter.is_connected())

        assoc = adapter.get_association_view()
        self.assertGreater(assoc.total_objects, 5)

        read_res = adapter.read_obis("1.0.32.7.0.255")
        self.assertEqual(read_res.unit, "V")
        self.assertGreater(read_res.value, 200)

        profile = adapter.read_profile(limit=5)
        self.assertEqual(len(profile), 5)

    def test_dlms_reader_demo_mode(self):
        config = MeterConfig(app_mode=AppMode.DEMO)
        reader = DLMSMeterReader(config)
        self.assertTrue(reader.connect())

        init_data = reader.initialize()
        self.assertEqual(init_data["status"], "CONNECTED")

        info = reader.get_meter_information()
        self.assertEqual(info["manufacturer"], "Iskraemeco")

        reading = reader.read_obis("1.0.14.7.0.255")  # Frequency
        self.assertEqual(reading.unit, "Hz")
        self.assertAlmostEqual(reading.value, 50.0, delta=1.0)


class _DummyObjects:
    """Stands in for GXDLMSClient.objects. Records what was actually looked
    up so a test can prove the real hardware code path ran (not just that
    it didn't crash)."""

    def __init__(self):
        self.find_calls = []

    def findByLN(self, object_type, obis_code):
        self.find_calls.append((object_type, obis_code))
        return object()  # any non-None sentinel stands in for "object found"


class _DummyClient:
    def __init__(self):
        self.objects = _DummyObjects()


class _DummyGuruxReader:
    """Stands in for GXDLMSReader. Simulates "a real connection already
    exists" (the exact condition reader.py's own methods check —
    self._reader being truthy) without any real hardware, media, or Gurux
    connection at all."""

    def __init__(self, stub_value="STUB-VALUE"):
        self.stub_value = stub_value
        self.read_calls = []

    def read(self, obj, attribute_index):
        self.read_calls.append((obj, attribute_index))
        return self.stub_value


class TestHardwareBranchingLogic(unittest.TestCase):
    """Verifies the data_source branching logic itself using a stub
    self._reader/self._client — NOT a real hardware integration test. Real
    hardware (or a proper DLMS simulator) isn't available in this
    environment, so full end-to-end hardware verification is out of scope
    until one is. What IS provable without hardware: that the code
    correctly chooses "hardware" and actually calls through to whatever
    reader is present, rather than silently pulling from MockMeterAdapter,
    and that this doesn't disturb the mock path at all.
    """

    def _hardware_reader(self, stub_value="231.4"):
        config = MeterConfig(app_mode=AppMode.HARDWARE)
        reader = DLMSMeterReader(config)
        reader._reader = _DummyGuruxReader(stub_value)
        reader._client = _DummyClient()
        return reader

    def test_hardware_present_uses_hardware_path_not_mock(self):
        reader = self._hardware_reader(stub_value="231.4")
        result = reader.read_obis("1.0.32.7.0.255")

        self.assertEqual(result.data_source, "hardware")
        self.assertEqual(result.value, "231.4")

        # Proves it actually went through the stub reader, not MockMeterAdapter.
        self.assertEqual(len(reader._reader.read_calls), 1)
        self.assertEqual(reader._client.objects.find_calls[0][1], "1.0.32.7.0.255")

    def test_reader_data_source_property_reflects_hardware_state(self):
        reader = self._hardware_reader()
        self.assertEqual(reader.data_source, "hardware")

    def test_mock_path_unaffected_by_hardware_branching_change(self):
        config = MeterConfig(app_mode=AppMode.DEMO)
        reader = DLMSMeterReader(config)
        self.assertEqual(reader.data_source, "mock")

        result = reader.read_obis("1.0.32.7.0.255")
        self.assertEqual(result.data_source, "mock")

    def test_no_reader_present_falls_back_to_mock_even_in_hardware_app_mode(self):
        # app_mode=HARDWARE but self._reader is still None (connect() never
        # called, or it never succeeded) — must still honestly report
        # "mock", not claim hardware just because the mode setting says so.
        config = MeterConfig(app_mode=AppMode.HARDWARE)
        reader = DLMSMeterReader(config)
        self.assertIsNone(reader._reader)
        self.assertEqual(reader.data_source, "mock")

        result = reader.read_obis("1.0.32.7.0.255")
        self.assertEqual(result.data_source, "mock")


if __name__ == "__main__":
    unittest.main()
