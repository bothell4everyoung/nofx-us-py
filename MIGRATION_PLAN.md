# NOFX US Stock Trading System - 迁移执行计划

## 📌 执行目标

将 NOFX 加密货币期货交易系统迁移为**美股股票/期权AI自动交易系统**，使用Python实现后端，Poetry管理依赖，Dummy Data API模拟真实API。

---

## 🎯 核心要求

1. **使用Poetry管理依赖** (不用requirements.txt)
2. **所有入口通过Makefile** (并提供友好提示)
3. **使用Dummy Data API** (模拟美股数据API和券商API)
4. **LLM可直接执行的详细行动计划**

---

## 📁 项目目录结构

```
nofx-us-stock/
├── Makefile                          # 所有程序入口
├── pyproject.toml                    # Poetry配置
├── README.md                         # 项目说明
├── config.json.example               # 配置模板
│
├── src/                              # 源代码
│   ├── __init__.py
│   ├── main.py                       # 程序入口
│   │
│   ├── config/                       # 配置管理
│   │   ├── __init__.py
│   │   └── loader.py
│   │
│   ├── market/                       # 市场数据
│   │   ├── __init__.py
│   │   ├── dummy_data_api.py        # Dummy数据API
│   │   ├── stock_data.py            # 股票数据获取
│   │   └── option_data.py           # 期权数据获取
│   │
│   ├── trader/                       # 交易接口
│   │   ├── __init__.py
│   │   ├── trader_interface.py      # 交易接口定义
│   │   ├── dummy_broker_api.py      # Dummy券商API
│   │   ├── stock_trader.py          # 股票交易实现
│   │   └── option_trader.py         # 期权交易实现
│   │
│   ├── manager/                      # Trader管理
│   │   ├── __init__.py
│   │   └── trader_manager.py
│   │
│   ├── decision/                     # 决策引擎
│   │   ├── __init__.py
│   │   └── engine.py
│   │
│   ├── mcp/                          # AI客户端
│   │   ├── __init__.py
│   │   └── ai_client.py
│   │
│   ├── logger/                       # 日志系统
│   │   ├── __init__.py
│   │   └── decision_logger.py
│   │
│   ├── pool/                         # 股票池
│   │   ├── __init__.py
│   │   └── stock_pool.py
│   │
│   └── api/                          # HTTP API
│       ├── __init__.py
│       └── server.py
│
├── tests/                            # 测试
│   ├── __init__.py
│   └── test_dummy_api.py
│
├── decision_logs/                    # 决策日志
└── logs/                             # 系统日志
```

---

## 🔧 技术栈

| 模块 | 技术选型 | 说明 |
|------|---------|------|
| 语言 | Python 3.11+ | 必须支持type hints |
| 包管理 | Poetry 1.7+ | 不用requirements.txt |
| Web框架 | FastAPI | RESTful API |
| AI客户端 | openai | 支持DeepSeek/Qwen |
| 技术指标 | TA-Lib | EMA/MACD/RSI等 |
| 异步 | asyncio + aiohttp | 并发处理 |
| 日志 | loguru | 友好日志输出 |
| 数据 | pandas + numpy | 数据处理 |

---

## 📝 pyproject.toml

```toml
[tool.poetry]
name = "nofx-us-stock"
version = "0.1.0"
description = "AI-driven US stock and option auto trading system"
authors = ["Your Name <you@example.com>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
openai = "^1.0.0"
aiohttp = "^3.9.0"
pandas = "^2.0.0"
numpy = "^1.24.0"
loguru = "^0.7.0"
pydantic = "^2.0.0"
pydantic-settings = "^2.0.0"

[tool.poetry.dev-dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
black = "^23.0.0"
isort = "^5.12.0"
mypy = "^1.5.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 100
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
```

---

## 🛠️ Makefile

```makefile
.PHONY: help install install-ta-lib dev test run start stop clean logs

# 默认显示帮助
help:
	@echo "╔═══════════════════════════════════════════════════════════════════╗"
	@echo "║          NOFX US Stock Trading System - 命令列表                  ║"
	@echo "╚═══════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📦 安装与依赖:"
	@echo "  make install          # 安装Python依赖 (Poetry)"
	@echo "  make install-ta-lib   # 安装TA-Lib技术指标库 (必须先装)"
	@echo "  make dev              # 安装开发依赖"
	@echo ""
	@echo "🚀 运行系统:"
	@echo "  make run              # 启动后端 (开发模式)"
	@echo "  make start            # 启动后端 (后台模式)"
	@echo "  make stop             # 停止后端"
	@echo ""
	@echo "🧪 测试:"
	@echo "  make test             # 运行所有测试"
	@echo "  make test-api         # 测试Dummy API"
	@echo ""
	@echo "📊 日志:"
	@echo "  make logs             # 实时查看日志"
	@echo "  make logs-api         # 查看API日志"
	@echo ""
	@echo "🧹 清理:"
	@echo "  make clean            # 清理缓存和日志"
	@echo "  make clean-all        # 完全清理 (包括Poetry环境)"
	@echo ""

# 安装依赖
install:
	@echo "📦 正在使用Poetry安装依赖..."
	poetry install
	@echo "✅ 依赖安装完成！"

# 安装TA-Lib (必须先安装系统依赖)
install-ta-lib:
	@echo "📊 正在安装TA-Lib..."
	@echo "⚠️  请先安装系统依赖:"
	@echo "  macOS:   brew install ta-lib"
	@echo "  Ubuntu:  sudo apt-get install libta-lib0-dev"
	@echo "  然后继续安装Python绑定..."
	@read -p "是否已安装系统依赖？(y/n) " confirm && [ $$confirm = "y" ]
	poetry add TA-Lib
	@echo "✅ TA-Lib安装完成！"

# 安装开发依赖
dev: install
	@echo "🔧 安装开发工具..."
	poetry install --with dev
	@echo "✅ 开发环境配置完成！"

# 运行测试
test:
	@echo "🧪 运行测试..."
	poetry run pytest tests/ -v
	@echo "✅ 测试完成！"

# 测试Dummy API
test-api:
	@echo "🧪 测试Dummy Data API..."
	poetry run pytest tests/test_dummy_api.py -v
	@echo "✅ Dummy API测试完成！"

# 运行后端 (开发模式)
run:
	@echo "🚀 启动NOFX US Stock交易系统 (开发模式)..."
	@echo "⚠️  按 Ctrl+C 停止"
	poetry run python src/main.py

# 启动后端 (后台模式)
start:
	@echo "🚀 启动NOFX US Stock交易系统 (后台模式)..."
	poetry run python src/main.py > logs/system.log 2>&1 &
	@echo $$! > logs/pid.txt
	@echo "✅ 系统已启动 (PID: $$(cat logs/pid.txt))"
	@echo "📊 日志位置: logs/system.log"

# 停止后端
stop:
	@echo "⏹️  停止系统..."
	@if [ -f logs/pid.txt ]; then \
		kill $$(cat logs/pid.txt); \
		rm logs/pid.txt; \
		echo "✅ 系统已停止"; \
	else \
		echo "⚠️  系统未运行"; \
	fi

# 查看实时日志
logs:
	@echo "📊 实时查看系统日志 (按 Ctrl+C 退出)..."
	@if [ -f logs/system.log ]; then \
		tail -f logs/system.log; \
	else \
		echo "⚠️  日志文件不存在"; \
	fi

# 查看API日志
logs-api:
	@echo "📊 查看API日志..."
	poetry run python -c "import os; os.makedirs('logs', exist_ok=True)"

# 清理
clean:
	@echo "🧹 清理缓存和日志..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	@echo "✅ 清理完成！"

# 完全清理
clean-all: clean stop
	@echo "🗑️  完全清理Poetry环境..."
	poetry env remove python 2>/dev/null || true
	@echo "✅ 完全清理完成！"

# 格式化代码
format:
	@echo "🎨 格式化代码..."
	poetry run black src/ tests/
	poetry run isort src/ tests/
	@echo "✅ 代码格式化完成！"

# 类型检查
type-check:
	@echo "🔍 运行类型检查..."
	poetry run mypy src/
	@echo "✅ 类型检查完成！"
```

---

## 🎯 LLM执行计划 (Phase-by-Phase)

### ✅ Phase 1: 项目初始化 (第一优先级)

**任务清单:**
```bash
# LLM执行顺序
1. 创建项目目录结构
2. 创建pyproject.toml
3. 创建Makefile
4. 创建config.json.example
5. 创建README.md (基础版本)
6. 创建logs目录和decision_logs目录
```

**LLM应该创建的文件:**
- `pyproject.toml` (完整依赖列表)
- `Makefile` (所有命令入口)
- `config.json.example` (配置模板)
- `README.md` (使用说明)
- 目录结构

---

### ✅ Phase 2: Dummy Data API (第二优先级)

**创建文件**: `src/market/dummy_data_api.py`

**核心功能**:
1. **美股OHLC数据生成器** - 模拟真实市场数据
2. **期权链数据生成器** - 生成期权链
3. **实时价格模拟器** - 价格变动模拟

**必须实现的API:**

```python
class DummyStockDataAPI:
    """Dummy美股数据API"""
    
    async def get_stock_ohlc(self, symbol: str, interval: str, limit: int):
        """获取股票OHLC数据
        
        Args:
            symbol: 股票代码 (如 "AAPL")
            interval: 时间间隔 ("1min", "5min", "1day")
            limit: 数据点数量
            
        Returns:
            List[Dict] with columns: timestamp, open, high, low, close, volume
        """
        pass
    
    async def get_stock_quote(self, symbol: str):
        """获取实时报价"""
        pass
    
    async def search_stocks(self, query: str):
        """搜索股票"""
        pass

class DummyOptionDataAPI:
    """Dummy期权数据API"""
    
    async def get_option_chain(self, symbol: str):
        """获取期权链"""
        pass
    
    async def get_option_quote(self, option_symbol: str):
        """获取期权报价"""
        pass

class DummyBrokerAPI:
    """Dummy券商交易API"""
    
    async def get_account(self):
        """获取账户信息"""
        pass
    
    async def get_positions(self):
        """获取持仓"""
        pass
    
    async def place_order(self, symbol: str, side: str, quantity: int, order_type: str):
        """下单"""
        pass
    
    async def cancel_order(self, order_id: str):
        """撤单"""
        pass
```

**LLM提示**:
- 使用随机数生成器模拟价格变动
- 实现简单的趋势模拟 (上升/下降/震荡)
- 期权链应包括多个到期日和多个行权价
- 账户余额从配置文件读取

---

### ✅ Phase 3: 核心业务逻辑 (第三优先级)

**创建顺序:**

#### 3.1 配置管理
**文件**: `src/config/loader.py`
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class USStockConfig:
    brokers: list
    ai_api_key: str
    initial_balance: float

def load_config(path: str = "config.json") -> USStockConfig:
    """加载配置"""
    pass
```

#### 3.2 市场数据获取
**文件**: `src/market/stock_data.py`
- 调用DummyStockDataAPI
- 计算技术指标 (EMA, MACD, RSI)
- 包装为标准数据结构

#### 3.3 交易接口
**文件**: `src/trader/trader_interface.py`
```python
class USStockTrader(ABC):
    @abstractmethod
    async def get_account(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def buy_stock(self, symbol: str, shares: int) -> Dict[str, Any]:
        pass
```

**文件**: `src/trader/stock_trader.py`
- 实现USStockTrader接口
- 调用DummyBrokerAPI
- 添加错误处理和日志

#### 3.4 AI客户端
**文件**: `src/mcp/ai_client.py`
- 支持DeepSeek/Qwen API
- 重试机制
- 错误处理

#### 3.5 决策引擎
**文件**: `src/decision/engine.py`
- 构建系统Prompt (美股版本)
- 构建User Prompt (包含股票数据)
- 解析AI响应为JSON决策
- 决策验证

#### 3.6 日志系统
**文件**: `src/logger/decision_logger.py`
- 记录每次决策
- 性能分析
- 历史回放

#### 3.7 自动交易器
**文件**: `src/manager/trader_manager.py`
- 管理多个trader实例
- 周期执行
- 状态管理

---

### ✅ Phase 4: 程序入口

**文件**: `src/main.py`

```python
"""NOFX US Stock Trading System - Main Entry Point"""

import asyncio
import logging
from pathlib import Path

from config.loader import load_config
from manager.trader_manager import TraderManager
from api.server import start_api_server
from market.dummy_data_api import DummyStockDataAPI

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("╔═══════════════════════════════════════════════════════════╗")
    logger.info("║   NOFX US Stock Trading System - Starting...              ║")
    logger.info("╚═══════════════════════════════════════════════════════════╝")
    
    # 1. 加载配置
    config = load_config("config.json")
    logger.info(f"✓ 配置加载成功: {len(config.traders)} 个trader")
    
    # 2. 初始化Dummy APIs (这里只是示例，实际应该是单例)
    dummy_api = DummyStockDataAPI()
    logger.info("✓ Dummy Data API已初始化")
    
    # 3. 创建并启动TraderManager
    manager = TraderManager(config)
    await manager.start_all()
    logger.info("✓ 所有trader已启动")
    
    # 4. 启动API服务器
    await start_api_server(manager, port=8080)
    logger.info("✓ API服务器已启动 (http://localhost:8080)")
    
    # 5. 运行循环
    try:
        await asyncio.Event().wait()  # 永久等待
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在关闭...")
    finally:
        await manager.stop_all()

if __name__ == "__main__":
    asyncio.run(main())
```

---

### ✅ Phase 5: 测试与验证

**创建测试文件**: `tests/test_dummy_api.py`

```python
import pytest
from src.market.dummy_data_api import DummyStockDataAPI

@pytest.mark.asyncio
async def test_get_stock_ohlc():
    """测试获取股票OHLC数据"""
    api = DummyStockDataAPI()
    data = await api.get_stock_ohlc("AAPL", "1min", 10)
    
    assert len(data) == 10
    assert all("timestamp" in d for d in data)
    assert all("close" in d for d in data)

# 更多测试...
```

---

## 📋 LLM执行清单

### 🎯 第一轮: 基础设施 (必须完成)

- [ ] 创建项目目录结构
- [ ] 创建 `pyproject.toml`
- [ ] 创建 `Makefile`
- [ ] 创建 `config.json.example`
- [ ] 创建 `README.md`
- [ ] 创建 `src/__init__.py` 等初始化文件
- [ ] 创建 `logs/` 和 `decision_logs/` 目录

### 🎯 第二轮: Dummy APIs (核心依赖)

- [ ] `src/market/dummy_data_api.py` - DummyStockDataAPI
- [ ] `src/market/dummy_data_api.py` - DummyOptionDataAPI
- [ ] `src/trader/dummy_broker_api.py` - DummyBrokerAPI
- [ ] `tests/test_dummy_api.py` - 测试Dummy APIs

### 🎯 第三轮: 业务逻辑

- [ ] `src/config/loader.py` - 配置加载
- [ ] `src/market/stock_data.py` - 股票数据
- [ ] `src/market/option_data.py` - 期权数据
- [ ] `src/trader/trader_interface.py` - 交易接口定义
- [ ] `src/trader/stock_trader.py` - 股票交易实现
- [ ] `src/trader/option_trader.py` - 期权交易实现
- [ ] `src/mcp/ai_client.py` - AI客户端
- [ ] `src/decision/engine.py` - 决策引擎
- [ ] `src/logger/decision_logger.py` - 日志系统
- [ ] `src/manager/trader_manager.py` - Trader管理
- [ ] `src/api/server.py` - HTTP API服务器

### 🎯 第四轮: 入口与测试

- [ ] `src/main.py` - 主程序入口
- [ ] 运行 `make test` 验证所有功能
- [ ] 更新 `README.md` 完整文档

---

## 🚀 快速开始

**LLM完成Phase 1-2后，用户可以运行:**

```bash
# 安装TA-Lib系统依赖
make install-ta-lib

# 安装Python依赖
make install

# 启动系统
make run
```

---

## 📊 配置文件示例

**config.json.example:**
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

---

## ✅ 完成标准

**LLM完成所有任务后，系统应该:**

1. ✅ 能运行 `make help` 显示帮助信息
2. ✅ 能运行 `make run` 启动后端
3. ✅ Dummy API能返回模拟数据
4. ✅ 能访问 `http://localhost:8080/health` 返回健康状态
5. ✅ 日志记录正常运行
6. ✅ 所有测试通过 (`make test`)

---

## 🎓 LLM执行提示

1. **先执行Phase 1**: 搭建基础结构
2. **再执行Phase 2**: 实现Dummy APIs (这是核心依赖)
3. **然后执行Phase 3**: 逐步实现业务逻辑
4. **最后执行Phase 4**: 测试和验证

**每完成一个Phase，告诉用户当前进度和下一步**

---

---

# 前端Web界面迁移计划

## 📋 执行范围

**LLM需要修改的文件**: 
- `web/src/types/index.ts` - 类型定义
- `web/src/App.tsx` - 主要组件
- `web/src/i18n/translations.ts` - 翻译文案
- `web/index.html` - 页面标题

**无需改动的部分**:
- React组件架构、样式系统、图表库、国际化系统、API调用逻辑

---

## 🎯 Phase A: 扩展类型定义

**文件**: `web/src/types/index.ts`

**任务**: 在现有类型基础上添加可选字段，支持美股和期权

```typescript
// 扩展Position接口
export interface Position {
  symbol: string;
  side: "long" | "short" | "call" | "put";  // 新增 call/put
  entry_price: number;
  mark_price: number;
  quantity: number;
  leverage: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  liquidation_price: number | null;  // 改为可null
  margin_used: number;
  
  // ========== 新增期权字段 ==========
  option_type?: "call" | "put";
  underlying?: string;
  strike?: number;
  expiration?: string;
  delta?: number;
  gamma?: number;
  theta?: number;
  vega?: number;
  days_to_expiry?: number;
}

// 扩展DecisionAction接口
export interface DecisionAction {
  action: string;  // 改为string，允许新动作类型
  symbol: string;
  quantity: number;
  leverage: number;
  price: number;
  order_id: number;
  timestamp: string;
  success: boolean;
  error: string;
  
  // ========== 新增期权字段 ==========
  option_type?: "call" | "put";
  strike?: number;
  expiration?: string;
  days_to_expiry?: number;
}
```

---

## 🎯 Phase B: 修改持仓表格显示逻辑

**文件**: `web/src/App.tsx`

**定位**: 找到`TraderDetailsPage`组件中的持仓表格渲染部分

**改动1**: 动态表头

```typescript
{positions && positions.length > 0 ? (
  <div className="overflow-x-auto">
    <table className="w-full text-sm">
      <thead className="text-left border-b border-gray-800">
        <tr>
          <th className="pb-3 font-semibold text-gray-400">{t('symbol', language)}</th>
          <th className="pb-3 font-semibold text-gray-400">{t('side', language)}</th>
          <th className="pb-3 font-semibold text-gray-400">{t('entryPrice', language)}</th>
          <th className="pb-3 font-semibold text-gray-400">{t('markPrice', language)}</th>
          <th className="pb-3 font-semibold text-gray-400">{t('quantity', language)}</th>
          <th className="pb-3 font-semibold text-gray-400">{t('positionValue', language)}</th>
          <th className="pb-3 font-semibold text-gray-400">{t('unrealizedPnL', language)}</th>
          {/* 只在有持仓时动态显示这些列 */}
          {positions.some(p => p.leverage && p.leverage > 1) && (
            <th className="pb-3 font-semibold text-gray-400">{t('leverage', language)}</th>
          )}
          {positions.some(p => p.liquidation_price) && (
            <th className="pb-3 font-semibold text-gray-400">{t('liqPrice', language)}</th>
          )}
          {positions.some(p => p.days_to_expiry !== undefined) && (
            <th className="pb-3 font-semibold text-gray-400">{t('dte', language)}</th>
          )}
        </tr>
      </thead>
```

**改动2**: 修改持仓行渲染

```typescript
{positions.map((pos, i) => {
  const isOption = pos.option_type !== undefined;
  const isCall = pos.option_type === "call";
  
  return (
    <tr key={i} className="border-b border-gray-800 last:border-0">
      <td className="py-3 font-mono font-semibold">{pos.symbol}</td>
      <td className="py-3">
        <span
          className="px-2 py-1 rounded text-xs font-bold"
          style={
            isOption
              ? { background: isCall ? 'rgba(14, 203, 129, 0.1)' : 'rgba(246, 70, 93, 0.1)', color: isCall ? '#0ECB81' : '#F6465D' }
              : { background: pos.side === 'long' ? 'rgba(14, 203, 129, 0.1)' : 'rgba(246, 70, 93, 0.1)', color: pos.side === 'long' ? '#0ECB81' : '#F6465D' }
          }
        >
          {isOption ? (isCall ? 'CALL' : 'PUT') : (pos.side === 'long' ? 'LONG' : 'SHORT')}
        </span>
      </td>
      <td className="py-3 font-mono" style={{ color: '#EAECEF' }}>{pos.entry_price.toFixed(4)}</td>
      <td className="py-3 font-mono" style={{ color: '#EAECEF' }}>{pos.mark_price.toFixed(4)}</td>
      <td className="py-3 font-mono" style={{ color: '#EAECEF' }}>
        {isOption ? pos.quantity.toFixed(0) : pos.quantity.toFixed(4)}
      </td>
      <td className="py-3 font-mono font-bold" style={{ color: '#EAECEF' }}>
        {(pos.quantity * pos.mark_price).toFixed(2)} USD
      </td>
      <td className="py-3 font-mono">
        <span style={{ color: pos.unrealized_pnl >= 0 ? '#0ECB81' : '#F6465D', fontWeight: 'bold' }}>
          {pos.unrealized_pnl >= 0 ? '+' : ''}
          {pos.unrealized_pnl.toFixed(2)} ({pos.unrealized_pnl_pct.toFixed(2)}%)
        </span>
      </td>
      {pos.leverage > 1 && (
        <td className="py-3 font-mono" style={{ color: '#F0B90B' }}>{pos.leverage}x</td>
      )}
      {pos.liquidation_price && (
        <td className="py-3 font-mono" style={{ color: '#848E9C' }}>
          {pos.liquidation_price.toFixed(4)}
        </td>
      )}
      {isOption && pos.days_to_expiry !== undefined && (
        <td className="py-3 font-mono" style={{ color: pos.days_to_expiry < 7 ? '#F6465D' : '#848E9C' }}>
          {pos.days_to_expiry}d
        </td>
      )}
    </tr>
  );
})}
```

---

## 🎯 Phase C: 添加翻译条目

**文件**: `web/src/i18n/translations.ts`

**任务**: 在现有translations对象中添加以下条目

```typescript
export const translations = {
  en: {
    // ... 保留所有现有条目 ...
    
    // ========== 新增美股相关条目 ==========
    dte: "DTE",
    delta: "Δ",
    theta: "Θ",
    // ... 英文条目 ...
  },
  zh: {
    // ... 保留所有现有条目 ...
    
    // ========== 新增美股相关条目 ==========
    dte: "到期",
    delta: "Δ",
    theta: "Θ",
    // ... 中文条目 ...
  }
}
```

---

## 🎯 Phase D: 更新页面标题

**文件**: `web/index.html`

```html
<title>NOFX - AI US Stock & Options Trading</title>
```

---

## ✅ 验证清单

**完成Phase A-D后，运行**:

```bash
cd web
npm install
npm run dev
```

**检查项**:
1. TypeScript编译无错误 (`npx tsc --noEmit`)
2. 持仓表格能正确识别股票/期权
3. 决策卡片能显示新的动作类型
4. 翻译切换正常
5. 图表单位显示为USD而非USDT