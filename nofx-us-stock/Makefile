.PHONY: help install install-ta-lib dev test run start stop clean logs logs-api clean-all format type-check

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

install:
	@echo "📦 正在使用Poetry安装依赖..."
	poetry install
	@echo "✅ 依赖安装完成！"

install-ta-lib:
	@echo "📊 正在安装TA-Lib..."
	@echo "⚠️  请先安装系统依赖:"
	@echo "  macOS:   brew install ta-lib"
	@echo "  Ubuntu:  sudo apt-get install libta-lib0-dev"
	@echo "  然后继续安装Python绑定..."
	@read -p "是否已安装系统依赖？(y/n) " confirm && [ $$confirm = "y" ]
	poetry add TA-Lib
	@echo "✅ TA-Lib安装完成！"

dev: install
	@echo "🔧 安装开发工具..."
	poetry install --with dev
	@echo "✅ 开发环境配置完成！"

test:
	@echo "🧪 运行测试..."
	poetry run pytest tests/ -v
	@echo "✅ 测试完成！"

test-api:
	@echo "🧪 测试Dummy Data API..."
	poetry run pytest tests/test_dummy_api.py -v
	@echo "✅ Dummy API测试完成！"

run:
	@echo "🚀 启动NOFX US Stock交易系统 (开发模式)..."
	@echo "⚠️  按 Ctrl+C 停止"
	poetry run python src/main.py

start:
	@echo "🚀 启动NOFX US Stock交易系统 (后台模式)..."
	poetry run python src/main.py > logs/system.log 2>&1 &
	@echo $$! > logs/pid.txt
	@echo "✅ 系统已启动 (PID: $$(cat logs/pid.txt))"
	@echo "📊 日志位置: logs/system.log"

stop:
	@echo "⏹️  停止系统..."
	@if [ -f logs/pid.txt ]; then \
		kill $$(cat logs/pid.txt); \
		rm logs/pid.txt; \
		echo "✅ 系统已停止"; \
	else \
		echo "⚠️  系统未运行"; \
	fi

logs:
	@echo "📊 实时查看系统日志 (按 Ctrl+C 退出)..."
	@if [ -f logs/system.log ]; then \
		tail -f logs/system.log; \
	else \
		echo "⚠️  日志文件不存在"; \
	fi

logs-api:
	@echo "📊 查看API日志..."
	poetry run python -c "import os; os.makedirs('logs', exist_ok=True)"

clean:
	@echo "🧹 清理缓存和日志..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	@echo "✅ 清理完成！"

clean-all: clean stop
	@echo "🗑️  完全清理Poetry环境..."
	poetry env remove python 2>/dev/null || true
	@echo "✅ 完全清理完成！"

format:
	@echo "🎨 格式化代码..."
	poetry run black src/ tests/
	poetry run isort src/ tests/
	@echo "✅ 代码格式化完成！"

type-check:
	@echo "🔍 运行类型检查..."
	poetry run mypy src/
	@echo "✅ 类型检查完成！"


