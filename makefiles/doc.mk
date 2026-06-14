# makefiles/doc.mk

.PHONY: doc doc-open

DOC_BUILD_DIR := $(PROJECT_ROOT)/build_doc
DOC_HTML := $(DOC_BUILD_DIR)/doxygen/html/index.html

## Собрать Doxygen документацию и открыть в браузере
doc:
	@printf "$(BLUE)$(BOLD)[INFO]$(NC) $(CYAN)Генерация Doxygen документации...$(NC)\n"
	@mkdir -p $(DOC_BUILD_DIR)
	@SRC=$(PROJECT_ROOT)/src/quadropted_controller_cpp && \
	  sed "s|@CMAKE_SOURCE_DIR@|$${SRC}|g; s|@CMAKE_CURRENT_SOURCE_DIR@|$${SRC}|g; s|@CMAKE_CURRENT_BINARY_DIR@|$(DOC_BUILD_DIR)|g" \
	  $${SRC}/doc/Doxyfile.in > $(DOC_BUILD_DIR)/Doxyfile && \
	  doxygen $(DOC_BUILD_DIR)/Doxyfile
	@printf "$(GREEN)$(BOLD)[v]$(NC) $(GREEN)Документация сгенерирована: file://$(DOC_HTML)$(NC)\n"
	@xdg-open $(DOC_HTML) 2>/dev/null || \
	  printf "$(YELLOW)$(BOLD)[!]$(NC) $(YELLOW)Не удалось открыть браузер. Откройте вручную:$(NC)\n  file://$(DOC_HTML)\n"

## Открыть уже сгенерированную документацию (без пересборки)
doc-open:
	@if [ -f $(DOC_HTML) ]; then \
		printf "$(GREEN)$(BOLD)[v]$(NC) $(GREEN)Открытие: file://$(DOC_HTML)$(NC)\n" && \
		xdg-open $(DOC_HTML) 2>/dev/null || \
		  printf "$(YELLOW)$(BOLD)[!]$(NC) $(YELLOW)Не удалось открыть браузер. Откройте вручную:$(NC)\n  file://$(DOC_HTML)\n"; \
	else \
		printf "$(RED)$(BOLD)[x]$(NC) $(RED)Документация не найдена. Запустите: make doc$(NC)\n"; \
		exit 1; \
	fi
