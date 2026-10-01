# makefiles/nvidia.mk
# Проверка и установка nvidia-container-toolkit для GPU-контейнеров

.PHONY: nvidia-check nvidia-install

NVIDIA_TOOLKIT_MARKER := /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

# Проверка, установлен ли nvidia-container-toolkit
define require-nvidia-toolkit
	@if ! command -v nvidia-ctk &>/dev/null; then \
		printf "$(ERR)nvidia-container-toolkit не установлен.${NC}\n" >&2; \
		printf "$(WARN)Установите: make nvidia-install${NC}\n" >&2; \
		exit 1; \
	fi
	@if [ "$$(docker info --format '{{.Runtimes}}' 2>/dev/null | grep -c nvidia)" -eq 0 ]; then \
		printf "$(ERR)nvidia runtime не настроен в Docker.${NC}\n" >&2; \
		printf "$(WARN)Установите: make nvidia-install${NC}\n" >&2; \
		exit 1; \
	fi
	@printf "$(OK)nvidia-container-toolkit: OK${NC}\n"
endef

## Проверить, установлен ли nvidia-container-toolkit
nvidia-check:
	$(require-nvidia-toolkit)

## Установить nvidia-container-toolkit (требуется sudo)
nvidia-install:
	@printf "$(INFO)Установка nvidia-container-toolkit...${NC}\n"
	curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
		sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
	curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
		sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
		sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
	sudo apt-get update
	sudo apt-get install -y nvidia-container-toolkit
	sudo nvidia-ctk runtime configure --runtime=docker
	sudo systemctl restart docker
	@printf "$(OK)nvidia-container-toolkit установлен. Docker перезапущен.${NC}\n"
