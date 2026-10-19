import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from main import DigitalHumanLive
from utils import format_duration, load_config
from barrage import ReplayBarrage
from preflight import check_config


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

    def test_dry_run_preflight_only_requires_replay_file(self):
        with tempfile.TemporaryDirectory() as directory:
            replay = Path(directory) / "messages.jsonl"
            replay.write_text('{"user":"测试","text":"多少钱"}\n', encoding="utf-8")
            result = check_config({"live": {}, "human": {}, "llm": {}}, dry_run=True, replay_file=replay)
            self.assertTrue(result["ok"])

    def test_real_room_is_rejected_until_adapter_is_complete(self):
        result = check_config(
            {"live": {"room_id": "123"}, "human": {}, "llm": {"api_key": "key"}},
            dry_run=False,
        )
        self.assertFalse(result["ok"])
        self.assertTrue(any(item["name"] == "barrage" and not item["ok"] for item in result["checks"]))

    def test_replay_preserves_order_and_metadata(self):
        async def scenario(path):
            source = ReplayBarrage(path, speed=1000, poll_interval=0.01)
            await source.connect()
            messages = []
            while not source.exhausted or not source.queue.empty():
                message = await source.get_message()
                if message:
                    messages.append(message)
            await source.disconnect()
            return messages

        with tempfile.TemporaryDirectory() as directory:
            replay = Path(directory) / "messages.jsonl"
            replay.write_text(
                "\n".join([
                    json.dumps({"user": "甲", "text": "多少钱", "delay": 0}, ensure_ascii=False),
                    json.dumps({"user": "乙", "text": "怎么买", "delay": 0}, ensure_ascii=False),
                ]),
                encoding="utf-8",
            )
            messages = asyncio.run(scenario(replay))
            self.assertEqual([(item.user, item.text) for item in messages], [("甲", "多少钱"), ("乙", "怎么买")])


if __name__ == "__main__":
    unittest.main()
