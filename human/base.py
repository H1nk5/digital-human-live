"""数字人驱动基类"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class BaseHuman:
    """数字人驱动基类

    输入：音频文件路径
    输出：视频帧序列（numpy array）
    """

    def __init__(
        self,
        face_image: str,
        output_width: int = 1080,
        output_height: int = 1920,
        fps: int = 25,
    ):
        self.face_image = Path(face_image)
        self.output_width = output_width
        self.output_height = output_height
        self.fps = fps

    async def initialize(self):
        """初始化模型"""
        raise NotImplementedError

    async def generate(self, audio_path: str, output_path: Optional[str] = None) -> str:
        """根据音频生成数字人视频

        Args:
            audio_path: 音频文件路径
            output_path: 输出视频路径（可选）

        Returns:
            输出视频文件路径
        """
        raise NotImplementedError

    async def generate_frames(self, audio_path: str):
        """根据音频生成视频帧流（用于实时推流）

        Args:
            audio_path: 音频文件路径

        Yields:
            numpy array: BGR 格式的视频帧
        """
        raise NotImplementedError
