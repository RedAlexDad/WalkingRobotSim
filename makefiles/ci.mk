# makefiles/ci.mk
#
# CI-проверки: по умолчанию запускаются все. Выбор одной — аргументом:
#   make ci-lint LINT=yaml            # только YAML
#   make ci-test TEST=cpp            # только C++

.PHONY: ci-lint ci-test ci-lint-yaml ci-lint-python ci-lint-cpp ci-test-cpp

## Полный CI lint (YAML + Python + C++)
ci-lint:
	@case "$(LINT)" in \
		yaml)   $(MAKE) --no-print-directory ci-lint-yaml ;; \
		python) $(MAKE) --no-print-directory ci-lint-python ;; \
		cpp)    $(MAKE) --no-print-directory ci-lint-cpp ;; \
		"")     $(MAKE) --no-print-directory ci-lint-yaml ci-lint-python ci-lint-cpp ;; \
		*) printf "$(ERR)Неизвестный LINT=$(LINT) (yaml|python|cpp)${NC}\n" >&2; exit 1 ;; \
	esac
	@printf "$(OK)CI lint пройден${NC}\n"

##! YAML lint (yamllint)
ci-lint-yaml:
	@printf "$(INFO)YAML lint (yamllint)...${NC}\n"
	@if command -v yamllint &> /dev/null; then \
		yamllint -c .yamllint .github/workflows/ && \
		yamllint -c .yamllint src/docker/*.yml && \
		printf "$(OK)YAML lint OK${NC}\n"; \
	else \
		pip install yamllint -q && \
		yamllint -c .yamllint .github/workflows/ && \
		yamllint -c .yamllint src/docker/*.yml && \
		printf "$(OK)YAML lint OK${NC}\n"; \
	fi

##! Python lint (ruff)
ci-lint-python:
	@printf "$(INFO)Python lint (ruff)...${NC}\n"
	@if command -v ruff &> /dev/null; then \
		ruff check src/ && \
		printf "$(OK)Python lint OK${NC}\n"; \
	else \
		pip install ruff -q && \
		ruff check src/ && \
		printf "$(OK)Python lint OK${NC}\n"; \
	fi

##! C++ format check (clang-format)
ci-lint-cpp:
	@printf "$(INFO)C++ format check (clang-format)...${NC}\n"
	@if command -v clang-format &> /dev/null; then \
		find src/quadropted_controller_cpp -name '*.hpp' -o -name '*.cpp' | \
			xargs clang-format --dry-run --Werror && \
		printf "$(OK)C++ format OK${NC}\n"; \
	else \
		printf "$(WARN)clang-format не установлен, пропускаем${NC}\n"; \
	fi

## Локальные CI тесты
ci-test:
	@case "$(TEST)" in \
		cpp|"") $(MAKE) --no-print-directory ci-test-cpp ;; \
		*) printf "$(ERR)Неизвестный TEST=$(TEST)${NC}\n" >&2; exit 1 ;; \
	esac
	@printf "$(OK)CI тесты пройдены${NC}\n"

##! C++ unit tests через Docker
ci-test-cpp:
	$(require-container)
	@printf "$(INFO)Запуск C++ unit тестов...${NC}\n"
	@docker exec $(CONTAINER_NAME) bash -c "\
		source /opt/ros/$(ROS_DISTRO)/setup.bash && \
		source /root/ws/install/setup.bash && \
		cd /root/ws && \
		colcon test --packages-select quadropted_controller_cpp && \
		colcon test-result --verbose"
	@printf "$(OK)C++ tests OK${NC}\n"
