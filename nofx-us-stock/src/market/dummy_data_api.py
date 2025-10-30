from __future__ import annotations

import asyncio
import math
import random
from datetime import datetime, timedelta, timezone
from typing import Any


class DummyStockDataAPI:
    """Dummy美股数据API"""

    async def get_stock_ohlc(self, symbol: str, interval: str, limit: int) -> list[dict[str, Any]]:
        random.seed(hash(symbol) & 0xFFFF)
        now = datetime.now(timezone.utc)

        step = {
            "1min": timedelta(minutes=1),
            "5min": timedelta(minutes=5),
            "1day": timedelta(days=1),
        }.get(interval, timedelta(minutes=1))

        base = 100 + (hash(symbol) % 50)
        trend = random.choice([-0.03, 0.0, 0.03])
        vol_base = 100000 + (hash(symbol) % 50000)

        prices: list[dict[str, Any]] = []
        price = base
        for i in range(limit)[::-1]:
            t = now - step * i
            noise = math.sin(i / 5) * 0.5 + random.uniform(-0.3, 0.3)
            drift = trend * (limit - i) / limit
            change = noise + drift
            open_ = max(1.0, price)
            close = max(1.0, open_ * (1 + change / 100))
            high = max(open_, close) * (1 + random.uniform(0.0, 0.005))
            low = min(open_, close) * (1 - random.uniform(0.0, 0.005))
            volume = int(vol_base * (1 + random.uniform(-0.2, 0.2)))
            prices.append(
                {
                    "timestamp": t.isoformat(),
                    "open": round(open_, 4),
                    "high": round(high, 4),
                    "low": round(low, 4),
                    "close": round(close, 4),
                    "volume": volume,
                }
            )
            price = close
        await asyncio.sleep(0)
        return prices

    async def get_stock_quote(self, symbol: str) -> dict[str, Any]:
        ohlc = await self.get_stock_ohlc(symbol, "1min", 1)
        last = ohlc[-1]
        return {
            "symbol": symbol,
            "price": last["close"],
            "timestamp": last["timestamp"],
        }

    async def search_stocks(self, query: str) -> list[dict[str, str]]:
        universe = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "AMZN", "META"]
        q = query.upper()
        return [{"symbol": s, "name": s} for s in universe if q in s]


class DummyOptionDataAPI:
    """Dummy期权数据API"""

    async def get_option_chain(self, symbol: str) -> list[dict[str, Any]]:
        quote = await DummyStockDataAPI().get_stock_quote(symbol)
        spot = quote["price"]
        expiries = [7, 14, 30]
        strikes = [round(spot * k, 2) for k in [0.9, 0.95, 1.0, 1.05, 1.1]]
        chain: list[dict[str, Any]] = []
        now = datetime.now(timezone.utc)
        for dte in expiries:
            expiry = (now + timedelta(days=dte)).date().isoformat()
            for strike in strikes:
                for opt_type in ("call", "put"):
                    iv = 0.35
                    premium = max(0.1, abs(spot - strike) * 0.1) * (1 if opt_type == "call" else 0.95)
                    chain.append(
                        {
                            "symbol": f"{symbol}-{expiry}-{strike}-{opt_type[:1].upper()}",
                            "underlying": symbol,
                            "option_type": opt_type,
                            "strike": strike,
                            "expiration": expiry,
                            "bid": round(premium * 0.98, 2),
                            "ask": round(premium * 1.02, 2),
                            "iv": iv,
                            "delta": 0.5 if opt_type == "call" else -0.5,
                            "gamma": 0.02,
                            "theta": -0.01,
                            "vega": 0.1,
                            "days_to_expiry": dte,
                        }
                    )
        await asyncio.sleep(0)
        return chain

    async def get_option_quote(self, option_symbol: str) -> dict[str, Any]:
        # simplistic echo for demo
        return {"option_symbol": option_symbol, "price": round(random.uniform(0.1, 10.0), 2)}


class DummyBrokerAPI:
    """Dummy券商交易API"""

    def __init__(self) -> None:
        self._balance = 10000.0
        self._positions: dict[str, dict[str, Any]] = {}
        self._orders: dict[str, dict[str, Any]] = {}

    async def get_account(self) -> dict[str, Any]:
        return {"balance": self._balance}

    async def get_positions(self) -> list[dict[str, Any]]:
        return list(self._positions.values())

    async def place_order(self, symbol: str, side: str, quantity: int, order_type: str) -> dict[str, Any]:
        order_id = f"ord_{len(self._orders) + 1}"
        self._orders[order_id] = {
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "type": order_type,
            "status": "filled",
        }
        pos = self._positions.get(symbol, {"symbol": symbol, "quantity": 0, "side": side})
        pos["quantity"] += quantity
        self._positions[symbol] = pos
        return self._orders[order_id]

    async def cancel_order(self, order_id: str) -> dict[str, Any]:
        order = self._orders.get(order_id)
        if not order:
            return {"order_id": order_id, "status": "not_found"}
        order["status"] = "canceled"
        return order


