import unittest

from body_runtime_host.midas_service import MiDaSDepthService


class MiDaSDepthServiceTests(unittest.TestCase):
    def test_service_is_opt_in_and_reports_relative_depth(self):
        values = {"BODY_MIDAS_ENABLED": False, "BODY_MIDAS_INTERVAL_S": 2.0}
        service = MiDaSDepthService(lambda key, default: values.get(key, default), lambda: {})

        service.start()

        self.assertEqual(service.status()["state"], "disabled")
        self.assertEqual(service.settings()["depth_type"], "relative")
        self.assertEqual(service.settings()["model"], "DPT_SwinV2_T_256")

    def test_inference_interval_is_bounded(self):
        values = {"BODY_MIDAS_ENABLED": False, "BODY_MIDAS_INTERVAL_S": 0.1}
        service = MiDaSDepthService(lambda key, default: values.get(key, default), lambda: {})

        self.assertEqual(service.settings()["interval_s"], 1.0)


if __name__ == "__main__":
    unittest.main()
