# makefiles/ci.mk
#
# CI-проверки: по умолчанию запускаются все. Выбор одной — аргументом:
#   make ci-lint LINT=yaml            # только YAML
#   make ci-lint LINT=python          # только Python

.PHONY: ci-lint ci-lint-yaml ci-lint-python

# GNU make определяет встроенную переменную LINT=lint (для правила .c.lint),
# из-за чего `make ci-lint` без аргумента попадал в ветку ошибки. Отбрасываем
# это значение, сохраняя явные LINT=yaml / LINT=python.
LINT := $(filter-out lint,$(LINT))

## Полный CI lint (YAML + Python)
ci-lint:
	@case "$(LINT)" in \
		yaml)   $(MAKE) --no-print-directory ci-lint-yaml ;; \
		python) $(MAKE) --no-print-directory ci-lint-python ;; \
		"")     $(MAKE) --no-print-directory ci-lint-yaml ci-lint-python ;; \
		*) printf "$(ERR)Неизвестный LINT=$(LINT) (yaml|python)${NC}\n" >&2; exit 1 ;; \
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
