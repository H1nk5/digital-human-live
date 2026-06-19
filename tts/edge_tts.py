"""Edge TTS 语音合成（微软免费 TTS）"""

import logging
from pathlib import Path
from typing import Optional

import edge_tts

from .base import BaseTTS

logger = logging.getLogger(__name__)


class EdgeTTS(BaseTTS):
    """Edge TTS 语音合成

    免费、高质量、支持中文多音色。
    音色列表：edge-tts --list-voices
    """

    VOICES = {
        "xiaoyi": "zh-CN-XiaoyiNeural",      # 女声，温柔
        "xiaoxiao": "zh-CN-XiaoxiaoNeural",  # 女声，活泼
        "yunxi": "zh-CN-YunxiNeural",        # 男声，阳光
        "yunjian": "zh-CN-YunjianNeural",    # 男声，沉稳
        "yunxia": "zh-CN-YunxiaNeural",      # 男声，少年
        "xiaomeng": "zh-CN-XiaomengNeural",  # 女声，甜萌
        "xiaochen": "zh-CN-XiaochenNeural",  # 女声，知性
    }

    def __init__(
        self,
        voice: str = "zh-CN-XiaoyiNeural",
        rate: str = "+0%",
        volume: str = "+0%",
        output_dir: str = "output/audio",
    ):
        super().__init__(output_dir)
        # 支持简称映射
        self.voice = self.VOICES.get(voice, voice)
        self.rate = rate
        self.volume = volume

    async def synthesize(self, text: str, output_path: Optional[str] = None) -> str:
        """合成语音并保存为 mp3"""
        if not output_path:
            output_path = str(self._next_path(".mp3"))

        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            volume=self.volume,
        )
        await communicate.save(output_path)

        logger.debug(f"TTS 合成完成: {output_path} ({len(text)} 字)")
        return output_path

    async def synthesize_stream(self, text: str):
        """流式合成，返回音频数据块迭代器"""
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            volume=self.volume,
        )
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]
