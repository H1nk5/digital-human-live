"""大模型接入模块（OpenAI 兼容协议）"""

import logging
from typing import Optional

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class LLMChat:
    """大模型调用，支持所有 OpenAI 兼容 API"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-chat",
        max_tokens: int = 200,
        temperature: float = 0.8,
        system_prompt: str = "你是一个直播带货助手，回答简短有力。",
    ):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.system_prompt = system_prompt
        self.history: list[dict] = []  # 对话历史
        self.max_history = 10  # 保留最近 N 轮对话

    async def chat(self, user_input: str, user_name: str = "") -> str:
        """发送消息并获取回复"""
        # 构建用户消息
        if user_name:
            content = f"用户[{user_name}]说：{user_input}"
        else:
            content = user_input

        self.history.append({"role": "user", "content": content})

        # 截断历史
        if len(self.history) > self.max_history * 2:
            self.history = self.history[-self.max_history * 2 :]

        messages = [{"role": "system", "content": self.system_prompt}] + self.history

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            reply = response.choices[0].message.content.strip()

            # 保存助手回复到历史
            self.history.append({"role": "assistant", "content": reply})

            logger.info(f"[LLM] {user_name}: {user_input} -> {reply}")
            return reply

        except Exception as e:
            logger.error(f"大模型调用失败: {e}")
            return "抱歉，我现在有点忙，稍后再聊~"

    async def chat_once(self, user_input: str, system_prompt: Optional[str] = None) -> str:
        """单次调用，不保存历史"""
        messages = [
            {"role": "system", "content": system_prompt or self.system_prompt},
            {"role": "user", "content": user_input},
        ]
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"大模型调用失败: {e}")
            return ""

    def clear_history(self):
        """清空对话历史"""
        self.history.clear()
