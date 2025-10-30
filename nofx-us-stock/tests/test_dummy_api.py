import pytest
from src.market.dummy_data_api import DummyStockDataAPI


@pytest.mark.asyncio
async def test_get_stock_ohlc():
    api = DummyStockDataAPI()
    data = await api.get_stock_ohlc("AAPL", "1min", 10)
    assert len(data) == 10
    assert all("timestamp" in d for d in data)
    assert all("close" in d for d in data)


