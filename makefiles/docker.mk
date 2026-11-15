# makefiles/docker.mk

.PHONY: deploy smart-deploy build build-no-cache build-fresh prune-build-cache image-save image-load image-pull image-restore up up-bg up-foreground down restart clean status logs shell deploy-no-cache build-stage build-stage-list

# Локальный кэш свежего образа: images/<name>-latest-<arch>.tar.zst.
# Каталог в .gitignore (тяжёлый) и в .dockerignore (не тащим в контекст).
IMAGE_DIR     ?= images
IMAGE_ARCHIVE ?= $(IMAGE_DIR)/walking_robot_sim-latest-$(shell uname -m).tar.zst
IMAGE_ID_FILE ?= $(IMAGE_DIR)/.last-image-id
GHCR_IMAGE    ?= ghcr.io/redalexdad/walking_robot_sim:latest
# Автосохранение свежего образа после make build (SAVE_IMAGE=0 — отключить)
SAVE_IMAGE    ?= 1

## Умная сборка и запуск (deploy, smart-deploy): пересобирает только при C++/Docker изменениях
deploy smart-deploy:
	$(require-docker)
	@bash scripts/smart-deploy.bash

## Сборка Docker образа
build:
	@printf "$(INFO)Сборка Docker образа$(if $(NO_CACHE), БЕЗ кэширования,)$(if $(PULL), с обновлением базы,) ...${NC}\n"
	@$(COMPOSE) --progress=auto build $(if $(NO_CACHE),--no-cache )$(if $(or $(NO_CACHE),$(PULL)),--pull,)
	@printf "$(OK)Образ собран${NC}\n"
	$(if $(filter 1,$(SAVE_IMAGE)),@$(MAKE) --no-print-directory image-save)

##! Сборка и запуск контейнера без кэша (make deploy-no-cache)
deploy-no-cache: build-no-cache up

##! Сборка образа без кэша (make build NO_CACHE=1)
build-no-cache:
	@$(MAKE) --no-print-directory build NO_CACHE=1

##! Полностью чистая пересборка: чистка BuildKit-кэша + сборка без кэша (make build-fresh)
build-fresh: prune-build-cache build-no-cache

##! Удалить кэш сборки BuildKit (docker buildx prune -af; ВНИМАНИЕ: затронет все проекты)
prune-build-cache:
	@printf "$(WARN)Чистка кэша BuildKit (buildx prune -af)...${NC}\n"
	@docker buildx prune -af >/dev/null
	@printf "$(OK)Кэш сборки очищен${NC}\n"

## Сохранить свежий образ в images/ (tar.zst) для восстановления после docker purge
image-save:
	$(require-docker)
	@mkdir -p $(IMAGE_DIR)
	@CUR=$$(docker image inspect walking_robot_sim:latest -f '{{.Id}}' 2>/dev/null || true); \
	if [ -z "$$CUR" ]; then \
		printf "$(ERR)Образ walking_robot_sim:latest не найден. Сначала make build${NC}\n"; exit 1; \
	fi; \
	if [ -f "$(IMAGE_ARCHIVE)" ] && [ -f "$(IMAGE_ID_FILE)" ] && [ "$$CUR" = "$$(cat $(IMAGE_ID_FILE))" ]; then \
		printf "$(OK)Кэш актуален: %s (%s)${NC}\n" "$(IMAGE_ARCHIVE)" "$$(du -h $(IMAGE_ARCHIVE) | cut -f1)"; \
	else \
		printf "$(INFO)Сохранение образа в $(IMAGE_ARCHIVE) (zstd)...${NC}\n"; \
		docker save walking_robot_sim:latest | zstd -T0 -3 -q -f -o $(IMAGE_ARCHIVE) || exit 1; \
		sha256sum $(IMAGE_ARCHIVE) > $(IMAGE_ARCHIVE).sha256; \
		cat $(IMAGE_ARCHIVE).sha256; \
		echo "$$CUR" > $(IMAGE_ID_FILE); \
		printf "$(OK)Образ сохранён: %s${NC}\n" "$$(du -h $(IMAGE_ARCHIVE) | cut -f1)"; \
	fi

## Загрузить образ из images/ в Docker (восстановление после docker purge)
image-load:
	$(require-docker)
	@if [ ! -f "$(IMAGE_ARCHIVE)" ]; then \
		printf "$(ERR)Нет $(IMAGE_ARCHIVE). Сделай make image-save или make image-pull${NC}\n"; exit 1; \
	fi
	@printf "$(INFO)Проверка и загрузка $(IMAGE_ARCHIVE) ...${NC}\n"
	@zstd -t $(IMAGE_ARCHIVE) && zstd -dc $(IMAGE_ARCHIVE) | docker load
	@printf "$(OK)Образ загружен: walking_robot_sim:latest${NC}\n"

## Скачать образ из GitHub Packages (GHCR), пометить walking_robot_sim:latest и сохранить в images/
image-pull:
	$(require-docker)
	@printf "$(INFO)Загрузка $(GHCR_IMAGE) ...${NC}\n"
	@docker pull $(GHCR_IMAGE) && docker tag $(GHCR_IMAGE) walking_robot_sim:latest
	@printf "$(OK)Образ $(GHCR_IMAGE) готов как walking_robot_sim:latest${NC}\n"
	@printf "$(INFO)Кэшируем образ в images/, чтобы больше не качать из GHCR...${NC}\n"
	@$(MAKE) --no-print-directory image-save

## Восстановить образ: из images/ если архив есть, иначе скачать из GHCR и закэшировать
image-restore:
	$(require-docker)
	@if [ -f "$(IMAGE_ARCHIVE)" ]; then \
		printf "$(INFO)Найден локальный архив $(IMAGE_ARCHIVE), загружаем без сети...${NC}\n"; \
		$(MAKE) --no-print-directory image-load; \
	else \
		printf "$(INFO)Локального архива нет, качаем из GHCR и кэшируем...${NC}\n"; \
		$(MAKE) --no-print-directory image-pull; \
	fi

## Запуск контейнера
up:
	$(require-docker)
	@if [ -n "$(BG)" ]; then \
		$(MAKE) --no-print-directory up-bg; \
	else \
		$(MAKE) --no-print-directory up-foreground; \
	fi

##! Запуск контейнера с ожиданием ROS (foreground)
up-foreground:
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

##! Запуск контейнера в фоновом режиме (make up BG=1)
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

## Сборка конкретного этапа Docker
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
