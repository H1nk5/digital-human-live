"""抖音直播弹幕抓取（WebSocket 协议）"""

import asyncio
import json
import logging
import re
import time
from typing import Optional

import aiohttp

from .base import BaseBarrage, BarrageMessage

logger = logging.getLogger(__name__)


class DouyinBarrage(BaseBarrage):
    """抖音直播弹幕抓取

    通过解析抖音直播网页获取 WebSocket 弹幕地址，
    然后用 WebSocket 接收实时弹幕。
    """

    # 抖音直播网页 API
    LIVE_INFO_URL = "https://live.douyin.com/webcast/room/web/enter/"
    WEBSOCKET_URL = "wss://webcast5-ws-web-lf.douyin.com/webcast/im/push/v2/"

    def __init__(self, room_id: str, **kwargs):
        super().__init__(room_id, **kwargs)
        self._session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._cookie = ""
        self._ttwid = ""

    async def connect(self):
        """连接抖音直播间"""
        self._session = aiohttp.ClientSession()
        self._running = True

        # 获取 ttwid cookie
        await self._get_ttwid()

        # 获取直播间信息和 WebSocket 地址
        ws_url = await self._get_ws_url()
        if not ws_url:
            logger.error("获取 WebSocket 地址失败，请检查 room_id")
            return

        # 连接 WebSocket
        try:
            self._ws = await self._session.ws_connect(
                ws_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Cookie": self._cookie,
                },
            )
            logger.info(f"已连接抖音直播间: {self.room_id}")
            self._task = asyncio.create_task(self._ws_loop())
        except Exception as e:
            logger.error(f"WebSocket 连接失败: {e}")

    async def disconnect(self):
        """断开连接"""
        await super().disconnect()
        if self._ws:
            await self._ws.close()
        if self._session:
            await self._session.close()

    async def _get_ttwid(self):
        """获取 ttwid cookie"""
        try:
            async with self._session.get(
                "https://live.douyin.com/",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            ) as resp:
                for cookie in self._session.cookie_jar:
                    if cookie.key == "ttwid":
                        self._ttwid = cookie.value
                        self._cookie = f"ttwid={cookie.value}"
                        break
        except Exception as e:
            logger.warning(f"获取 ttwid 失败: {e}")

    async def _get_ws_url(self) -> Optional[str]:
        """获取 WebSocket 推送地址"""
        try:
            params = {
                "aid": "6383",
                "app_name": "douyin_web",
                "live_id": "1",
                "device_platform": "web",
                "language": "zh-CN",
                "browser_language": "zh-CN",
                "browser_platform": "Win32",
                "browser_name": "Chrome",
                "browser_version": "120.0.0.0",
                "web_rid": self.room_id,
            }
            async with self._session.get(
                self.LIVE_INFO_URL,
                params=params,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Cookie": self._cookie,
                    "Referer": f"https://live.douyin.com/{self.room_id}",
                },
            ) as resp:
                data = await resp.json()
                if data.get("status_code") == 0:
                    room_data = data.get("data", {})
                    # 从返回数据中提取 WebSocket 参数
                    # 实际实现需要解析 protobuf 协议
                    # 这里提供简化版的轮询方案作为备选
                    return None
        except Exception as e:
            logger.error(f"获取直播间信息失败: {e}")
        return None

    async def _ws_loop(self):
        """WebSocket 消息循环"""
        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.BINARY:
                    self._parse_message(msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket 错误: {self._ws.exception()}")
                    break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"WebSocket 循环异常: {e}")

    def _parse_message(self, data: bytes):
        """解析 protobuf 消息（简化版）"""
        try:
            # 抖音弹幕用 protobuf 编码
            # 这里用文本匹配做简化处理
            text = data.decode("utf-8", errors="ignore")

            # 匹配弹幕内容（简化版正则）
            # 正式版需要用 protobuf 解析 douyin 的 PushMessage 结构
            chat_patterns = [
                r'"content"\s*:\s*"([^"]+)".*"user"\s*:.*?"nickname"\s*:\s*"([^"]+)"',
                r'"nickname"\s*:\s*"([^"]+)".*"content"\s*:\s*"([^"]+)"',
            ]
            for pattern in chat_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    user, content = match[1], match[0] if len(match[0]) > len(match[1]) else match
                    if len(content) > 1 and len(content) < 100:
                        msg = BarrageMessage(user=user, text=content)
                        if not self.queue.full():
                            self.queue.put_nowait(msg)
        except Exception:
            pass  # 忽略解析失败的消息

    async def _fetch_messages(self) -> list[BarrageMessage]:
        """获取新弹幕（轮询模式备选）"""
        # 如果 WebSocket 连接成功，消息通过 _ws_loop 自动入队
        # 这里只是把队列中的消息返回
        messages = []
        while not self.queue.empty():
            try:
                messages.append(self.queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        return messages

    async def poll_web_page(self) -> list[BarrageMessage]:
        """网页轮询模式（备选方案，当 WebSocket 不可用时）"""
        messages = []
        try:
            async with self._session.get(
                f"https://live.douyin.com/{self.room_id}",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Cookie": self._cookie,
                },
            ) as resp:
                html = await resp.text()
                # 从页面中提取弹幕数据
                # 抖音页面会内嵌 JSON 数据
                pattern = r'"chat"\s*:\s*\[(.*?)\]'
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    try:
                        chats = json.loads(f"[{match.group(1)}]")
                        for chat in chats:
                            user = chat.get("user", {}).get("nickname", "未知用户")
                            text = chat.get("content", "")
                            if text:
                                messages.append(BarrageMessage(user=user, text=text))
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            logger.error(f"网页轮询失败: {e}")
        return messages
