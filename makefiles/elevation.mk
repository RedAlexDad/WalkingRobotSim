# makefiles/elevation.mk

.PHONY: build-elevation elevation elevation-logs elevation-down

## Сборка GPU-образа для elevation mapping
build-elevation:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Сборка elevation_mapping образа...${NC}\n"
	@$(COMPOSE) build elevation_mapping
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Образ elevation_mapping собран${NC}\n"

## Запуск elevation mapping с RViz (требует запущенного симулятора)
elevation:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск elevation mapping (GPU + RViz)...${NC}\n"
	@$(COMPOSE) up -d elevation_mapping
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Elevation mapping запущен${NC}\n"
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Логи: make elevation-logs${NC}\n"

## Логи elevation mapping
elevation-logs:
	@$(COMPOSE) logs -f elevation_mapping

## Остановка elevation mapping
elevation-down:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Остановка elevation mapping...${NC}\n"
	@$(COMPOSE) stop elevation_mapping
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Elevation mapping остановлен${NC}\n"
