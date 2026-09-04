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


if __name__ == "__main__":
    unittest.main()
