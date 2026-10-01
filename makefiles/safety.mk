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

# ── GPU: выбор режима рендера ────────────────────────────
#
#   WRS_GPU=auto     — nvidia, если доступна (nvidia-smi), иначе amd, иначе none
#   WRS_GPU=nvidia   — NVIDIA eGPU (RTX) через nvidia runtime
#   WRS_GPU=amd      — встроенная AMD (iGPU) по vendor 0x1002
#   WRS_GPU=none     — без проброса GPU (headless)
#
# Пример: WRS_GPU=nvidia make deploy

WRS_GPU ?= auto

# Встроенная AMD (iGPU) — по vendor 0x1002 (номера cardN плавают)
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

# NVIDIA доступна?
WRS_HAS_NVIDIA := $(shell command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1 && echo 1)

# Итоговый режим
ifeq ($(WRS_GPU),auto)
  ifneq ($(WRS_HAS_NVIDIA),)
    WRS_GPU_EFF := nvidia
  else ifneq ($(WRS_DRI_RENDER),)
    WRS_GPU_EFF := amd
  else
    WRS_GPU_EFF := none
  endif
else
  WRS_GPU_EFF := $(WRS_GPU)
endif

export WRS_DRI_CARD
export WRS_DRI_RENDER
export WRS_GPU_EFF

# Рекурсивные переменные: раскрываются при вызове, уже после проверки выше.
WRS_COMPOSE_FILES = -f $(PROJECT_ROOT)/compose.yml \
  $(if $(filter nvidia,$(WRS_GPU_EFF)),-f $(PROJECT_ROOT)/compose.nvidia.yml) \
  $(if $(filter amd,$(WRS_GPU_EFF)),$(if $(WRS_DRI_RENDER),-f $(PROJECT_ROOT)/compose.gpu.yml))
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

## Показать, какая GPU будет проброшена
gpu-info:
	@printf "$(OK)Режим GPU: $(WRS_GPU_EFF)${NC}\n"
	@if [ "$(WRS_GPU_EFF)" = "nvidia" ]; then \
		printf "$(OK)NVIDIA eGPU: $(shell nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)${NC}\n"; \
	elif [ -n "$(WRS_DRI_RENDER)" ]; then \
		printf "$(OK)iGPU AMD: card=$(WRS_DRI_CARD) render=$(WRS_DRI_RENDER)${NC}\n"; \
	else \
		printf "$(WARN)GPU не найден — контейнер стартует headless${NC}\n"; \
	fi
