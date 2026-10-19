"""Deterministic JSONL barrage replay for rehearsals and regression tests."""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from .base import BaseBarrage, BarrageMessage


class ReplayBarrage(BaseBarrage):
    def __init__(self, replay_file, *, speed=1.0, **kwargs):
        super().__init__(room_id="replay", **kwargs)
        self.replay_file = Path(replay_file)
        self.speed = max(float(speed), 0.01)
        self.exhausted = False

    async def connect(self):
        if not self.replay_file.is_file():
            raise FileNotFoundError(f"弹幕回放文件不存在: {self.replay_file}")
        self._running = True
        self._task = asyncio.create_task(self._replay())

    async def _replay(self):
        try:
            for line_number, raw in enumerate(self.replay_file.read_text("utf-8").splitlines(), 1):
                if not self._running:
                    break
                if not raw.strip():
                    continue
                try:
                    item = json.loads(raw)
                    user = str(item.get("user", "观众")).strip() or "观众"
                    text = str(item["text"]).strip()
                    delay = max(float(item.get("delay", 0)), 0) / self.speed
                except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                    raise ValueError(f"回放文件第 {line_number} 行无效: {error}") from error
                if not text:
                    continue
                if delay:
                    await asyncio.sleep(delay)
                await self.queue.put(BarrageMessage(
                    user=user,
                    text=text,
                    timestamp=datetime.now(),
                    msg_type=str(item.get("msg_type", "text")),
                    extra={"replay_line": line_number},
                ))
        finally:
            self.exhausted = True
            self._running = False

    async def _fetch_messages(self):
        return []
