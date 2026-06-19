"""数字人直播系统 - 主控入口

流程：弹幕抓取 → 大模型回复 → TTS 合成 → 数字人驱动 → RTMP 推流
"""

import argparse
import asyncio
import logging
import signal
import sys
import time
from pathlib import Path

from utils import load_config, setup_logging, format_duration

logger = logging.getLogger(__name__)


class DigitalHumanLive:
    """数字人直播主控"""

    def __init__(self, config: dict):
        self.config = config
        self._running = False
        self._start_time = 0.0

        # 模块（延迟初始化）
        self.barrage = None
        self.llm = None
        self.tts = None
        self.human = None
        self.stream = None
        self.scripts = None

    async def initialize(self):
        """初始化所有模块"""
        logger.info("=" * 50)
        logger.info("数字人直播系统启动中...")
        logger.info("=" * 50)

        # 1. 初始化话术管理
        from scripts import ScriptManager
        self.scripts = ScriptManager(self.config.get("scripts", {}))
        logger.info("[1/5] 话术管理器就绪")

        # 2. 初始化大模型
        from llm import LLMChat
        llm_cfg = self.config.get("llm", {})
        self.llm = LLMChat(
            api_key=llm_cfg.get("api_key", ""),
            base_url=llm_cfg.get("base_url", "https://api.deepseek.com"),
            model=llm_cfg.get("model", "deepseek-chat"),
            max_tokens=llm_cfg.get("max_tokens", 200),
            temperature=llm_cfg.get("temperature", 0.8),
            system_prompt=llm_cfg.get("system_prompt", "你是一个直播带货助手。"),
        )
        logger.info(f"[2/5] 大模型就绪 ({llm_cfg.get('model', 'deepseek-chat')})")

        # 3. 初始化 TTS
        tts_cfg = self.config.get("tts", {})
        engine = tts_cfg.get("engine", "edge-tts")
        if engine == "edge-tts":
            from tts import EdgeTTS
            self.tts = EdgeTTS(
                voice=tts_cfg.get("voice", "zh-CN-XiaoyiNeural"),
                rate=tts_cfg.get("rate", "+0%"),
                volume=tts_cfg.get("volume", "+0%"),
            )
        else:
            logger.warning(f"TTS 引擎 {engine} 暂未实现，使用 edge-tts")
            from tts import EdgeTTS
            self.tts = EdgeTTS()
        logger.info(f"[3/5] TTS 就绪 ({engine})")

        # 4. 初始化数字人
        human_cfg = self.config.get("human", {})
        human_engine = human_cfg.get("engine", "simple")
        if human_engine == "musetalk":
            from human import MuseTalkHuman
            self.human = MuseTalkHuman(
                face_image=human_cfg.get("face_image", "assets/avatar.png"),
                musetalk_path=human_cfg.get("musetalk_path", "../MuseTalk"),
                version=human_cfg.get("musetalk_version", "v15"),
                output_width=human_cfg.get("output_width", 1080),
                output_height=human_cfg.get("output_height", 1920),
                fps=human_cfg.get("output_fps", 25),
            )
        else:
            from human.musetalk_human import SimpleHuman
            self.human = SimpleHuman(
                face_image=human_cfg.get("face_image", "assets/avatar.png"),
                output_width=human_cfg.get("output_width", 1080),
                output_height=human_cfg.get("output_height", 1920),
                fps=human_cfg.get("output_fps", 25),
            )

        init_ok = await self.human.initialize()
        if not init_ok:
            logger.warning("数字人初始化失败，将使用简单模式")
            from human.musetalk_human import SimpleHuman
            self.human = SimpleHuman(
                face_image=human_cfg.get("face_image", "assets/avatar.png"),
            )
            await self.human.initialize()
        logger.info(f"[4/5] 数字人就绪 ({human_engine})")

        # 5. 初始化推流
        live_cfg = self.config.get("live", {})
        rtmp_url = live_cfg.get("rtmp_url", "")
        rtmp_key = live_cfg.get("rtmp_key", "")
        if rtmp_url:
            from stream import RTMPPusher
            self.stream = RTMPPusher(rtmp_url, rtmp_key)
            logger.info(f"[5/5] 推流就绪 ({rtmp_url})")
        else:
            logger.info("[5/5] 推流未配置，视频将保存到本地")

        # 6. 初始化弹幕
        barrage_cfg = self.config.get("barrage", {})
        platform = live_cfg.get("platform", "douyin")
        room_id = live_cfg.get("room_id", "")

        if room_id:
            from barrage import DouyinBarrage
            self.barrage = DouyinBarrage(
                room_id=room_id,
                poll_interval=barrage_cfg.get("poll_interval", 1.0),
            )
            await self.barrage.connect()
            logger.info(f"弹幕已连接 ({platform} 房间: {room_id})")
        else:
            logger.info("未配置直播间 ID，进入演示模式（手动输入）")

        logger.info("=" * 50)
        logger.info("系统初始化完成！")
        logger.info("=" * 50)

    async def run(self):
        """主循环"""
        self._running = True
        self._start_time = time.time()

        while self._running:
            try:
                # 获取弹幕
                msg = None
                if self.barrage:
                    msg = await self.barrage.get_message()

                # 处理弹幕或空闲话术
                reply = None
                if msg:
                    logger.info(f"[弹幕] {msg.user}: {msg.text}")

                    # 1. 先检查关键词
                    reply = self.scripts.check_keyword(msg.text)

                    # 2. 没匹配关键词就问大模型
                    if not reply:
                        reply = await self.llm.chat(msg.text, msg.user)

                    # 3. 检查是否是新人（欢迎）
                    # （简化处理，实际可以用 Set 记录已欢迎的用户）
                else:
                    # 没弹幕，检查空闲话术
                    reply = self.scripts.get_idle_script()

                if reply:
                    await self._speak(reply)

                # 短暂等待避免 CPU 空转
                await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"主循环异常: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def _speak(self, text: str):
        """完整播报流程：TTS → 数字人 → 推流"""
        try:
            # 1. TTS 合成
            logger.info(f"[播报] {text}")
            audio_path = await self.tts.synthesize(text)
            if not audio_path:
                logger.error("TTS 合成失败")
                return

            # 2. 数字人生成视频
            video_path = await self.human.generate(audio_path)
            if not video_path:
                logger.error("数字人视频生成失败")
                return

            # 3. 推流或保存
            if self.stream:
                await self.stream.push_with_audio(video_path, audio_path)
                # 等待播放完成
                await asyncio.sleep(self._estimate_duration(text))
                await self.stream.stop()
            else:
                logger.info(f"视频已保存: {video_path}")

        except Exception as e:
            logger.error(f"播报失败: {e}", exc_info=True)

    def _estimate_duration(self, text: str) -> float:
        """估算语音时长（秒）"""
        # 中文大约 4 字/秒
        return max(len(text) / 4.0, 2.0)

    async def stop(self):
        """停止系统"""
        logger.info("正在停止系统...")
        self._running = False

        if self.barrage:
            await self.barrage.disconnect()
        if self.stream:
            await self.stream.stop()

        duration = time.time() - self._start_time
        logger.info(f"系统已停止，运行时长: {format_duration(duration)}")


async def interactive_mode(live: DigitalHumanLive):
    """交互模式（无直播间时使用）"""
    print("\n" + "=" * 50)
    print("  数字人直播 - 交互模式")
    print("  输入文字模拟弹幕，输入 q 退出")
    print("=" * 50 + "\n")

    loop = asyncio.get_event_loop()

    while live._running:
        try:
            # 在线程中读取输入，不阻塞事件循环
            text = await loop.run_in_executor(None, lambda: input("模拟弹幕 > "))

            if text.strip().lower() in ("q", "quit", "exit"):
                break

            if not text.strip():
                continue

            # 检查关键词
            reply = live.scripts.check_keyword(text)
            if not reply:
                reply = await live.llm.chat(text, "测试用户")

            print(f"  回复: {reply}\n")
            await live._speak(reply)

        except (EOFError, KeyboardInterrupt):
            break


async def main():
    parser = argparse.ArgumentParser(description="数字人直播系统")
    parser.add_argument("-c", "--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("-i", "--interactive", action="store_true", help="交互模式")
    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)
    setup_logging(config)

    # 创建系统
    live = DigitalHumanLive(config)

    # 信号处理
    def signal_handler(sig, frame):
        logger.info("收到退出信号")
        asyncio.get_event_loop().create_task(live.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await live.initialize()

        if args.interactive or not config.get("live", {}).get("room_id"):
            # 交互模式
            await interactive_mode(live)
        else:
            # 自动模式
            await live.run()

    except KeyboardInterrupt:
        pass
    finally:
        await live.stop()


if __name__ == "__main__":
    asyncio.run(main())
