<div align="center">

# 🎙️ Digital Human Live

**AI 数字人直播系统 · 弹幕互动 + 大模型回复 + TTS + 数字人驱动 + RTMP 推流**

<br>

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FFmpeg](https://img.shields.io/badge/FFmpeg-007808?style=for-the-badge&logo=ffmpeg&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)

<br>

弹幕实时抓取 → 大模型智能回复 → TTS 语音合成 → 数字人口型同步 → RTMP 推流

[系统架构](#系统架构) · [核心功能](#核心功能) · [快速启动](#快速启动) · [项目结构](#项目结构)

</div>

---

## 系统架构

```
弹幕抓取 → 大模型回复 → TTS 语音合成 → 数字人驱动 → RTMP 推流
  │            │             │              │            │
  ▼            ▼             ▼              ▼            ▼
抖音弹幕    DeepSeek      Edge-TTS      MuseTalk     FFmpeg
WebSocket   / OpenAI      CosyVoice    SadTalker    推流到
            / 通义千问     GPT-SoVITS                直播平台
```

---

## 核心功能

| 模块 | 功能 | 技术 |
|------|------|------|
| 🎯 弹幕互动 | 实时抓取直播间弹幕 | WebSocket / aiohttp |
| 🤖 智能回复 | 关键词匹配 + AI 大模型回复 | DeepSeek / OpenAI / 通义千问 |
| 🗣️ 语音合成 | 多引擎 TTS | Edge-TTS / CosyVoice / GPT-SoVITS |
| 👤 数字人驱动 | 口型同步视频生成 | MuseTalk / SadTalker |
| 📺 RTMP 推流 | 推流到任意直播平台 | FFmpeg |
| 📝 话术管理 | 自动欢迎、空闲话术、商品讲解 | 内置调度器 |

---

## 快速启动

```bash
git clone https://github.com/H1nk5/digital-human-live.git
cd digital-human-live

# 虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装 FFmpeg
# Windows: winget install ffmpeg
# macOS:   brew install ffmpeg
# Ubuntu:  sudo apt install ffmpeg
```

### 配置

编辑 `config.yaml`：

```yaml
llm:
  api_key: "your-api-key"
  model: "deepseek-chat"

live:
  room_id: "直播间ID"       # 留空则进入交互模式
  rtmp_url: "rtmp://..."
  rtmp_key: "your-stream-key"

human:
  engine: "musetalk"        # musetalk / simple
  face_image: "assets/avatar.png"

tts:
  engine: "edge-tts"        # edge-tts / cosyvoice / gpt-sovits
  voice: "zh-CN-XiaoyiNeural"
```

### 运行

```bash
python main.py -i           # 交互模式（手动输入模拟弹幕）
python main.py              # 自动模式（连接直播间）
python main.py -c config.yaml
```

---

## 项目结构

```
digital-human-live/
├── main.py                 # 主控入口
├── config.yaml             # 配置文件
├── barrage/                # 弹幕模块
│   └── douyin.py           # 抖音弹幕抓取
├── llm/chat.py             # 大模型调用
├── tts/                    # 语音合成
│   └── edge_tts.py         # Edge-TTS 实现
├── human/                  # 数字人驱动
│   └── musetalk_human.py   # MuseTalk 实现
├── stream/rtmp.py          # RTMP 推流
├── scripts/manager.py      # 话术管理
└── assets/                 # 素材（头像等）
```

---

## 开源许可

MIT © [H1nk5](https://github.com/H1nk5)
