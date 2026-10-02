# makefiles/microservices.mk
#
# Микросервисная декомпозиция (reports/isaam/2026-08-22_docker-microservices-v2.md).
# Образы: wrs-base -> wrs-sim / wrs-core / wrs-nav / wrs-rviz.
# SVC=sim|core|nav|rviz — только один сервис; по умолчанию все.

MICRO_BASE_DF  := src/docker/Dockerfile.base
MICRO_SERVICES := wrs-sim wrs-core wrs-nav wrs-rviz

.PHONY: base ms-build ms-up ms-down

## Собрать общий базовый образ wrs-base
base:
	$(require-docker)
	@printf "$(INFO)Сборка wrs-base...${NC}\n"
	@docker build --network=host -f $(MICRO_BASE_DF) -t wrs-base:latest .
	@printf "$(OK)wrs-base собран${NC}\n"

## Собрать образы микросервисов
ms-build: base
	$(require-docker)
	@case "$(SVC)" in \
		"")   $(COMPOSE) build $(MICRO_SERVICES) ;; \
		sim)  $(COMPOSE) build wrs-sim ;; \
		core) $(COMPOSE) build wrs-core ;; \
		nav)  $(COMPOSE) build wrs-nav ;; \
		rviz) $(COMPOSE) build wrs-rviz ;; \
		*) printf "$(ERR)SVC=$(SVC): ожидается sim|core|nav|rviz${NC}\n" >&2; exit 1 ;; \
	esac
	@printf "$(OK)Образы собраны${NC}\n"

## Поднять микросервис-стек
ms-up:
	$(require-docker)
	@case "$(SVC)" in \
		"")   $(COMPOSE) --profile full up -d wrs-sim wrs-core wrs-nav wrs-rviz ;; \
		sim)  $(COMPOSE) --profile sim up -d wrs-sim ;; \
		core) $(COMPOSE) --profile core up -d wrs-core ;; \
		nav)  $(COMPOSE) --profile nav up -d wrs-nav ;; \
		rviz) $(COMPOSE) --profile viz up -d wrs-rviz ;; \
		*) printf "$(ERR)SVC=$(SVC): ожидается sim|core|nav|rviz${NC}\n" >&2; exit 1 ;; \
	esac
	@printf "$(OK)Микросервисы запущены${NC}\n"

## Остановить микросервис-стек
ms-down:
	@docker rm -f $(if $(SVC),wrs-$(SVC),$(MICRO_SERVICES)) >/dev/null 2>&1 || true
	@printf "$(OK)Микросервис-стек остановлен${NC}\n"
