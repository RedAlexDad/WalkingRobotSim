# makefiles/safety.mk
#
# Общие защитные механизмы «на все случаи»: docker/окружение, устройство GPU,
# X11, состояние контейнера. Переиспользуемые проверки оформлены через define
# (require-docker, require-device); цель `doctor` прогоняет их разом.
#
# Проброс встроенной AMD (iGPU) сюда же: номера /dev/dri/cardN и renderDN
# меняются при подключении/отключении eGPU, поэтому пути определяются
# динамически по vendor 0x1002 (scripts/detect-gpu.sh) и подключаются
# отдельным override-файлом compose.gpu.yml ТОЛЬКО если iGPU найден:
#   - iGPU есть → compose.yml + compose.gpu.yml   (GUI/сенсоры работают)
#   - iGPU нет  → только compose.yml              (headless, деплой не падает)
#
# Переопределение вручную: WRS_DRI_CARD=... WRS_DRI_RENDER=... make deploy

# ── переиспользуемые проверки ─────────────────────────────

# docker + compose + запущенный демон
define require-docker
	@command -v docker >/dev/null 2>&1 || { \
		printf "$(ERR)docker не установлен${NC}\n" >&2; exit 1; }
	@docker compose version >/dev/null 2>&1 || { \
		printf "$(ERR)плагин docker compose недоступен${NC}\n" >&2; exit 1; }
	@docker info >/dev/null 2>&1 || { \
		printf "$(ERR)демон docker не запущен (sudo systemctl start docker)${NC}\n" >&2; \
		exit 1; }
endef

# require-device <path> — устройство/файл существует
define require-device
	@[ -e "$(1)" ] || { \
		printf "$(ERR)устройство $(1) не найдено${NC}\n" >&2; exit 1; }
endef

# ── GPU: динамический проброс iGPU AMD ───────────────────

WRS_DRI_CARD   ?= $(shell bash $(PROJECT_ROOT)/scripts/detect-gpu.sh card 2>/dev/null)
WRS_DRI_RENDER ?= $(shell bash $(PROJECT_ROOT)/scripts/detect-gpu.sh render 2>/dev/null)

# Защита: путь задан, но не существует → проброс отключаем, иначе docker
# падает «no such file or directory» (актуально при смене номеров cardN).
ifneq ($(WRS_DRI_RENDER),)
ifeq ($(wildcard $(WRS_DRI_RENDER)),)
$(warning WRS_DRI_RENDER=$(WRS_DRI_RENDER) не существует — проброс GPU отключён)
override WRS_DRI_RENDER :=
override WRS_DRI_CARD :=
endif
endif

export WRS_DRI_CARD
export WRS_DRI_RENDER

# Рекурсивные переменные: раскрываются при вызове, уже после проверки выше.
WRS_COMPOSE_FILES = -f $(PROJECT_ROOT)/compose.yml \
  $(if $(WRS_DRI_RENDER),-f $(PROJECT_ROOT)/compose.gpu.yml)
COMPOSE = docker compose $(WRS_COMPOSE_FILES)

# ── preflight ─────────────────────────────────────────────

.PHONY: doctor gpu-info

## Проверить окружение (docker, GPU, X11, контейнер)
doctor:
	@printf "${BOLD}Preflight:${NC}\n"
	@command -v docker >/dev/null 2>&1 \
		&& printf "  ${GREEN}[v]${NC} docker\n" \
		|| printf "  ${RED}[x]${NC} docker не установлен\n"
	@docker compose version >/dev/null 2>&1 \
		&& printf "  ${GREEN}[v]${NC} docker compose\n" \
		|| printf "  ${RED}[x]${NC} docker compose недоступен\n"
	@docker info >/dev/null 2>&1 \
		&& printf "  ${GREEN}[v]${NC} docker daemon\n" \
		|| printf "  ${RED}[x]${NC} docker daemon не запущен\n"
	@if [ -n "$(WRS_DRI_RENDER)" ]; then \
		printf "  ${GREEN}[v]${NC} iGPU: $(WRS_DRI_CARD) $(WRS_DRI_RENDER)\n"; \
	else \
		printf "  ${YELLOW}[!]${NC} iGPU не найден — GUI/сенсоры без GPU\n"; \
	fi
	@if [ -n "$$DISPLAY" ]; then \
		printf "  ${GREEN}[v]${NC} DISPLAY=$$DISPLAY\n"; \
	else \
		printf "  ${YELLOW}[!]${NC} DISPLAY не задан (GUI недоступен)\n"; \
	fi
	@if docker ps --format '{{.Names}}' 2>/dev/null | grep -q $(CONTAINER_NAME); then \
		printf "  ${GREEN}[v]${NC} контейнер $(CONTAINER_NAME) запущен\n"; \
	else \
		printf "  ${YELLOW}[!]${NC} контейнер $(CONTAINER_NAME) не запущен\n"; \
	fi

## Показать, какая iGPU будет проброшена
gpu-info:
	@if [ -n "$(WRS_DRI_RENDER)" ]; then \
		printf "$(OK)iGPU пробрасывается: card=$(WRS_DRI_CARD) render=$(WRS_DRI_RENDER)${NC}\n"; \
	else \
		printf "$(WARN)iGPU не найден — контейнер стартует без проброса GPU (headless)${NC}\n"; \
	fi
