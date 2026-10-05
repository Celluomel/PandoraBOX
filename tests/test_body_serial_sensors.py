import unittest

from body_runtime_host.sensor_serial import (
    extract_ld2450_frames,
    parse_ld2450_frame,
    parse_nmea_sentence,
)


class LD2450DecoderTests(unittest.TestCase):
    def test_decodes_signed_metric_target_and_ignores_empty_slots(self):
        # Official manual example: x=-782 mm, y=+1713 mm, speed=-16 cm/s.
        frame = bytes.fromhex(
            "AA FF 03 00 0E 03 B1 86 10 00 40 01 "
            "00 00 00 00 00 00 00 00 "
            "00 00 00 00 00 00 00 00 55 CC"
        )
        decoded = parse_ld2450_frame(frame, timestamp=123.0)
        self.assertEqual(decoded["timestamp"], 123.0)
        self.assertEqual(len(decoded["targets"]), 1)
        target = decoded["targets"][0]
        self.assertEqual(target["position_m"], [-0.782, 1.713, 0.0])
        self.assertEqual(target["velocity_mps"], [-0.16, 0.0, 0.0])
        self.assertEqual(target["distance_gate_m"], 0.32)

    def test_stream_extractor_handles_noise_split_frames_and_bad_tail(self):
        frame = bytes.fromhex("AA FF 03 00") + bytes(24) + bytes.fromhex("55 CC")
        buffer = bytearray(b"noise" + frame[:11])
        self.assertEqual(extract_ld2450_frames(buffer), [])
        buffer.extend(frame[11:] + frame)
        self.assertEqual(extract_ld2450_frames(buffer), [frame, frame])
        self.assertEqual(buffer, bytearray())

    def test_rejects_invalid_frame(self):
        with self.assertRaises(ValueError):
            parse_ld2450_frame(bytes(30))


class NmeaDecoderTests(unittest.TestCase):
    def test_parses_checksum_verified_gga_and_rmc(self):
        gga = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
        fix = parse_nmea_sentence(gga, timestamp=10.0)
        self.assertIsNotNone(fix)
        self.assertAlmostEqual(fix.latitude_deg, 48.1173, places=5)
        self.assertAlmostEqual(fix.longitude_deg, 11.5166667, places=5)
        self.assertEqual(fix.altitude_m, 545.4)
        self.assertEqual(fix.satellites, 8)

        rmc = "$GPRMC,123519,A,4807.038,N,01131.000,E,10.0,84.4,230394,003.1,W*6F"
        motion = parse_nmea_sentence(rmc, timestamp=11.0)
        self.assertIsNotNone(motion)
        self.assertAlmostEqual(motion.speed_mps, 5.14444, places=4)
        self.assertAlmostEqual(motion.course_deg, 84.4)

    def test_rejects_bad_checksum_and_no_fix(self):
        self.assertIsNone(parse_nmea_sentence("$GPGGA,123519,,,,,0,00,99.9,,,,,,*48"))
        self.assertIsNone(parse_nmea_sentence("$GPRMC,123519,V,,,,,,,230394,,,N*53"))


if __name__ == "__main__":
    unittest.main()
