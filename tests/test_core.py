import tempfile
import unittest
from pathlib import Path

from main import DigitalHumanLive
from utils import format_duration, load_config


class UtilityTests(unittest.TestCase):
    def test_duration_format(self):
        self.assertEqual(format_duration(65), "01:05")
        self.assertEqual(format_duration(3661), "1:01:01")

    def test_config_must_be_a_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text("- not\n- a\n- mapping\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "顶层必须是对象"):
                load_config(path)
            path.write_text("", encoding="utf-8")
            self.assertEqual(load_config(path), {})

    def test_speech_duration_has_a_floor(self):
        live = DigitalHumanLive({})
        self.assertEqual(live._estimate_duration("短"), 2.0)
        self.assertEqual(live._estimate_duration("测试文本" * 4), 4.0)


if __name__ == "__main__":
    unittest.main()
