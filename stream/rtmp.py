"""RTMP 推流模块"""

import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class RTMPPusher:
    """FFmpeg RTMP 推流

    支持两种模式：
    1. 推送视频文件到 RTMP
    2. 管道模式：接收帧数据实时推流
    """

    def __init__(self, rtmp_url: str, rtmp_key: str = ""):
        self.rtmp_url = rtmp_url.rstrip("/")
        self.rtmp_key = rtmp_key
        self.full_url = f"{self.rtmp_url}/{self.rtmp_key}" if rtmp_key else rtmp_url
        self._process: Optional[asyncio.subprocess.Process] = None
        self._running = False

    async def push_file(self, video_path: str, loop: bool = False) -> bool:
        """推送视频文件到 RTMP

        Args:
            video_path: 视频文件路径
            loop: 是否循环播放
        """
        if not Path(video_path).exists():
            logger.error(f"视频文件不存在: {video_path}")
            return False

        cmd = ["ffmpeg", "-y"]
        if loop:
            cmd += ["-stream_loop", "-1"]
        cmd += [
            "-re",                          # 按原始速率发送
            "-i", video_path,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-c:a", "aac",
            "-b:a", "128k",
            "-f", "flv",
            self.full_url,
        ]

        try:
            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self._running = True
            logger.info(f"开始推流: {video_path} -> {self.full_url}")
            return True

        except Exception as e:
            logger.error(f"推流启动失败: {e}")
            return False

    async def push_pipe(self, width: int = 1080, height: int = 1920, fps: int = 25) -> bool:
        """管道模式推流（实时接收帧数据）"""
        cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-pix_fmt", "bgr24",
            "-s", f"{width}x{height}",
            "-r", str(fps),
            "-i", "pipe:0",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-f", "flv",
            self.full_url,
        ]

        try:
            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self._running = True
            logger.info(f"管道推流已启动: {width}x{height}@{fps}fps")
            return True

        except Exception as e:
            logger.error(f"管道推流启动失败: {e}")
            return False

    async def write_frame(self, frame_data: bytes):
        """写入一帧数据（管道模式）"""
        if self._process and self._process.stdin:
            try:
                self._process.stdin.write(frame_data)
                await self._process.stdin.drain()
            except Exception as e:
                logger.error(f"帧写入失败: {e}")

    async def push_with_audio(self, video_path: str, audio_path: str) -> bool:
        """推送视频+音频到 RTMP"""
        cmd = [
            "ffmpeg", "-y",
            "-re",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-c:a", "aac",
            "-b:a", "128k",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            "-f", "flv",
            self.full_url,
        ]

        try:
            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self._running = True
            logger.info(f"开始推流（视频+音频）: {video_path} + {audio_path}")
            return True

        except Exception as e:
            logger.error(f"推流启动失败: {e}")
            return False

    async def stop(self):
        """停止推流"""
        self._running = False
        if self._process:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._process.kill()
            except Exception as e:
                logger.error(f"停止推流异常: {e}")
            finally:
                self._process = None
        logger.info("推流已停止")

    @property
    def is_running(self) -> bool:
        return self._running and self._process is not None and self._process.returncode is None
