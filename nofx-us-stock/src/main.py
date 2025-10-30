"""NOFX US Stock Trading System - Main Entry Point"""

import asyncio
import logging
from pathlib import Path

from config.loader import load_config
from manager.trader_manager import TraderManager
from api.server import start_api_server
from market.dummy_data_api import DummyStockDataAPI


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("╔═══════════════════════════════════════════════════════════╗")
    logger.info("║   NOFX US Stock Trading System - Starting...              ║")
    logger.info("╚═══════════════════════════════════════════════════════════╝")

    # 1. 加载配置
    root = Path(__file__).resolve().parents[1]
    cfg = root / "config.json"
    config = load_config(str(cfg))
    logger.info("✓ 配置加载成功")

    # 2. 初始化Dummy APIs
    _ = DummyStockDataAPI()
    logger.info("✓ Dummy Data API已初始化")

    # 3. 创建并启动TraderManager
    manager = TraderManager(config)
    await manager.start_all()
    logger.info("✓ 所有trader已启动")

    # 4. 启动API服务器（阻塞）
    await start_api_server(manager, port=config.api_server_port)


if __name__ == "__main__":
    asyncio.run(main())


