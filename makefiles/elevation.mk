# makefiles/elevation.mk

.PHONY: elevation-build elevation elevation-bg elevation-rviz elevation-logs elevation-down
.PHONY: elevation-cpu-build elevation-cpu elevation-cpu-bg elevation-cpu-logs elevation-cpu-down
.PHONY: elevation-test

require-elevation = \
if [ -z "$$(docker ps -q -f name=elevation_mapping)" ]; then \
	printf "${RED}${BOLD}[x]${NC} ${RED}Контейнер elevation_mapping не запущен. Сначала выполните 'make elevation'${NC}\n" >&2; \
	exit 1; \
fi

require-elevation-cpu = \
if [ -z "$$(docker ps -q -f name=elevation_mapping_cpu)" ]; then \
	printf "${RED}${BOLD}[x]${NC} ${RED}Контейнер elevation_mapping_cpu не запущен. Сначала выполните 'make elevation-cpu'${NC}\n" >&2; \
	exit 1; \
fi

## Сборка GPU-образа для elevation mapping (умная: только при изменениях)
elevation-build:
	@bash scripts/smart-elevation.bash

## Принудительная пересборка GPU-образа
elevation-force-build:
	@bash scripts/smart-elevation.bash --build

## Запуск elevation mapping в фоне (без логов)
elevation-bg:
	@xhost +local: >/dev/null 2>&1 || true
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск elevation mapping в фоне...${NC}\n"
	@$(COMPOSE) up -d elevation_mapping
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Elevation mapping запущен${NC}\n"
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Логи: make elevation-logs${NC}\n"

## Запуск elevation mapping с логами (foreground)
elevation:
	@xhost +local: >/dev/null 2>&1 || true
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск elevation mapping с логами...${NC}\n"
	@$(COMPOSE) up elevation_mapping

## Запуск только RViz в elevation контейнере
elevation-rviz:
	$(require-elevation)
	@xhost +local: >/dev/null 2>&1 || true
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск RViz в elevation контейнере...${NC}\n"
	@docker exec -it elevation_mapping bash -c '\
		source /opt/ros/jazzy/setup.bash; \
		source /ws/install/setup.bash 2>/dev/null; \
		rviz2 -d /ws/install/elevation_mapping_cupy/share/elevation_mapping_cupy/rviz/elevation.rviz; \
	'

## Логи elevation mapping
elevation-logs:
	@$(COMPOSE) logs -f elevation_mapping

## Остановка elevation mapping
elevation-down:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Остановка elevation mapping...${NC}\n"
	@$(COMPOSE) stop elevation_mapping
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Elevation mapping остановлен${NC}\n"

## Сборка CPU-образа для elevation mapping
elevation-cpu-build:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Сборка CPU-образа elevation_mapping...${NC}\n"
	@$(COMPOSE) build elevation_mapping_cpu
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}CPU-образ elevation_mapping собран${NC}\n"

## Запуск elevation mapping (CPU) с логами (foreground)
elevation-cpu:
	@xhost +local: >/dev/null 2>&1 || true
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск elevation mapping (CPU) с логами...${NC}\n"
	@$(COMPOSE) up elevation_mapping_cpu

## Запуск elevation mapping (CPU) в фоне (без логов)
elevation-cpu-bg:
	@xhost +local: >/dev/null 2>&1 || true
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск elevation mapping (CPU) в фоне...${NC}\n"
	@$(COMPOSE) up -d elevation_mapping_cpu
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Elevation mapping (CPU) запущен${NC}\n"

## Запуск RViz в CPU-контейнере (Go2 elevation + Nav2 costmap)
elevation-cpu-rviz:
	$(require-elevation-cpu)
	@xhost +local: >/dev/null 2>&1 || true
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск RViz в CPU-контейнере...${NC}\n"
	@docker exec -it elevation_mapping_cpu bash -c '\
		source /opt/ros/jazzy/setup.bash; \
		source /ws/install/setup.bash 2>/dev/null; \
		rviz2 -d /ws/install/elevation_mapping_cupy/share/elevation_mapping_cupy/rviz/go2_elevation_nav2.rviz; \
	'

## Запуск unit-тестов elevation_mapping_cupy (pytest) с coverage
elevation-test:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск unit-тестов elevation_mapping_cupy...${NC}\n"
	cd elevation_mapping_cupy/elevation_mapping_cupy/elevation_mapping_cupy/tests && \
		python3 -m pytest -v --tb=short \
			--cov=.. --cov-report=term
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Unit-тесты завершены${NC}\n"

## Логи elevation mapping (CPU)
elevation-cpu-logs:
	@$(COMPOSE) logs -f elevation_mapping_cpu

## Остановка elevation mapping (CPU)
elevation-cpu-down:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Остановка elevation mapping (CPU)...${NC}\n"
	@$(COMPOSE) stop elevation_mapping_cpu
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Elevation mapping (CPU) остановлен${NC}\n"
