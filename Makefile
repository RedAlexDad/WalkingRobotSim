# Walking Robot Simulation - Makefile
# Конфигурация + include модулей

SHELL := /bin/bash

# ════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ════════════════════════════════════════════════════════════

CONTAINER_NAME  := walking_robot_sim
IMAGE_NAME      := walking_robot_sim:latest
DOCKER_DIR      := $(CURDIR)/src/docker
PROJECT_ROOT    := $(CURDIR)
ROS_DISTRO      := jazzy

# COMPOSE и проброс iGPU определяются в makefiles/safety.mk (подключается ниже).

# ════════════════════════════════════════════════════════════
# ЦВЕТА
# ════════════════════════════════════════════════════════════

BLUE    := \033[0;34m
GREEN   := \033[0;32m
YELLOW  := \033[1;33m
RED     := \033[0;31m
CYAN    := \033[0;36m
BOLD    := \033[1m
NC      := \033[0m

# Готовые префиксы сообщений — убирают дублирование ANSI в сотнях printf.
INFO    := ${BLUE}${BOLD}[INFO]${NC} ${CYAN}
OK      := ${GREEN}${BOLD}[v]${NC} ${GREEN}
WARN    := ${YELLOW}${BOLD}[!]${NC} ${YELLOW}
ERR     := ${RED}${BOLD}[x]${NC} ${RED}

# ════════════════════════════════════════════════════════════
# ПОДКЛЮЧЕНИЕ МОДУЛЕЙ
# ════════════════════════════════════════════════════════════

include makefiles/safety.mk
include makefiles/container.mk
include makefiles/help.mk
include makefiles/docker.mk
include makefiles/rust.mk
include makefiles/nvidia.mk
include makefiles/elevation.mk
include makefiles/simulation.mk
include makefiles/controller.mk
include makefiles/navigation.mk
include makefiles/yolo.mk
include makefiles/experiment.mk
include makefiles/ci.mk
include makefiles/test.mk

# ════════════════════════════════════════════════════════════
# DEFAULT TARGET
# ════════════════════════════════════════════════════════════

.DEFAULT_GOAL := help
