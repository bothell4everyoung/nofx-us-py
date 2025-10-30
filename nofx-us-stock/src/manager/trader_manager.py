from __future__ import annotations

from typing import Any
import asyncio
from dataclasses import dataclass
from time import time

from trader.stock_trader import StockTrader
from logger.decision_logger import DecisionLogger
from mcp.ai_client import AIClient
from decision.engine import build_system_prompt, build_user_prompt, parse_decision
from market.stock_data import fetch_stock_with_indicators


class TraderManager:
    def __init__(self, config: Any) -> None:
        self.config = config
        self._tasks: dict[str, asyncio.Task] = {}
        self._is_running = False
        self._start_time = 0.0
        self._call_count = 0
        self._logger = DecisionLogger(str((__import__("pathlib").Path(__file__).resolve().parents[2] / "decision_logs")))
        self._brokers: dict[str, StockTrader] = {}

    async def start_all(self) -> None:
        if self._is_running:
            return
        self._is_running = True
        self._start_time = time()
        for t in self.config.traders:
            trader_id = t.get("id", "default")
            # 初始化 broker 并保存，供API使用
            self._brokers[trader_id] = StockTrader()
            task = asyncio.create_task(self._run_trader_loop(trader_id, t))
            self._tasks[trader_id] = task

    async def stop_all(self) -> None:
        self._is_running = False
        for task in self._tasks.values():
            task.cancel()
        self._tasks.clear()

    async def _run_trader_loop(self, trader_id: str, cfg: dict) -> None:
        interval_min = int(cfg.get("scan_interval_minutes", 3))
        stocks = cfg.get("stocks", ["AAPL"]) or ["AAPL"]
        ai = AIClient(model=cfg.get("ai_model", "deepseek"), api_key=cfg.get("ai_api_key", ""))
        broker = self._brokers.get(trader_id) or StockTrader()
        sys_prompt = build_system_prompt()
        while self._is_running:
            for symbol in stocks:
                try:
                    data = await fetch_stock_with_indicators(symbol, "1min", 120)
                    user_prompt = build_user_prompt(symbol, data.tail(50).to_dict(orient="records"))
                    _ = sys_prompt  # 预留未来多段提示
                    ai_resp = await ai.complete(user_prompt)
                    decision = parse_decision(ai_resp)
                    # 简单执行：仅演示 buy
                    if decision.get("action") == "buy":
                        await broker.buy_stock(symbol=decision["symbol"], shares=int(decision["quantity"]))
                    self._logger.log(trader_id, {"symbol": symbol, **decision})
                    self._call_count += 1
                except Exception:
                    self._logger.log(trader_id, {"symbol": symbol, "action": "hold"})
                    continue
            await asyncio.sleep(max(1, interval_min * 60))

    # 查询接口（供API使用）
    def status(self, trader_id: str | None = None) -> dict[str, Any]:
        return {
            "is_running": self._is_running,
            "start_time": self._start_time,
            "runtime_minutes": int((time() - self._start_time) / 60) if self._is_running else 0,
            "call_count": self._call_count,
        }

    def recent_decisions(self, trader_id: str, limit: int = 50) -> list[dict[str, Any]]:
        return self._logger.read_recent(trader_id, limit=limit)

    # 账户/持仓/下单/撤单（供API使用）
    async def get_account(self, trader_id: str) -> dict[str, Any]:
        broker = self._brokers.get(trader_id)
        if not broker:
            return {"error": "trader_not_found"}
        return await broker.get_account()

    async def get_positions(self, trader_id: str) -> list[dict[str, Any]]:
        broker = self._brokers.get(trader_id)
        if not broker:
            return []
        return await broker.get_positions()

    async def place_order(self, trader_id: str, symbol: str, side: str, quantity: int, order_type: str) -> dict[str, Any]:
        broker = self._brokers.get(trader_id)
        if not broker:
            return {"error": "trader_not_found"}
        return await broker.place_order(symbol=symbol, side=side, quantity=quantity, order_type=order_type)

    async def cancel_order(self, trader_id: str, order_id: str) -> dict[str, Any]:
        broker = self._brokers.get(trader_id)
        if not broker:
            return {"error": "trader_not_found"}
        return await broker.cancel_order(order_id)


