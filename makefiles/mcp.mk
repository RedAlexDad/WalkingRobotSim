# makefiles/mcp.mk
#
# ROS MCP (https://github.com/robotmcp/ros-mcp-server) работает через rosbridge
# (websocket). Контейнер в network_mode: host — rosbridge на :9090 доступен и с
# хоста, и видит граф и хоста, и контейнера (один DDS-домен). Достаточно поднять
# rosbridge один раз; MCP-сервер подключается к ws://localhost:9090.

MCP_PORT ?= 9090

.PHONY: mcp mcp-start mcp-stop

## Подключить ROS MCP: поднять rosbridge (websocket :9090)
mcp: mcp-start

## Поднять rosbridge_websocket в контейнере (для ROS MCP)
mcp-start:
	$(require-container)
	@printf "$(INFO)Запуск rosbridge_websocket на :$(MCP_PORT)...${NC}\n"
	@$(call ros-exec,pkill -f '[r]osbridge_websocket' 2>/dev/null || true)
	@$(call ros-exec-d,ros2 launch rosbridge_server rosbridge_websocket_launch.xml port:=$(MCP_PORT))
	@sleep 2
	@if ss -ltn 2>/dev/null | grep -q ":$(MCP_PORT) "; then \
		printf "$(OK)rosbridge запущен — MCP подключайте к ws://localhost:$(MCP_PORT)${NC}\n"; \
	else \
		printf "$(WARN)rosbridge не слушает :$(MCP_PORT). Проверьте: docker exec $(CONTAINER_NAME) pgrep -af rosbridge${NC}\n"; \
	fi

## Остановить rosbridge
mcp-stop:
	@$(call ros-exec,pkill -f '[r]osbridge_websocket' 2>/dev/null || true)
	@printf "$(OK)rosbridge остановлен${NC}\n"
