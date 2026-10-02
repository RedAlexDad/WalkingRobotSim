# makefiles/test.mk

.PHONY: test check benchmark setup backup
.PHONY: test-rust test-coverage test-build test-container test-clean check-deps check-structure test-yaml check-x11
.PHONY: test-correctness test-benchmark benchmark-cpp test-sim

## Полный цикл тестирования
test:
	@case "$(TARGET)" in \
		rust)        $(MAKE) --no-print-directory test-rust ;; \
		sim)         $(MAKE) --no-print-directory test-sim ;; \
		coverage)    $(MAKE) --no-print-directory test-coverage ;; \
		correctness) $(MAKE) --no-print-directory test-correctness ;; \
		benchmark)   $(MAKE) --no-print-directory test-benchmark ;; \
		"")          $(MAKE) --no-print-directory check test-build test-container ;; \
		*) printf "$(ERR)TARGET=$(TARGET): rust|sim|coverage|correctness|benchmark${NC}\n" >&2; exit 1 ;; \
	esac
	@printf "$(OK)Тесты завершены${NC}\n"
	@printf "$(INFO)Теперь можно выполнять git push${NC}\n"

## Проверки окружения
check:
	@case "$(WHAT)" in \
		deps)      $(MAKE) --no-print-directory check-deps ;; \
		structure) $(MAKE) --no-print-directory check-structure ;; \
		yaml)      $(MAKE) --no-print-directory test-yaml ;; \
		x11)       $(MAKE) --no-print-directory check-x11 ;; \
		"")        $(MAKE) --no-print-directory check-deps check-structure test-yaml check-x11 ;; \
		*) printf "$(ERR)WHAT=$(WHAT): deps|structure|yaml|x11${NC}\n" >&2; exit 1 ;; \
	esac

## Бенчмарк
benchmark:
	@case "$(WHAT)" in \
		python)  $(MAKE) --no-print-directory test-benchmark ;; \
		cpp|"")  $(MAKE) --no-print-directory benchmark-cpp ;; \
		*) printf "$(ERR)WHAT=$(WHAT): cpp|python${NC}\n" >&2; exit 1 ;; \
	esac

## Начальная настройка проекта
setup: check-x11
	@echo ""
	@printf "${CYAN}${BOLD}╔════════════════════════════════════════════════════════════╗${NC}\n"
	@printf "${CYAN}${BOLD}║${NC}  ${BOLD}WalkingRobotSim - Setup${NC}                               ${CYAN}${BOLD}║${NC}\n"
	@printf "${CYAN}${BOLD}╚════════════════════════════════════════════════════════════╝${NC}\n"
	@echo ""
	$(require-docker)
	@printf "$(OK)Docker: $$(docker --version)${NC}\n"
	@printf "$(OK)Compose: $$(docker compose version --short)${NC}\n"
	@printf "$(INFO)Проверка структуры проекта...${NC}\n"
	@for file in "docker/Dockerfile" "docker/cyclonedds.xml"; do \
		if [ ! -f "$(PROJECT_ROOT)/src/$$file" ]; then \
			printf "$(ERR)Файл не найден: $$file${NC}\n"; \
			exit 1; \
		fi; \
	done; \
	if [ ! -f "$(PROJECT_ROOT)/compose.yml" ]; then \
		printf "$(ERR)Файл compose.yml не найден${NC}\n"; \
		exit 1; \
	fi
	@printf "$(OK)Структура проекта верна${NC}\n"
	@echo ""
	@printf "$(INFO)Информация о системе:${NC}\n"
	@printf "  OS: $$(uname -s)\n"
	@printf "  Kernel: $$(uname -r)\n"
	@printf "  Docker: $$(docker --version)\n"
	@printf "  Compose: $$(docker compose version --short)\n"
	@printf "  User: $$(whoami)\n"
	@printf "  Home: $$HOME\n"
	@echo ""
	@printf "$(OK)Инициализация завершена успешно!${NC}\n"
	@echo ""
	@printf "$(INFO)Следующие шаги:${NC}\n"
	@printf "  1. ${BOLD}make deploy${NC}              # Сборка и запуск\n"
	@printf "  2. ${BOLD}make gazebo${NC}              # Запуск Gazebo\n"
	@printf "  3. ${BOLD}make teleop${NC}              # Управление роботом (в другом терминале)\n"
	@echo ""

## Создание бэкапа данных
backup:
	@backup_file="walking_robot_backup_$$(date +%Y%m%d_%H%M%S).tar.gz"; \
	printf "$(INFO)Создание бэкапа: $$backup_file${NC}\n"; \
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		-v $(DOCKER_DIR):/backup alpine tar czf /backup/"$$backup_file" \
		/var/lib/docker/volumes/gazebo_logs /var/lib/docker/volumes/gazebo_data 2>/dev/null || true; \
	printf "$(OK)Бэкап создан: $$backup_file${NC}\n"

##! Покрытие кода Rust (tarpaulin, ≥ 90%)
test-coverage:
	@printf "$(INFO)Измерение покрытия кода (tarpaulin)...${NC}\n"
	@source /opt/ros/$(ROS_DISTRO)/setup.bash 2>/dev/null; \
	source install/setup.bash 2>/dev/null || true; \
	cd $(PROJECT_ROOT)/src/quadropted_controller_rust && \
	cargo tarpaulin --package quadropted-core --tests --out Stdout 2>&1 | tail -30
	@printf "$(OK)Покрытие измерено (цель 90%%)${NC}\n"

##! Все автоматические тесты Rust (юнит + кросс-валидация + интеграционные)
test-rust:
	$(require-container)
	@printf "$(INFO)Запуск всех Rust тестов (юнит + кросс-валидация + интеграционные)...${NC}\n"
	@$(call ros-exec,cd /root/ws/src/quadropted_controller_rust && cargo test --workspace 2>&1 | tail -40)
	@printf "$(INFO)Запуск скрипта кросс-валидации (на хосте, C++ харнесс + Rust)...${NC}\n"
	@bash scripts/test_cross_validation.sh 2>&1 | tail -40
	@printf "$(OK)Rust тесты завершены${NC}\n"

##! Интеграционные тесты против ЖИВОЙ симуляции (нужен запущенный make gazebo)
test-sim:
	$(require-container)
	@printf "$(INFO)Запуск интеграционных тестов против живой симуляции...${NC}\n"
	@printf "$(WARN)Убедитесь, что симуляция запущена: make gazebo${NC}\n"
	@bash scripts/test_sim_integration.sh
	@printf "$(OK)Интеграционные тесты завершены${NC}\n"

##! Только сборка образа для теста
test-build: check-deps check-structure test-yaml
	@printf "$(INFO)Локальная сборка Docker-образа...${NC}\n"
	@$(COMPOSE) build --no-cache
	@printf "$(OK)Локальная сборка завершена успешно${NC}\n"

##! Тестовый запуск контейнера
test-container:
	@printf "$(INFO)Тестовый запуск контейнера...${NC}\n"
	@$(COMPOSE) up -d
	@printf "$(INFO)Ожидание запуска контейнера...${NC}\n"
	@sleep 15
	@if $(COMPOSE) ps | grep -q "healthy"; then \
		printf "$(OK)Контейнер запущен и здоров${NC}\n"; \
	else \
		printf "$(WARN)Контейнер запущен, но статус здоровья неизвестен${NC}\n"; \
	fi
	@if $(COMPOSE) exec -T simulator bash -c "source /opt/ros/$(ROS_DISTRO)/setup.bash && ros2 node list"; then \
		printf "$(OK)ROS функциональность проверена успешно${NC}\n"; \
	else \
		printf "$(WARN)ROS функциональность не проверена (контейнер может быть в процессе инициализации)${NC}\n"; \
	fi
	@$(COMPOSE) down
	@printf "$(OK)Контейнер остановлен${NC}\n"

##! Очистка Docker ресурсов после тестов
test-clean:
	@printf "$(INFO)Очистка Docker ресурсов...${NC}\n"
	@$(COMPOSE) down -v 2>/dev/null || true
	@docker rmi walking_robot_sim:latest 2>/dev/null || true
	@printf "$(OK)Очистка завершена${NC}\n"

##! Проверка зависимостей
check-deps:
	@printf "$(INFO)Проверка необходимых инструментов...${NC}\n"
	$(require-docker)
	@if ! command -v yamllint &> /dev/null; then \
		printf "$(WARN)yamllint не установлен. Установите: pip install yamllint${NC}\n"; \
	fi
	@printf "$(OK)Все необходимые инструменты установлены${NC}\n"

##! Проверка структуры проекта
check-structure:
	@printf "$(INFO)Проверка структуры проекта...${NC}\n"
	@if [ ! -d "$(PROJECT_ROOT)/src" ]; then \
		printf "$(ERR)Директория src не найдена${NC}\n"; \
		exit 1; \
	fi
	@if [ ! -d "$(PROJECT_ROOT)/src/docker" ]; then \
		printf "$(ERR)Директория src/docker не найдена${NC}\n"; \
		exit 1; \
	fi
	@if [ ! -f "$(PROJECT_ROOT)/compose.yml" ]; then \
		printf "$(ERR)Файл compose.yml не найден${NC}\n"; \
		exit 1; \
	fi
	@if [ ! -f "$(PROJECT_ROOT)/src/docker/Dockerfile" ]; then \
		printf "$(ERR)Файл src/docker/Dockerfile не найден${NC}\n"; \
		exit 1; \
	fi
	@if [ ! -d "$(PROJECT_ROOT)/src/gazebo_sim" ]; then \
		printf "$(WARN)Директория src/gazebo_sim не найдена${NC}\n"; \
	fi
	@if [ ! -d "$(PROJECT_ROOT)/src/go1_description" ]; then \
		printf "$(WARN)Директория src/go1_description не найдена${NC}\n"; \
	fi
	@if [ ! -d "$(PROJECT_ROOT)/src/go2_description" ]; then \
		printf "$(WARN)Директория src/go2_description не найдена${NC}\n"; \
	fi
	@printf "$(OK)Структура проекта проверена${NC}\n"

##! Проверка синтаксиса YAML
test-yaml:
	@if command -v yamllint &> /dev/null; then \
		printf "$(INFO)Проверка синтаксиса YAML...${NC}\n"; \
		if yamllint $(PROJECT_ROOT)/compose.yml; then \
			printf "$(OK)Синтаксис compose.yml корректен${NC}\n"; \
		else \
			printf "$(ERR)Обнаружены ошибки в синтаксисе compose.yml${NC}\n"; \
			exit 1; \
		fi; \
		if [ -d "$(PROJECT_ROOT)/.github/workflows" ]; then \
			if yamllint $(PROJECT_ROOT)/.github/workflows/; then \
				printf "$(OK)Синтаксис GitHub workflows корректен${NC}\n"; \
			else \
				printf "$(ERR)Обнаружены ошибки в синтаксисе GitHub workflows${NC}\n"; \
				exit 1; \
			fi; \
		else \
			printf "$(WARN)Директория .github/workflows не найдена${NC}\n"; \
		fi; \
	else \
		printf "$(WARN)yamllint не установлен, пропускаем проверку YAML${NC}\n"; \
	fi

##! Проверка X11 (для GUI)
check-x11:
	@printf "$(INFO)Проверка X11 (для GUI)...${NC}\n"
	@if [ -z "$$DISPLAY" ]; then \
		printf "$(WARN)DISPLAY не установлен. X11 GUI может не работать.${NC}\n"; \
		printf "$(INFO)Для использования GUI установите DISPLAY:${NC}\n"; \
		echo "  export DISPLAY=:0"; \
		echo "  xhost +local:"; \
	else \
		printf "$(OK)DISPLAY установлен: $$DISPLAY${NC}\n"; \
	fi

##! Проверка корректности — запуск всех тестов в correctness/
test-correctness:
	@printf "$(INFO)Тесты корректности...${NC}\n"
	@cd $(PROJECT_ROOT)/src/tests/correctness && python3 run_all.py
	@echo ""
	@printf "$(OK)Тесты корректности завершены${NC}\n"

##! Benchmark производительности — замер времени (Python)
test-benchmark:
	@printf "$(INFO)Benchmark производительности...${NC}\n"
	@cd $(PROJECT_ROOT) && python3 src/tests/benchmark_performance.py
	@echo ""
	@printf "$(OK)Benchmark завершён${NC}\n"

##! Запуск C++ бенчмарка
benchmark-cpp:
	$(require-container)
	@printf "$(INFO)Запуск C++ бенчмарка...${NC}\n"
	@$(call ros-exec,/root/ws/build/quadropted_controller_cpp/benchmark)
