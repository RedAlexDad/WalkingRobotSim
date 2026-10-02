# makefiles/elevation.mk
#
# Elevation mapping: по умолчанию GPU, CPU — через аргумент CPU=1.
#   make elevation            # GPU
#   make elevation CPU=1      # CPU

# CPU=1 (любое непустое) -> CPU-сервис, иначе GPU.
ELEV_CPU        := $(if $(CPU),1,)
ELEV_SERVICE     = $(if $(ELEV_CPU),elevation_mapping_cpu,elevation_mapping)
ELEV_CONTAINER   = $(ELEV_SERVICE)
ELEV_SUFFIX      = $(if $(ELEV_CPU), (CPU),)
ELEV_RVIZ_CONFIG = $(if $(ELEV_CPU),go2_elevation_nav2.rviz,elevation.rviz)
ELEV_NVIDIA_DEP  = $(if $(ELEV_CPU),,nvidia-check)

.PHONY: elevation elevation-build elevation-force-build elevation-bg \
        elevation-rviz elevation-logs elevation-down elevation-test

require-elevation = \
if [ -z "$$(docker ps -q -f name=$(ELEV_CONTAINER))" ]; then \
	printf "$(ERR)Контейнер $(ELEV_CONTAINER) не запущен. Сначала: make elevation$(if $(ELEV_CPU), CPU=1,)${NC}\n" >&2; \
	exit 1; \
fi

## Сборка образа elevation mapping
elevation-build: $(ELEV_NVIDIA_DEP)
	@if [ -n "$(ELEV_CPU)" ]; then \
		printf "$(INFO)Сборка CPU-образа elevation_mapping...${NC}\n"; \
		$(COMPOSE) build elevation_mapping_cpu; \
		printf "$(OK)CPU-образ elevation_mapping собран${NC}\n"; \
	else \
		bash scripts/smart-elevation.bash; \
	fi

## Принудительная пересборка образа
elevation-force-build: $(ELEV_NVIDIA_DEP)
	@if [ -n "$(ELEV_CPU)" ]; then \
		printf "$(INFO)Пересборка CPU-образа elevation_mapping...${NC}\n"; \
		$(COMPOSE) build --no-cache elevation_mapping_cpu; \
		printf "$(OK)CPU-образ elevation_mapping собран${NC}\n"; \
	else \
		bash scripts/smart-elevation.bash --build; \
	fi

## Запуск elevation mapping с логами (foreground)
elevation: $(ELEV_NVIDIA_DEP)
	@xhost +local: >/dev/null 2>&1 || true
	@printf "$(INFO)Запуск elevation mapping$(ELEV_SUFFIX) с логами...${NC}\n"
	@$(COMPOSE) up $(ELEV_SERVICE)

## Запуск elevation mapping в фоне
elevation-bg: $(ELEV_NVIDIA_DEP)
	@xhost +local: >/dev/null 2>&1 || true
	@printf "$(INFO)Запуск elevation mapping$(ELEV_SUFFIX) в фоне...${NC}\n"
	@$(COMPOSE) up -d $(ELEV_SERVICE)
	@printf "$(OK)Elevation mapping$(ELEV_SUFFIX) запущен${NC}\n"
	@printf "$(INFO)Логи: make elevation-logs$(if $(ELEV_CPU), CPU=1,)${NC}\n"

## Запуск RViz в контейнере elevation mapping
elevation-rviz:
	$(require-elevation)
	@xhost +local: >/dev/null 2>&1 || true
	@printf "$(INFO)Запуск RViz в $(ELEV_CONTAINER)...${NC}\n"
	@docker exec -it $(ELEV_CONTAINER) bash -c '\
		source /opt/ros/jazzy/setup.bash; \
		source /ws/install/setup.bash 2>/dev/null; \
		rviz2 -d /ws/install/elevation_mapping_cupy/share/elevation_mapping_cupy/rviz/$(ELEV_RVIZ_CONFIG); \
	'

## Логи elevation mapping
elevation-logs:
	@$(COMPOSE) logs -f $(ELEV_SERVICE)

## Остановка elevation mapping
elevation-down:
	@printf "$(INFO)Остановка elevation mapping$(ELEV_SUFFIX)...${NC}\n"
	@$(COMPOSE) stop $(ELEV_SERVICE)
	@printf "$(OK)Elevation mapping$(ELEV_SUFFIX) остановлен${NC}\n"

## Запуск unit-тестов elevation_mapping_cupy (pytest + coverage)
elevation-test:
	@printf "$(INFO)Запуск unit-тестов elevation_mapping_cupy...${NC}\n"
	cd elevation_mapping_cupy/elevation_mapping_cupy/elevation_mapping_cupy/tests && \
		python3 -m pytest -v --tb=short \
			--cov=.. --cov-report=term
	@printf "$(OK)Unit-тесты завершены${NC}\n"
