import unittest

from body_runtime_host.ventuno_gateway import VentunoGateway, validate_command


class VentunoGatewayTests(unittest.TestCase):
    def test_validates_only_robot_commands(self):
        self.assertEqual(validate_command({"type": "forward", "params": {}}), (True, ""))
        self.assertFalse(validate_command({"type": "shell"})[0])
        self.assertFalse(validate_command({"type": "forward", "params": []})[0])

    def test_gateway_requires_explicit_actuation(self):
        gateway = VentunoGateway("http://fnk0031.local:9100")
        with self.assertRaises(PermissionError):
            gateway.command({"type": "forward", "params": {}})

    def test_stop_is_always_forwardable_for_safety(self):
        gateway = VentunoGateway("http://fnk0031.local:9100")
        gateway.stop = lambda reason="": {"stopped": True, "reason": reason}
        self.assertEqual(gateway.command({"type": "stop"})["stopped"], True)


if __name__ == "__main__":
    unittest.main()
