# makefiles/docker.mk

.PHONY: deploy smart-deploy build up up-bg down restart clean status logs shell deploy-no-cache build-stage build-stage-list

## Умная сборка и запуск: пересобирает только если есть C++/Docker изменения
deploy smart-deploy:
	$(require-docker)
	@bash scripts/smart-deploy.bash

## Сборка и запуск контейнера без кэша
deploy-no-cache: build-no-cache up

## Сборка Docker образа
build:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Сборка Docker образа с кэшированием по этапам...${NC}\n"
	@cd $(DOCKER_DIR) && $(COMPOSE) --progress=auto build
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Образ собран${NC}\n"

## Сборка Docker образа без кэша
build-no-cache:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Сборка Docker образа БЕЗ кэширования...${NC}\n"
	@cd $(DOCKER_DIR) && $(COMPOSE) --progress=auto build --no-cache
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Образ собран без кэша${NC}\n"

## Запуск контейнера
up:
	$(require-docker)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск контейнера $(CONTAINER_NAME)...${NC}\n"
	@cd $(DOCKER_DIR) && $(COMPOSE) up -d 2>&1 || { \
		if docker ps -a --format '{{.Names}}' | grep -Fxq '$(CONTAINER_NAME)'; then \
			printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}Контейнер $(CONTAINER_NAME) уже существует, удаляем и повторяем...${NC}\n"; \
			docker rm -f $(CONTAINER_NAME) >/dev/null 2>&1; \
			sleep 1; \
			$(COMPOSE) up -d; \
		else \
			printf "${RED}${BOLD}[x]${NC} ${RED}Неизвестная ошибка запуска${NC}\n"; \
			exit 1; \
		fi; \
	}
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Ожидание инициализации ROS окружения...${NC}\n"
	@attempt=0; \
	while [ $$attempt -lt 30 ]; do \
		if docker exec $(CONTAINER_NAME) bash -c "source /opt/ros/$(ROS_DISTRO)/setup.bash && source /root/ws/install/setup.bash 2>/dev/null && ros2 node list" >/dev/null 2>&1; then \
			printf "${GREEN}${BOLD}[v]${NC} ${GREEN}ROS окружение готово ($${attempt} сек)${NC}\n"; \
			break; \
		fi; \
		attempt=$$((attempt + 1)); \
		sleep 1; \
		printf "."; \
	done; \
	if [ $$attempt -eq 30 ]; then \
		printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}ROS окружение может быть не готово, но продолжаем...${NC}\n"; \
	fi
	@echo ""
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Статус контейнера:${NC}\n"
	@docker ps --filter "name=$(CONTAINER_NAME)" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Контейнер запущен${NC}\n"

## Запуск контейнера в фоновом режиме (без ожидания ROS)
up-bg:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Запуск контейнера $(CONTAINER_NAME) в фоновом режиме...${NC}\n"
	@cd $(DOCKER_DIR) && $(COMPOSE) up -d
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Контейнер запущен${NC}\n"

## Остановка контейнера с сохранением логов
down: save-logs
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Остановка контейнера $(CONTAINER_NAME)...${NC}\n"
	@cd $(DOCKER_DIR) && $(COMPOSE) down
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Контейнер остановлен${NC}\n"

## Перезапуск контейнера
restart: down up

## Полная очистка Docker образов и контейнеров
clean:
	@printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}Очистка Docker образов и контейнеров...${NC}\n"
	@cd $(DOCKER_DIR) && $(COMPOSE) down -v --remove-orphans
	@docker system prune -f
	@docker volume prune -f
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Очистка завершена${NC}\n"

## Статус контейнера
status:
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Статус контейнера:${NC}\n"
	@docker ps --filter "name=$(CONTAINER_NAME)" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Использование ресурсов:${NC}\n"
	@docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" $(CONTAINER_NAME) 2>/dev/null || printf "${YELLOW}${BOLD}[!]${NC} ${YELLOW}Контейнер не запущен${NC}\n"

## Просмотр логов контейнера
logs:
	@cd $(DOCKER_DIR) && $(COMPOSE) logs -f

## Подключение к контейнеру (shell)
shell:
	$(require-container)
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Подключение к контейнеру $(CONTAINER_NAME)...${NC}\n"
	@docker cp $(PROJECT_ROOT)/scripts/container-shell.sh $(CONTAINER_NAME):/tmp/container-shell.sh >/dev/null
	@docker exec -it $(CONTAINER_NAME) bash /tmp/container-shell.sh

## Сборка конкретного этапа Docker (пример: make build-stage STAGE=ros-core)
build-stage:
	@if [ -z "$(STAGE)" ]; then \
		printf "${RED}${BOLD}[x]${NC} ${RED}Укажите этап: make build-stage STAGE=<stage>${NC}\n"; \
		echo "Доступные этапы: base-system ros-core ros-control ros-simulation ros-navigation ros-vision ros-tools python-deps workspace final"; \
		exit 1; \
	fi
	@printf "${BLUE}${BOLD}[INFO]${NC} ${CYAN}Сборка этапа: $(STAGE)${NC}\n"
	@cd $(DOCKER_DIR) && docker build \
		--target $(STAGE) \
		--tag walking_robot_sim:$(STAGE) \
		--tag walking_robot_sim:latest \
		--cache-from walking_robot_sim:$(STAGE) \
		--cache-from walking_robot_sim:latest \
		.
	@printf "${GREEN}${BOLD}[v]${NC} ${GREEN}Этап $(STAGE) собран${NC}\n"

## Показать доступные этапы сборки
build-stage-list:
	@printf "${CYAN}Доступные этапы сборки:${NC}\n"
	@printf "  ${BOLD}base-system${NC}     - Системные зависимости\n"
	@printf "  ${BOLD}package-xmls${NC}     - Изоляция package.xml для кэша rosdep\n"
	@printf "  ${BOLD}ros-deps${NC}         - ROS зависимости через rosdep + pip\n"
	@printf "  ${BOLD}workspace${NC}        - Сборка workspace\n"
	@printf "  ${BOLD}final${NC}            - Финальный образ (по умолчанию)\n"
