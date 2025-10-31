.PHONY: help install install-ta-lib dev test run start stop clean logs logs-api clean-all format type-check

help:
	@$(MAKE) -C nofx-us-stock help
	@echo "  make web-install       # 安装前端依赖 (web)"
	@echo "  make web-dev           # 启动前端开发服务器 (web)"
	@echo "  make web-build         # 前端构建 (web)"
	@echo "  make run-all           # 启动后端+前端 (开发模式)"
	@echo "  make start-all         # 后端+前端 后台启动"
	@echo "  make stop-all          # 停止后端+前端"

install:
	@$(MAKE) -C nofx-us-stock install

install-ta-lib:
	@$(MAKE) -C nofx-us-stock install-ta-lib

dev:
	@$(MAKE) -C nofx-us-stock dev

test:
	@$(MAKE) -C nofx-us-stock test

run:
	@$(MAKE) -C nofx-us-stock run

start:
	@$(MAKE) -C nofx-us-stock start

stop:
	@$(MAKE) -C nofx-us-stock stop

logs:
	@$(MAKE) -C nofx-us-stock logs

logs-api:
	@$(MAKE) -C nofx-us-stock logs-api

clean:
	@$(MAKE) -C nofx-us-stock clean

clean-all:
	@$(MAKE) -C nofx-us-stock clean-all

format:
	@$(MAKE) -C nofx-us-stock format

type-check:
	@$(MAKE) -C nofx-us-stock type-check

# ===== Web (frontend) =====
.PHONY: web-install web-dev web-build web-start web-stop run-all start-all stop-all

web-install:
	cd web && npm install

web-dev:
	cd web && npm run dev

web-build:
	cd web && npm run build

# ===== Combined =====
run-all:
	@echo "🚀 启动NOFX US Stock交易系统 (开发模式)..."; \
	echo "⚠️  按 Ctrl+C 停止"; \
	echo ""; \
	mkdir -p logs; \
	$(MAKE) -C nofx-us-stock stop >/dev/null 2>&1 || true; \
	PORT=$$(python -c "import json,os; p='nofx-us-stock/config.json'; print(json.load(open(p)).get('api_server_port',8080) if os.path.exists(p) else 8080)"); \
	echo "Backend:  http://localhost:$$PORT"; \
	echo "Frontend: http://localhost:3000"; \
	echo ""; \
	( cd nofx-us-stock && poetry run python src/main.py ) & \
	BACKEND_PID=$$!; \
	trap 'kill $$BACKEND_PID 2>/dev/null || true; exit' INT TERM; \
	cd web && npm run dev; \
	kill $$BACKEND_PID 2>/dev/null || true

start-all:
	@$(MAKE) -C nofx-us-stock start; \
	cd web && npm run dev > ../logs/web.dev.log 2>&1 & \
	echo $$! > ../logs/web.pid; \
	PORT=$$(python -c "import json,os; p='nofx-us-stock/config.json'; print(json.load(open(p)).get('api_server_port',8080) if os.path.exists(p) else 8080)"); \
	echo "Backend:  http://localhost:$$PORT"; \
	echo "Frontend: http://localhost:3000"; \
	echo "Frontend dev started (PID: $$(cat logs/web.pid))"

stop-all:
	@$(MAKE) -C nofx-us-stock stop; \
	if [ -f logs/web.pid ]; then kill $$(cat logs/web.pid) || true; rm -f logs/web.pid; echo "Frontend stopped"; else echo "Frontend not running"; fi; \
	# 端口兜底清理 (macOS): 如仍被占用则强杀占用 8080/3000-3010 的进程
	if command -v lsof >/dev/null 2>&1; then \
		lsof -ti tcp:8080 | xargs -r kill -9 2>/dev/null || true; \
		for p in $$(seq 3000 3010); do lsof -ti tcp:$$p | xargs -r kill -9 2>/dev/null || true; done; \
	fi

.PHONY: kill-ports
kill-ports:
	@echo "Killing processes on 8080 and 3000-3010 (if any)..."; \
	if command -v lsof >/dev/null 2>&1; then \
		lsof -ti tcp:8080 | xargs -r kill -9 2>/dev/null || true; \
		for p in $$(seq 3000 3010); do lsof -ti tcp:$$p | xargs -r kill -9 2>/dev/null || true; done; \
		echo "Done."; \
	else \
		echo "lsof not found; please kill ports manually."; \
	fi


