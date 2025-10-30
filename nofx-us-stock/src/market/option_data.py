from __future__ import annotations

from typing import Any

import pandas as pd

from .dummy_data_api import DummyOptionDataAPI


async def fetch_option_chain(symbol: str) -> pd.DataFrame:
    api = DummyOptionDataAPI()
    chain = await api.get_option_chain(symbol)
    return pd.DataFrame(chain)


