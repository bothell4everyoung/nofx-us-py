from __future__ import annotations

from typing import Any

import asyncio


class AIClient:
    def __init__(self, model: str, api_key: str) -> None:
        self.model = model
        self.api_key = api_key

    async def complete(self, prompt: str, retry: int = 3, backoff_base: float = 0.25) -> str:
        """占位实现：带重试与指数退避。未来可接入 OpenAI/DeepSeek/Qwen SDK。

        返回值需是JSON字符串，由上层解析与校验。
        """
        attempt = 0
        while attempt < retry:
            try:
                await asyncio.sleep(0)
                # 返回最小可用决策结构
                return '{"action":"hold"}'
            except Exception:
                await asyncio.sleep(backoff_base * (2**attempt))
                attempt += 1
        return "{}"


