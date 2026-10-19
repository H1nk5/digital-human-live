"""Side-effect-free runtime readiness checks."""

import shutil
from pathlib import Path


def check_config(config, *, dry_run=False, replay_file=None):
    checks = []

    def add(name, ok, detail):
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    llm = config.get("llm", {})
    add("llm", dry_run or bool(str(llm.get("api_key", "")).strip()),
        "dry-run 不调用 LLM" if dry_run else "需要配置 llm.api_key")

    human = config.get("human", {})
    face = Path(human.get("face_image", "assets/avatar.png"))
    add("avatar", dry_run or face.is_file(), str(face))

    add("ffmpeg", dry_run or shutil.which("ffmpeg") is not None,
        "dry-run 不调用 FFmpeg" if dry_run else "需要在 PATH 中安装 ffmpeg")

    live = config.get("live", {})
    rtmp_url = str(live.get("rtmp_url", "")).strip()
    add("rtmp", not rtmp_url or rtmp_url.startswith(("rtmp://", "rtmps://")),
        "未配置时仅保存本地视频" if not rtmp_url else rtmp_url)

    if replay_file:
        path = Path(replay_file)
        add("replay", path.is_file(), str(path))
    elif live.get("room_id"):
        add("barrage", False, "抖音 protobuf 适配尚未完成，请使用 --replay 进行可靠验收")
    else:
        add("barrage", True, "交互模式")

    return {"ok": all(item["ok"] for item in checks), "checks": checks}
