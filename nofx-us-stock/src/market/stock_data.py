from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .dummy_data_api import DummyStockDataAPI


async def fetch_stock_with_indicators(symbol: str, interval: str = "1min", limit: int = 200) -> pd.DataFrame:
    api = DummyStockDataAPI()
    data = await api.get_stock_ohlc(symbol, interval, limit)
    df = pd.DataFrame(data)
    if df.empty:
        return df
    # 指标: EMA/MACD/RSI（简化实现，不依赖TA-Lib）
    df["ema_12"] = df["close"].ewm(span=12, adjust=False).mean()
    df["ema_26"] = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = df["ema_12"] - df["ema_26"]
    df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()

    change = df["close"].diff()
    gain = (change.where(change > 0, 0.0)).rolling(window=14).mean()
    loss = (-change.where(change < 0, 0.0)).rolling(window=14).mean()
    rs = gain / (loss.replace(0, np.nan))
    df["rsi"] = 100 - (100 / (1 + rs))
    df["rsi"] = df["rsi"].fillna(50)
    return df


