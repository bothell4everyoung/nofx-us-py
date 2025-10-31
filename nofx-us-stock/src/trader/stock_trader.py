from __future__ import annotations

from typing import Any, Dict

from .trader_interface import USStockTrader
from .dummy_broker_api import DummyBrokerAPI


class StockTrader(USStockTrader):
    def __init__(self, broker: DummyBrokerAPI | None = None) -> None:
        self.broker = broker or DummyBrokerAPI()

    async def get_account(self) -> Dict[str, Any]:
        return await self.broker.get_account()

    async def buy_stock(self, symbol: str, shares: int) -> Dict[str, Any]:
        if shares <= 0:
            return {"error": "invalid_shares"}
        return await self.broker.place_order(symbol=symbol, side="buy", quantity=shares, order_type="market")
    
    async def sell_stock(self, symbol: str, shares: int = 0) -> Dict[str, Any]:
        """卖出股票（平多仓）。如果shares为0，则平掉该股票的所有持仓"""
        if shares == 0:
            # 获取当前持仓
            positions = await self.broker.get_positions()
            for pos in positions:
                if pos.get("symbol") == symbol and pos.get("side") == "long":
                    shares = int(pos.get("quantity", 0))
                    break
            if shares == 0:
                return {"error": "no_position"}
        if shares <= 0:
            return {"error": "invalid_shares"}
        return await self.broker.place_order(symbol=symbol, side="sell", quantity=shares, order_type="market")
    
    async def short_stock(self, symbol: str, shares: int) -> Dict[str, Any]:
        """做空股票（开空仓）"""
        if shares <= 0:
            return {"error": "invalid_shares"}
        return await self.broker.place_order(symbol=symbol, side="short", quantity=shares, order_type="market")
    
    async def cover_short(self, symbol: str, shares: int = 0) -> Dict[str, Any]:
        """平空仓。如果shares为0，则平掉该股票的所有空仓"""
        if shares == 0:
            # 获取当前持仓
            positions = await self.broker.get_positions()
            for pos in positions:
                if pos.get("symbol") == symbol and pos.get("side") == "short":
                    shares = int(pos.get("quantity", 0))
                    break
            if shares == 0:
                return {"error": "no_position"}
        if shares <= 0:
            return {"error": "invalid_shares"}
        return await self.broker.place_order(symbol=symbol, side="cover", quantity=shares, order_type="market")

    async def get_positions(self) -> list[dict[str, Any]]:
        return await self.broker.get_positions()

    async def place_order(self, symbol: str, side: str, quantity: int, order_type: str = "market") -> Dict[str, Any]:
        if quantity <= 0:
            return {"error": "invalid_quantity"}
        side = side.lower()
        if side not in {"buy", "sell"}:
            return {"error": "invalid_side"}
        return await self.broker.place_order(symbol=symbol, side=side, quantity=quantity, order_type=order_type)

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        return await self.broker.cancel_order(order_id)


