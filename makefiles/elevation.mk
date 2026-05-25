# makefiles/elevation.mk

.PHONY: elevation-build elevation elevation-bg elevation-rviz elevation-logs elevation-down

require-elevation = \
if [ -z "$$(docker ps -q -f name=elevation_mapping)" ]; then \
	printf "${RED}${BOLD}[x]${NC} ${RED}Контейнер elevation_mapping не запущен. Сначала выполните 'make elevation'${NC}\n" >&2; \
	exit 1; \
fi

## Сборка GPU-образа для elevation mapping
elevation-build:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Сборка elevation_mapping образа...${NC}\n"
	@$(COMPOSE) build elevation_mapping
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Образ elevation_mapping собран${NC}\n"

## Запуск elevation mapping в фоне (без логов)
elevation-bg:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск elevation mapping в фоне...${NC}\n"
	@$(COMPOSE) up -d elevation_mapping
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Elevation mapping запущен${NC}\n"
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Логи: make elevation-logs${NC}\n"

## Запуск elevation mapping с логами (foreground)
elevation:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск elevation mapping с логами...${NC}\n"
	@$(COMPOSE) up elevation_mapping

## Запуск только RViz в elevation контейнере
elevation-rviz:
	$(require-elevation)
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
