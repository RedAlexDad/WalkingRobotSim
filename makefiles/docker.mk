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
	@printf "$(INFO)Сборка Docker образа с кэшированием по этапам...${NC}\n"
	@$(COMPOSE) --progress=auto build
	@printf "$(OK)Образ собран${NC}\n"

## Сборка Docker образа без кэша
build-no-cache:
	@printf "$(INFO)Сборка Docker образа БЕЗ кэширования...${NC}\n"
	@$(COMPOSE) --progress=auto build --no-cache
	@printf "$(OK)Образ собран без кэша${NC}\n"

## Запуск контейнера
up:
	$(require-docker)
	@printf "$(INFO)Запуск контейнера $(CONTAINER_NAME)...${NC}\n"
	@$(COMPOSE) up -d 2>&1 || { \
		if docker ps -a --format '{{.Names}}' | grep -Fxq '$(CONTAINER_NAME)'; then \
			printf "$(WARN)Контейнер $(CONTAINER_NAME) уже существует, удаляем и повторяем...${NC}\n"; \
			docker rm -f $(CONTAINER_NAME) >/dev/null 2>&1; \
			sleep 1; \
			$(COMPOSE) up -d; \
		else \
			printf "$(ERR)Неизвестная ошибка запуска${NC}\n"; \
			exit 1; \
		fi; \
	}
	@printf "$(INFO)Ожидание инициализации ROS окружения...${NC}\n"
	@attempt=0; \
	while [ $$attempt -lt 30 ]; do \
		if docker exec $(CONTAINER_NAME) bash -c "source /opt/ros/$(ROS_DISTRO)/setup.bash && source /root/ws/install/setup.bash 2>/dev/null && ros2 node list" >/dev/null 2>&1; then \
			printf "$(OK)ROS окружение готово ($${attempt} сек)${NC}\n"; \
			break; \
		fi; \
		attempt=$$((attempt + 1)); \
		sleep 1; \
		printf "."; \
	done; \
	if [ $$attempt -eq 30 ]; then \
		printf "$(WARN)ROS окружение может быть не готово, но продолжаем...${NC}\n"; \
	fi
	@echo ""
	@printf "$(INFO)Статус контейнера:${NC}\n"
	@docker ps --filter "name=$(CONTAINER_NAME)" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
	@printf "$(OK)Контейнер запущен${NC}\n"

## Запуск контейнера в фоновом режиме (без ожидания ROS)
up-bg:
	@printf "$(INFO)Запуск контейнера $(CONTAINER_NAME) в фоновом режиме...${NC}\n"
	@$(COMPOSE) up -d
	@printf "$(OK)Контейнер запущен${NC}\n"

## Остановка контейнера с сохранением логов
down: save-logs
	@printf "$(INFO)Остановка контейнера $(CONTAINER_NAME)...${NC}\n"
	@$(COMPOSE) down
	@printf "$(OK)Контейнер остановлен${NC}\n"

## Перезапуск контейнера
restart: down up

## Полная очистка Docker образов и контейнеров
clean:
	@printf "$(WARN)Очистка Docker образов и контейнеров...${NC}\n"
	@$(COMPOSE) down -v --remove-orphans
	@docker system prune -f
	@docker volume prune -f
	@printf "$(OK)Очистка завершена${NC}\n"

## Статус контейнера
status:
	@printf "$(INFO)Статус контейнера:${NC}\n"
	@docker ps --filter "name=$(CONTAINER_NAME)" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@printf "$(INFO)Использование ресурсов:${NC}\n"
	@docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" $(CONTAINER_NAME) 2>/dev/null || printf "$(WARN)Контейнер не запущен${NC}\n"

## Просмотр логов контейнера
logs:
	@$(COMPOSE) logs -f

## Подключение к контейнеру (shell)
shell:
	$(require-container)
	@printf "$(INFO)Подключение к контейнеру $(CONTAINER_NAME)...${NC}\n"
	@docker cp $(PROJECT_ROOT)/scripts/container-shell.sh $(CONTAINER_NAME):/tmp/container-shell.sh >/dev/null
	@docker exec -it $(CONTAINER_NAME) bash /tmp/container-shell.sh

## Сборка конкретного этапа Docker (пример: make build-stage STAGE=ros-core)
build-stage:
	@if [ -z "$(STAGE)" ]; then \
		printf "$(ERR)Укажите этап: make build-stage STAGE=<stage>${NC}\n"; \
		echo "Доступные этапы: base-system ros-core ros-control ros-simulation ros-navigation ros-vision ros-tools python-deps workspace final"; \
		exit 1; \
	fi
	@printf "$(INFO)Сборка этапа: $(STAGE)${NC}\n"
	@cd $(DOCKER_DIR) && docker build \
		--target $(STAGE) \
		--tag walking_robot_sim:$(STAGE) \
		--tag walking_robot_sim:latest \
		--cache-from walking_robot_sim:$(STAGE) \
		--cache-from walking_robot_sim:latest \
		.
	@printf "$(OK)Этап $(STAGE) собран${NC}\n"

## Показать доступные этапы сборки
build-stage-list:
	@printf "${CYAN}Доступные этапы сборки:${NC}\n"
	@printf "  ${BOLD}base-system${NC}     - Системные зависимости\n"
	@printf "  ${BOLD}package-xmls${NC}     - Изоляция package.xml для кэша rosdep\n"
	@printf "  ${BOLD}ros-deps${NC}         - ROS зависимости через rosdep + pip\n"
	@printf "  ${BOLD}workspace${NC}        - Сборка workspace\n"
	@printf "  ${BOLD}final${NC}            - Финальный образ (по умолчанию)\n"
