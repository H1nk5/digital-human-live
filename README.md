# 🎙️ 数字人直播系统

AI 驱动的数字人直播系统，支持弹幕实时互动、大模型智能回复、TTS 语音合成、数字人视频生成和 RTMP 推流。

## 📐 系统架构

```
弹幕抓取 → 大模型回复 → TTS 语音合成 → 数字人驱动 → RTMP 推流
  │            │             │              │            │
  ▼            ▼             ▼              ▼            ▼
抖音弹幕    DeepSeek      Edge-TTS      MuseTalk     FFmpeg
WebSocket   / OpenAI      CosyVoice    SadTalker    推流到
            / 通义千问     GPT-SoVITS                直播平台
```

## ✨ 核心功能

- 🎯 **弹幕互动** — 实时抓取抖音直播间弹幕
- 🤖 **智能回复** — DeepSeek / OpenAI 兼容大模型，支持关键词匹配 + AI 回复
- 🗣️ **语音合成** — Edge-TTS（免费）/ CosyVoice / GPT-SoVITS 多引擎
- 👤 **数字人驱动** — MuseTalk 口型同步 / Simple 简单模式
- 📺 **RTMP 推流** — FFmpeg 推流到任意直播平台
- 📝 **话术管理** — 自动欢迎、空闲话术、商品讲解
- 🎮 **交互模式** — 无直播间时手动输入模拟弹幕

## 🛠️ 技术栈

| 模块 | 技术 |
|------|------|
| 大模型 | DeepSeek / OpenAI 兼容 API |
| TTS | Edge-TTS / CosyVoice / GPT-SoVITS |
| 数字人 | MuseTalk / SadTalker |
| 弹幕抓取 | WebSocket / aiohttp |
| 推流 | FFmpeg + RTMP |
| 异步框架 | Python asyncio |

## 📦 安装

```bash
# 克隆项目
git clone https://github.com/H1nk5/digital-human-live.git
cd digital-human-live

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装 FFmpeg（推流需要）
# Windows: winget install ffmpeg
# macOS:  brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
```

## ⚙️ 配置

编辑 `config.yaml`：

```yaml
# 大模型配置
llm:
  api_key: "your-api-key"       # DeepSeek / OpenAI API Key
  model: "deepseek-chat"        # 模型名称

# 直播间配置
live:
  platform: "douyin"
  room_id: "你的直播间ID"       # 留空则进入交互模式
  rtmp_url: "rtmp://..."        # RTMP 推流地址
  rtmp_key: "your-stream-key"

# 数字人配置
human:
  engine: "musetalk"            # musetalk / simple
  face_image: "assets/avatar.png"

# TTS 配置
tts:
  engine: "edge-tts"            # edge-tts / cosyvoice / gpt-sovits
  voice: "zh-CN-XiaoyiNeural"
```

## 🚀 运行

```bash
# 交互模式（手动输入模拟弹幕）
python main.py -i

# 自动模式（连接直播间）
python main.py

# 指定配置文件
python main.py -c my_config.yaml
```

### MuseTalk 数字人（可选）

如需使用 MuseTalk 驱动数字人，需额外安装：

```bash
# 克隆 MuseTalk
git clone https://github.com/TMElyralab/MuseTalk.git ../MuseTalk
cd ../MuseTalk
bash download_weights.sh
```

## 📁 项目结构

```
digital-human-live/
├── main.py                 # 主控入口
├── config.yaml             # 配置文件
├── requirements.txt        # Python 依赖
├── start.bat / start.sh    # 启动脚本
├── barrage/                # 弹幕模块
│   ├── base.py             # 弹幕基类
│   └── douyin.py           # 抖音弹幕抓取
├── llm/                    # 大模型模块
│   └── chat.py             # OpenAI 兼容 API 调用
├── tts/                    # 语音合成模块
│   ├── base.py             # TTS 基类
│   └── edge_tts.py         # Edge-TTS 实现
├── human/                  # 数字人模块
│   ├── base.py             # 数字人基类
│   └── musetalk_human.py   # MuseTalk 实现
├── stream/                 # 推流模块
│   └── rtmp.py             # RTMP 推流
├── scripts/                # 话术管理
│   └── manager.py          # 话术调度
├── assets/                 # 素材（头像等）
└── output/                 # 输出（音频/视频/日志）
```

## 📄 License

MIT
