"""弹幕基类"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class BarrageMessage:
    """弹幕消息"""
    user: str              # 用户名
    text: str              # 弹幕内容
    timestamp: datetime = field(default_factory=datetime.now)
    msg_type: str = "text" # text / gift / enter / like
    extra: dict = field(default_factory=dict)

    def __str__(self):
        return f"[{self.user}]: {self.text}"


class BaseBarrage:
    """弹幕抓取基类"""

    def __init__(self, room_id: str, poll_interval: float = 1.0, max_queue: int = 50):
        self.room_id = room_id
        self.poll_interval = poll_interval
        self.queue: asyncio.Queue[BarrageMessage] = asyncio.Queue(maxsize=max_queue)
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def connect(self):
        """连接直播间"""
        raise NotImplementedError

    async def disconnect(self):
        """断开连接"""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _poll_loop(self):
        """轮询循环，子类实现 _fetch_messages"""
        while self._running:
            try:
                messages = await self._fetch_messages()
                for msg in messages:
                    if self.queue.full():
                        try:
                            self.queue.get_nowait()  # 丢弃最旧的
                        except asyncio.QueueEmpty:
                            pass
                    await self.queue.put(msg)
            except Exception as e:
                logger.error(f"弹幕获取失败: {e}")
            await asyncio.sleep(self.poll_interval)

    async def _fetch_messages(self) -> list[BarrageMessage]:
        """获取新弹幕，子类实现"""
        raise NotImplementedError

    async def get_message(self) -> Optional[BarrageMessage]:
        """获取一条弹幕（阻塞）"""
        try:
            return await asyncio.wait_for(self.queue.get(), timeout=self.poll_interval)
        except asyncio.TimeoutError:
            return None

    async def get_all_messages(self) -> list[BarrageMessage]:
        """获取所有待处理弹幕"""
        messages = []
        while not self.queue.empty():
            try:
                messages.append(self.queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        return messages
