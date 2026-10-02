# makefiles/rust.mk
#
# Сборка Rust-контроллера. В контейнере install/.../robot_controller_node — симлинк
# на хостовый ./src/quadropted_controller_rust/target/release (bind-mount project_src),
# поэтому образ можно не пересобирать, но бинарник нужно пересобрать обязательно —
# иначе gazebo/teleop используют старую версию.

.PHONY: rust-build

## Пересобрать Rust-контроллер (robot_controller_node + odometry_node)
rust-build:
	$(require-container)
	@printf "$(INFO)Пересборка Rust-контроллера...${NC}\n"
	@$(PROJECT_ROOT)/scripts/build-rust.sh
	@printf "$(OK)Rust-контроллер собран${NC}\n"
