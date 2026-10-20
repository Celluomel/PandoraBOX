import unittest

from body_runtime_host.battery_indicator import VentunoBatteryIndicator, estimated_level_percent


class FakeBridge:
    def __init__(self, connect=True):
        self.connect_result = connect
        self.calls = []

    def connect(self, timeout):
        return self.connect_result

    def call(self, method, *args, timeout):
        self.calls.append((method, args, timeout))
        return True


class BatteryIndicatorTests(unittest.TestCase):
    def test_estimated_level_is_clamped_and_rounded(self):
        self.assertEqual(estimated_level_percent(0, 99, 0.85), 100)
        self.assertEqual(estimated_level_percent(99, 99, 0.85), 0)
        self.assertEqual(estimated_level_percent(42.075, 99, 0.85), 50)

    def test_indicator_sends_only_changed_percent(self):
        bridge = FakeBridge()
        led_writes = []
        indicator = VentunoBatteryIndicator(bridge_factory=lambda: bridge,
                                            led_writer=lambda name, value: led_writes.append((name, value)))

        self.assertTrue(indicator.update(61))
        self.assertFalse(indicator.update(61))
        self.assertTrue(indicator.update(60))
        self.assertEqual([call[1] for call in bridge.calls], [(61,), (60,)])
        self.assertEqual(led_writes, [("red", 0), ("green", 255), ("blue", 0)])
        self.assertTrue(all(call[0] == "body_battery_indicator_set" for call in bridge.calls))

    def test_rgb_color_bands_and_unknown_level(self):
        writes = []
        indicator = VentunoBatteryIndicator(bridge_factory=lambda: FakeBridge(),
                                            led_writer=lambda name, value: writes.append((name, value)))
        indicator.update(50)
        self.assertEqual(writes[-3:], [("red", 255), ("green", 120), ("blue", 0)])
        indicator.update(20)
        self.assertEqual(writes[-3:], [("red", 255), ("green", 0), ("blue", 0)])
        indicator.update(None)
        self.assertEqual(writes[-3:], [("red", 0), ("green", 0), ("blue", 0)])

    def test_unknown_state_is_sent_as_minus_one(self):
        bridge = FakeBridge()
        indicator = VentunoBatteryIndicator(bridge_factory=lambda: bridge,
                                            led_writer=lambda _name, _value: None)
        self.assertTrue(indicator.update(None))
        self.assertEqual(bridge.calls[0][1], (-1,))

    def test_bridge_failures_are_rate_limited(self):
        now = [10.0]
        indicator = VentunoBatteryIndicator(bridge_factory=lambda: FakeBridge(False),
                                            clock=lambda: now[0], led_writer=lambda _name, _value: None)
        self.assertFalse(indicator.update(61))
        now[0] = 12.0
        self.assertFalse(indicator.update(61))
        now[0] = 15.1
        self.assertFalse(indicator.update(61))


if __name__ == "__main__":
    unittest.main()
