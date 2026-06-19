"""MuseTalk 数字人驱动

MuseTalk 是腾讯开源的实时数字人驱动模型，
输入一个人脸视频 + 一段音频，输出口型同步的视频。
"""

import asyncio
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
import yaml

from .base import BaseHuman

logger = logging.getLogger(__name__)


class MuseTalkHuman(BaseHuman):
    """MuseTalk 数字人驱动

    调用 MuseTalk 的推理脚本生成口型同步的数字人视频。
    """

    def __init__(
        self,
        face_image: str,
        musetalk_path: str = "../MuseTalk",
        version: str = "v15",
        output_width: int = 1080,
        output_height: int = 1920,
        fps: int = 25,
    ):
        super().__init__(face_image, output_width, output_height, fps)
        self.musetalk_path = Path(musetalk_path).resolve()
        self.version = version  # v10 or v15
        self._initialized = False
        self._face_video: Optional[str] = None

    async def initialize(self):
        """初始化 MuseTalk 环境"""
        # 检查 MuseTalk 目录
        if not self.musetalk_path.exists():
            logger.error(f"MuseTalk 目录不存在: {self.musetalk_path}")
            return False

        # 检查模型权重
        if self.version == "v15":
            model_path = self.musetalk_path / "models" / "musetalkV15" / "unet.pth"
        else:
            model_path = self.musetalk_path / "models" / "musetalk" / "pytorch_model.bin"

        if not model_path.exists():
            logger.error(f"模型权重不存在: {model_path}")
            return False

        # 将静态图片转为视频（MuseTalk 需要视频输入）
        if str(self.face_image).endswith((".png", ".jpg", ".jpeg")):
            self._face_video = await self._image_to_video(str(self.face_image))
        else:
            self._face_video = str(self.face_image)

        self._initialized = True
        logger.info(f"MuseTalk {self.version} 初始化完成")
        return True

    async def _image_to_video(self, image_path: str) -> str:
        """将静态图片转为视频（MuseTalk 需要视频输入）"""
        output = Path(image_path).with_suffix(".mp4")
        if output.exists():
            return str(output)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", image_path,
            "-c:v", "libx264",
            "-t", "10",
            "-pix_fmt", "yuv420p",
            "-vf", f"scale=512:512:force_original_aspect_ratio=decrease,pad=512:512:(ow-iw)/2:(oh-ih)/2",
            "-r", str(self.fps),
            str(output),
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await process.communicate()

        if process.returncode != 0:
            logger.error("图片转视频失败")
            return ""

        logger.info(f"图片已转为视频: {output}")
        return str(output)

    async def generate(self, audio_path: str, output_path: Optional[str] = None) -> str:
        """生成数字人视频"""
        if not self._initialized:
            logger.error("MuseTalk 未初始化")
            return ""

        if not output_path:
            output_path = f"output/human_{Path(audio_path).stem}.mp4"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # 创建临时配置文件
        config_path = await self._create_config(audio_path)
        if not config_path:
            return ""

        # 构建推理命令
        if self.version == "v15":
            unet_model = str(self.musetalk_path / "models" / "musetalkV15" / "unet.pth")
            unet_config = str(self.musetalk_path / "models" / "musetalkV15" / "musetalk.json")
            version_arg = "v15"
        else:
            unet_model = str(self.musetalk_path / "models" / "musetalk" / "pytorch_model.bin")
            unet_config = str(self.musetalk_path / "models" / "musetalk" / "musetalk.json")
            version_arg = "v1"

        result_dir = str(self.musetalk_path / "results" / "live")

        # 使用 MuseTalk 的 Python 3.10 虚拟环境
        musetalk_python = str(self.musetalk_path / ".venv" / "Scripts" / "python.exe")
        if not Path(musetalk_python).exists():
            musetalk_python = "python"  # fallback

        cmd = [
            musetalk_python, "-m", "scripts.inference",
            "--inference_config", config_path,
            "--result_dir", result_dir,
            "--unet_model_path", unet_model,
            "--unet_config", unet_config,
            "--version", version_arg,
        ]

        logger.info(f"MuseTalk 开始生成: {audio_path}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.musetalk_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"MuseTalk 推理失败: {stderr.decode(errors='replace')[-500:]}")
                return ""

            # 查找输出文件（MuseTalk 输出格式：{video_name}_{audio_name}.mp4）
            # MuseTalk 输出到 {result_dir}/v15/ 目录下
            result_path = Path(result_dir) / version_arg
            if not result_path.exists():
                result_path = Path(result_dir)

            # 等待文件写入完成
            await asyncio.sleep(1)

            videos = sorted(result_path.rglob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
            if videos:
                # 复制到目标路径
                import shutil
                shutil.copy2(str(videos[0]), output_path)
                logger.info(f"数字人视频生成完成: {output_path}")
                return output_path
            else:
                logger.error(f"未找到输出视频，检查目录: {result_path}")
                return ""

        except Exception as e:
            logger.error(f"MuseTalk 执行异常: {e}")
            return ""

    async def _create_config(self, audio_path: str) -> str:
        """创建 MuseTalk 推理配置"""
        if not self._face_video:
            return ""

        config = {
            "task_0": {
                "video_path": os.path.abspath(self._face_video),
                "audio_path": os.path.abspath(audio_path),
            }
        }

        config_path = str(self.musetalk_path / "configs" / "inference" / "live_config.yaml")
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True)

        return config_path


class SimpleHuman(BaseHuman):
    """简单数字人（不需要 GPU）

    用静态图片 + 音频合成视频，效果一般但不需要 GPU。
    适合快速验证流程。
    """

    async def initialize(self):
        logger.info("SimpleHuman 初始化完成（静态图片模式）")
        return True

    async def generate(self, audio_path: str, output_path: Optional[str] = None) -> str:
        """用 FFmpeg 将静态图片 + 音频合成视频"""
        if not output_path:
            output_path = f"output/human_{Path(audio_path).stem}.mp4"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(self.face_image),
            "-i", audio_path,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-vf", f"scale={self.output_width}:{self.output_height}:force_original_aspect_ratio=decrease,pad={self.output_width}:{self.output_height}:(ow-iw)/2:(oh-ih)/2",
            "-shortest",
            output_path,
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"FFmpeg 合成失败: {stderr.decode()}")
                return ""

            return output_path

        except Exception as e:
            logger.error(f"视频合成异常: {e}")
            return ""
