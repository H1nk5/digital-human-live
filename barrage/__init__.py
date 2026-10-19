from .base import BarrageMessage, BaseBarrage
from .replay import ReplayBarrage

__all__ = ["BarrageMessage", "BaseBarrage", "DouyinBarrage", "ReplayBarrage"]


def __getattr__(name):
    if name == "DouyinBarrage":
        from .douyin import DouyinBarrage

        return DouyinBarrage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
