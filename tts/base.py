"""TTS 基类"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class BaseTTS:
    """语音合成基类"""

    def __init__(self, output_dir: str = "output/audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._counter = 0

    def _next_path(self, suffix: str = ".wav") -> Path:
        """生成下一个音频文件路径"""
        self._counter += 1
        return self.output_dir / f"tts_{self._counter:06d}{suffix}"

    async def synthesize(self, text: str, output_path: Optional[str] = None) -> str:
        """合成语音，返回音频文件路径"""
        raise NotImplementedError

    async def synthesize_to_bytes(self, text: str) -> bytes:
        """合成语音，返回音频字节数据"""
        path = await self.synthesize(text)
        with open(path, "rb") as f:
            return f.read()
