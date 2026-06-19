"""直播话术管理器"""

import logging
import random
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Product:
    """商品信息"""
    id: str
    name: str
    price: str
    description: str
    selling_points: list[str] = field(default_factory=list)


class ScriptManager:
    """直播话术管理

    功能：
    - 自动欢迎话术
    - 空闲话术轮播
    - 商品讲解话术
    - 关键词触发回复
    """

    def __init__(self, config: dict):
        self.config = config

        # 欢迎话术
        self.welcome_template = config.get("welcome_template", "欢迎 {user} 来到直播间！")
        self.welcome_enabled = config.get("welcome_enabled", True)

        # 空闲话术
        self.idle_enabled = config.get("idle_enabled", True)
        self.idle_interval = config.get("idle_interval", 30)
        self.idle_scripts = config.get("idle_scripts", [
            "欢迎新来的宝宝们，喜欢的点点关注不迷路~",
            "今天给大家带来超值好物，有什么想看的可以扣在公屏上哦~",
            "关注主播不迷路，主播带你上高速！",
        ])
        self._last_idle_time = 0.0
        self._idle_index = 0

        # 商品列表
        self.products: dict[str, Product] = {}
        self.current_product: Optional[Product] = None

        # 关键词映射
        self.keyword_handlers: dict[str, callable] = {}
        self._setup_keywords()

    def _setup_keywords(self):
        """设置关键词处理"""
        self.keyword_handlers = {
            "多少钱": self._handle_price,
            "价格": self._handle_price,
            "怎么买": self._handle_buy,
            "购买": self._handle_buy,
            "链接": self._handle_buy,
            "下单": self._handle_buy,
            "有什么": self._handle_products,
            "推荐": self._handle_products,
        }

    def add_product(self, product: Product):
        """添加商品"""
        self.products[product.id] = product
        logger.info(f"添加商品: {product.name} (ID: {product.id})")

    def set_current_product(self, product_id: str) -> bool:
        """设置当前讲解的商品"""
        if product_id in self.products:
            self.current_product = self.products[product_id]
            return True
        return False

    def get_welcome(self, user: str) -> Optional[str]:
        """获取欢迎话术"""
        if not self.welcome_enabled:
            return None
        return self.welcome_template.format(user=user)

    def get_idle_script(self) -> Optional[str]:
        """获取空闲话术（带间隔控制）"""
        if not self.idle_enabled or not self.idle_scripts:
            return None

        now = time.time()
        if now - self._last_idle_time < self.idle_interval:
            return None

        self._last_idle_time = now
        script = self.idle_scripts[self._idle_index % len(self.idle_scripts)]
        self._idle_index += 1
        return script

    def check_keyword(self, text: str) -> Optional[str]:
        """检查关键词并返回处理结果"""
        for keyword, handler in self.keyword_handlers.items():
            if keyword in text:
                return handler(text)
        return None

    def _handle_price(self, text: str) -> str:
        """处理价格询问"""
        if self.current_product:
            p = self.current_product
            return f"这款{p.name}现在活动价只要{p.price}，非常划算！需要的宝宝扣1，我给你们上链接~"
        return "我们直播间的价格都很实惠哦，想看哪个商品可以告诉我~"

    def _handle_buy(self, text: str) -> str:
        """处理购买询问"""
        if self.current_product:
            return f"想入手的宝宝点击下方小黄车，找到{self.current_product.name}直接下单就行~有问题随时问我！"
        return "宝宝点击下方小黄车就可以选购啦，有任何问题随时问我~"

    def _handle_products(self, text: str) -> str:
        """处理商品询问"""
        if self.products:
            names = "、".join(p.name for p in list(self.products.values())[:3])
            return f"我们今天有{names}等好物，想了解哪个可以告诉我~"
        return "今天给大家准备了很多好物，稍后一一给大家介绍~"

    def get_product_script(self, product_id: Optional[str] = None) -> Optional[str]:
        """获取商品讲解话术"""
        product = self.products.get(product_id) if product_id else self.current_product
        if not product:
            return None

        points = "，".join(product.selling_points[:3]) if product.selling_points else product.description
        return f"给大家介绍一下这款{product.name}，{points}，现在只要{product.price}，真的很值！"
