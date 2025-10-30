from __future__ import annotations

from typing import Any, Dict, Literal
import json
from dataclasses import dataclass


def build_system_prompt() -> str:
    return "You are an AI trading agent for US stocks and options. Respond in JSON."


def build_user_prompt(symbol: str, recent_data: list[dict[str, Any]]) -> str:
    return f"Make a decision for {symbol} based on recent data of length {len(recent_data)}."


@dataclass
class Decision:
    action: Literal["buy", "sell", "hold"]
    symbol: str | None = None
    quantity: int | None = None


def parse_decision(response_text: str) -> Dict[str, Any]:
    """解析与校验AI响应为JSON决策，返回字典。

    规则：action ∈ {buy, sell, hold}；buy/sell 需要 symbol 与 quantity。
    """
    try:
        data = json.loads(response_text)
    except Exception:
        return {"action": "hold"}

    action = str(data.get("action", "hold")).lower()
    if action not in {"buy", "sell", "hold"}:
        action = "hold"

    if action in {"buy", "sell"}:
        symbol = data.get("symbol")
        quantity = data.get("quantity")
        if not isinstance(symbol, str) or not isinstance(quantity, int) or quantity <= 0:
            return {"action": "hold"}
        return {"action": action, "symbol": symbol, "quantity": quantity}

    return {"action": "hold"}


