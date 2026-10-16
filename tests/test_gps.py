import json
import unittest

from body_runtime_host.gps import VentunoBridgeGpsSource


class FakeBridge:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def connect(self, timeout):
        return True

    def call(self, method, timeout):
        self.calls.append(method)
        return json.dumps(self.payload)


class GpsTests(unittest.TestCase):
    def test_nmea_gga_is_parsed_as_fix_and_marks_d0_uart_connected(self):
        bridge = FakeBridge({
            "available": True,
            "transport": "Serial1_USART3_D0_D1",
            "baudrate": 38400,
            "bytes_received": 900,
            "valid_sentences": 12,
            "checksum_errors": 0,
            "sequence": 12,
            "latest_gga": "$GNGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,",
        })
        source = VentunoBridgeGpsSource(bridge_factory=lambda: bridge)

        sample = source.read()

        self.assertTrue(sample["connected"])
        self.assertTrue(sample["fix"])
        self.assertAlmostEqual(sample["latitude"], 48.1173)
        self.assertAlmostEqual(sample["longitude"], 11.5166667)
        self.assertEqual(sample["satellites"], 8)
        self.assertAlmostEqual(sample["altitude_m"], 545.4)
        self.assertEqual(bridge.calls, ["body_gps_read"])

    def test_valid_uart_stream_without_satellite_fix_is_not_reported_as_position(self):
        bridge = FakeBridge({
            "available": True,
            "latest_gga": "$GNGGA,123519,,,,,0,00,99.9,,,,,,",
            "valid_sentences": 4,
        })
        source = VentunoBridgeGpsSource(bridge_factory=lambda: bridge)

        sample = source.read()

        self.assertTrue(sample["connected"])
        self.assertFalse(sample["fix"])
        self.assertIsNone(sample["latitude"])
        self.assertIsNone(sample["longitude"])

    def test_uart_with_no_nmea_returns_error_and_preserves_diagnostics(self):
        bridge = FakeBridge({
            "available": False,
            "bytes_received": 250,
            "valid_sentences": 0,
            "checksum_errors": 3,
            "error": "waiting_for_fresh_gga",
        })
        source = VentunoBridgeGpsSource(bridge_factory=lambda: bridge)

        with self.assertRaises(TimeoutError):
            source.read()

        self.assertEqual(source.status()["diagnostic"]["checksum_errors"], 3)
        self.assertIn("waiting_for_fresh_gga", source.status()["last_error"])

    def test_firmware_reads_serial1_without_reusing_ld2450_uart7(self):
        from pathlib import Path

        sketch = (Path(__file__).resolve().parents[1] / "firmware" / "ventuno_sensor_bridge"
                  / "ventuno_sensor_bridge.ino").read_text(encoding="utf-8")

        self.assertIn("Serial1.begin(GPS_BAUD)", sketch)
        self.assertIn("Serial1.available()", sketch)
        self.assertIn('Bridge.provide_safe("body_gps_read"', sketch)
        self.assertIn('DT_NODELABEL(uart7)', sketch)
        self.assertIn("Serial1_USART3_D0_D1", sketch)
        self.assertIn("checksum_errors", sketch)
        self.assertIn("latest_gsv", sketch)
        self.assertIn("GPS_GSV_CAPACITY", sketch)

    def test_gsv_fragments_expose_per_satellite_cn0_and_sky_angles(self):
        bridge = FakeBridge({
            "available": True,
            "latest_gga": "$GNGGA,123519,4807.038,N,01131.000,E,1,05,0.9,545.4,M,46.9,M,,",
            "latest_gsv": [
                "$GPGSV,2,1,05,01,40,083,41,02,17,273,30,03,12,123,25,04,22,180,18",
                "$GPGSV,2,2,05,05,05,300,12",
            ],
        })

        sample = VentunoBridgeGpsSource(bridge_factory=lambda: bridge).read()

        self.assertEqual(sample["satellites_in_view"], 5)
        strongest = sample["satellite_signals"][0]
        self.assertEqual(strongest["svid"], 1)
        self.assertEqual(strongest["elevation_deg"], 40)
        self.assertEqual(strongest["azimuth_deg"], 83)
        self.assertEqual(strongest["cn0_db_hz"], 41.0)

    def test_gsv_empty_cn0_still_reports_satellites_in_view(self):
        bridge = FakeBridge({
            "available": True,
            "latest_gga": "$GNGGA,123519,4807.038,N,01131.000,E,1,05,0.9,545.4,M,46.9,M,,",
            "latest_gsv": ["$GNGSV,1,1,02,01,40,083,,02,17,273,,1"],
        })

        sample = VentunoBridgeGpsSource(bridge_factory=lambda: bridge).read()

        self.assertEqual(sample["satellites_in_view"], 2)
        self.assertEqual(len(sample["satellite_signals"]), 2)
        self.assertTrue(all(signal["cn0_db_hz"] is None for signal in sample["satellite_signals"]))

    def test_body_exposes_gps_diagnostic_endpoint_and_plugin_entry(self):
        from pathlib import Path

        runtime = (Path(__file__).resolve().parents[1] / "body_runtime_host" / "runtime.py")
        source = runtime.read_text(encoding="utf-8")

        self.assertIn('path == "/plugins/gps/status"', source)
        self.assertIn('"status_url": "/plugins/gps/status"', source)
        self.assertIn('"Serial1 USART3 · D0/D1 via Ventuno STM32 Bridge"', source)


if __name__ == "__main__":
    unittest.main()
