# makefiles/help.mk

.PHONY: help

## Показать справку
help:
	@python3 $(PROJECT_ROOT)/scripts/help.py
