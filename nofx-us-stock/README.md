# NOFX US Stock & Options Trading (Python)

基于 FastAPI 与 asyncio 的美股/期权 AI 自动交易系统（迁移自加密期货版本）。使用 Poetry 管理依赖，提供 Dummy Data/Broker API 便于本地开发与测试。

## 快速开始

```bash
cd nofx-us-stock
make help
make install
make test
make run
```

可选：安装 TA-Lib（先安装系统库后再执行）
```bash
make install-ta-lib
```

访问健康检查：`http://localhost:8080/health`

## 目录结构

```
nofx-us-stock/
├── Makefile
├── pyproject.toml
├── README.md
├── config.json.example
├── src/
│   ├── main.py
│   ├── api/
│   │   └── server.py
│   ├── config/
│   │   └── loader.py
│   ├── manager/
│   │   └── trader_manager.py
│   ├── market/
│   │   ├── dummy_data_api.py
│   │   ├── stock_data.py
│   │   └── option_data.py
│   ├── trader/
│   │   ├── trader_interface.py
│   │   ├── stock_trader.py
│   │   ├── option_trader.py
│   │   └── dummy_broker_api.py
│   ├── decision/
│   │   └── engine.py
│   ├── logger/
│   │   └── decision_logger.py
│   └── pool/
│       └── stock_pool.py
├── tests/
│   ├── __init__.py
│   └── test_dummy_api.py
├── logs/
│   └── .gitkeep
└── decision_logs/
    └── .gitkeep
```

## 配置

参考 `config.json.example` 创建 `config.json`。

示例：
```json
{
  "traders": [
    {
      "id": "deepseek_trader",
      "name": "DeepSeek AI Trader",
      "ai_model": "deepseek",
      "ai_api_key": "sk-xxxxx",
      "initial_balance": 10000.0,
      "scan_interval_minutes": 3,
      "trading_type": "stock",
      "stocks": ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL"]
    }
  ],
  "api_server_port": 8080
}
```

## 组件说明
- API 服务器：`src/api/server.py`，提供 `/health` 健康检查
- 市场数据：`src/market/dummy_data_api.py` 生成 OHLC/期权链，`stock_data.py` 计算 EMA/MACD/RSI
- 券商模拟：`src/trader/dummy_broker_api.py` 下单/撤单/账户/持仓
- 交易实现：`src/trader/stock_trader.py`、`src/trader/option_trader.py`
- AI 客户端：`src/mcp/ai_client.py`（占位，可替换为真实 SDK）
- 决策引擎：`src/decision/engine.py`（占位）
- 日志：`src/logger/decision_logger.py`

## 常用命令
- `make help`：查看命令
- `make install`：安装依赖
- `make test`：运行测试
- `make run`：启动后端（开发模式）
- `make start`：后台运行
- `make stop`：停止后台
- `make format`：代码格式化
- `make type-check`：类型检查

## 下一步
- 扩充 API 路由（账户/持仓/下单等）
- 接入真实 AI/券商 SDK
- 完善策略与决策校验
