# makefiles/microservices.mk
#
# Микросервисная декомпозиция (см. reports/isaam/2026-08-22_docker-microservices-v2.md).
# Образы: wrs-base -> wrs-sim / wrs-core / wrs-nav / wrs-rviz.
# Профили compose: sim | core | nav | viz | full.

MICRO_BASE_DF := src/docker/Dockerfile.base
MICRO_SERVICES := wrs-sim wrs-core wrs-nav wrs-rviz

.PHONY: base ms-build ms-build-sim ms-build-core ms-build-nav ms-build-rviz \
        ms-up ms-down ms-sim ms-core ms-nav ms-viz

## Собрать общий базовый образ wrs-base
base:
	$(require-docker)
	@printf "$(INFO)Сборка wrs-base...${NC}\n"
	@docker build --network=host -f $(MICRO_BASE_DF) -t wrs-base:latest .
	@printf "$(OK)wrs-base собран${NC}\n"

## Собрать все микросервис-образы (сначала база)
ms-build: base
	$(require-docker)
	@printf "$(INFO)Сборка сервисов: $(MICRO_SERVICES)...${NC}\n"
	@$(COMPOSE) build $(MICRO_SERVICES)
	@printf "$(OK)Микросервисы собраны${NC}\n"

## Собрать симулятор
ms-build-sim: base
	@$(COMPOSE) build wrs-sim

## Собрать ядро (Rust-контроллер — частая пересборка)
ms-build-core: base
	@$(COMPOSE) build wrs-core

## Собрать навигацию
ms-build-nav: base
	@$(COMPOSE) build wrs-nav

## Собрать RViz
ms-build-rviz: base
	@$(COMPOSE) build wrs-rviz

## Поднять полный микросервис-стек (sim+core+nav+viz)
ms-up:
	$(require-docker)
	@$(COMPOSE) --profile full up -d wrs-sim wrs-core wrs-nav wrs-rviz
	@printf "$(OK)Полный стек поднят${NC}\n"

## Остановить микросервис-стек
ms-down:
	@docker rm -f wrs-sim wrs-core wrs-nav wrs-rviz >/dev/null 2>&1 || true
	@printf "$(OK)Микросервис-стек остановлен${NC}\n"

## Поднять симулятор
ms-sim:
	@$(COMPOSE) --profile sim up -d wrs-sim

## Поднять ядро (нужен запущенный симулятор)
ms-core:
	@$(COMPOSE) --profile core up -d wrs-core

## Поднять навигацию
ms-nav:
	@$(COMPOSE) --profile nav up -d wrs-nav

## Поднять визуализацию
ms-viz:
	@$(COMPOSE) --profile viz up -d wrs-rviz
