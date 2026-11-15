# Аудит миграции C++ → Rust и план добивания (2026-11-15)

**Задача:** `task-9` (kickoff-аудит, read-only по коду).
**HEAD:** `924bb20` (`feat/ergonomics-rviz-demo`); рабочее дерево содержит несвязанные правки (`.gitignore`, `docs/NIRS/*`, untracked `.Knowledge/` и `flow2spec.config.json`), файлы Rust чистые.
**Метод:** чтение документации, кода, git-истории; запуски в контейнере `walking_robot_sim` (`cargo build`, `cargo test`, C++ gtest-бинари, инспекция `install/`, образа). Код, конфиги и другие отчёты не изменялись; этот файл — единственный новый артефакт.

---

## 1. Вердикт

**Факт.** Rust-стек — основной в дефолтном запуске: `make gazebo` → `gazebo-rust` (`makefiles/simulation.mk:73,79`) → `launch.launch.py` → `gazebo_multi_nav2_rust.launch.py`, где запускаются `quadropted_controller_rust/robot_controller_node` и `odometry_node` (`src/gazebo_sim/launch/gazebo_multi_nav2_rust.launch.py:188,217`).

**Факт.** Объём: 5403 строки Rust в `src/quadropted_controller_rust` (3643 core + 681 nodes, включая `build.rs` 16 + 1032 тестов + 47 в примере), плюс 1767 строк в 7 крейтах сообщений. Тестов — 144 `#[test]`: 115 lib + 21 cross-validation + 4 CRAWL + 4 odometry.

**Факт.** На текущем HEAD `cargo test --workspace` **не компилируется** (exit 101): в `quadropted-core/src/math/transform.rs:5` импорт без `Vector4`, а тесты используют его в строках 94 и 104. Импорт удалён коммитом `4616f8c` (2026-10-02, «устранить warnings»), которого нет в `feat/rust-migration`, но который есть в HEAD. В копии дерева с восстановленным импортом все 144 теста проходят (115+21+4+4, 0 failed).

**Вывод.** «Миграция завершена» в документах означает «Rust-контроллер функционально заменяет C++ в дефолтном запуске». Это подтверждается для контроллера и одометрии. Как утверждение «C++ устранён / миграция проекта закончена» — неверно: в дефолтном launch остаётся C++-узел `cmd_vel_pub` (`gazebo_multi_nav2_rust.launch.py:290-295`), C++-пакет собирается в образе и обязателен для дефолтного launch и 21 кросс-валидационного теста, а тестовое состояние на HEAD — красное.

**Вывод.** Заявленные «92% → 97,4%» — не прогресс одной метрики: 92% — это чек-лист «12/13 компонентов» (`docs/rust-migration-status.md:168`), 97,34% — покрытие строк tarpaulin (`docs/rust-migration-final-report.md:278`). Сравнивать их нельзя; актуальность tarpaulin-числа в этой сессии не подтверждена (инструмент не установлен).

**Итоговая оценка:** контроллер — мигрирован (с отклонениями); одометрия — мигрирована (частично по параметрам); полное устранение C++ и подтверждённое зелёное состояние — не выполнены.

---

## 2. Матрица компонентов

| C++ (источник) | Rust-эквивалент | Статус | Доказательство / примечание |
|---|---|---|---|
| `src/utils/rotation_matrices.cpp:7-28` rotx/roty/rotz/rotxyz | `quadropted-core/src/math/rotation.rs:8-40` | перенесён | кросс-валидация < 1e-12 (`tests/cross_validation.rs`) |
| `src/utils/homogeneous_transforms.cpp:5-26` | `math/transform.rs:8-28` | перенесён | кросс-валидация < 1e-12; тесты сломаны на HEAD (см. §1) |
| `src/kinematics/forward_kinematics.cpp:9,54` | `kinematics/forward.rs:25,60` | перенесён | `compute_leg_fk_chain`, `forward_kinematics_all_legs` |
| `src/kinematics/inverse_kinematics.cpp:11,62,144` | `kinematics/inverse.rs:17,78,101,128` | перенесён, с допуском | IK сверяется с допуском 2e-3 из-за `fast_atan2` в C++ (`final-report:232-234`) |
| `src/controllers/gait_controller.cpp:5-66` | `controllers/gait.rs:9-92` | перенесён | фазы/контакты/phase_index |
| `src/controllers/trot/trot_gait.cpp:16` | `controllers/trot/gait.rs:70` | перенесён | step + 21 cross-val |
| `src/controllers/trot/trot_stance.cpp:18-31` | `controllers/trot/stance.rs:29,45` | перенесён | < 1e-9 |
| `src/controllers/trot/trot_swing.cpp:20-40` | `controllers/trot/swing.rs:38,56,65` | перенесён | < 1e-9 |
| `src/controllers/crawl/crawl_gait.cpp:21` (`step`) | `controllers/crawl/gait.rs:88` (`step`) | перенесён с отклонением | Rust повторяет **рантайм-путь** C++-ноды `step_crawl` (`src/control/crawl_control.cpp:17-34`), а не библиотечный `CrawlGaitController::step`, который нода не вызывает |
| `src/controllers/crawl/crawl_stance.cpp:19` | `controllers/crawl/stance.rs:31` | перенесён | бит-в-бит по `test_crawl_rust_matches_cpp_runtime_bit_exact` |
| `src/controllers/crawl/crawl_swing.cpp:21-61` | `controllers/crawl/swing.rs:41,66,78` | перенесён | `shifted_left` жёстко `false`, как в C++ (`crawl_swing.cpp:58`) |
| `src/controllers/rest_controller.cpp:15` | `controllers/rest.rs:39` | перенесён | есть расхождение дефолта `use_imu` (C++ `false`, Rust `true`) — задокументировано в `final-report:247` |
| `src/controllers/stand_controller.cpp:9` | `controllers/stand.rs:37` | перенесён | — |
| `src/controllers/pid_controller.cpp:7-49` | `controllers/pid.rs:33-73` | перенесён | `max_i` выровнен 1.0→0.2 (`final-report:246`) |
| `src/states/state_command.cpp` (2 строки, пустой TU) | `state/command.rs:3`, `state/behavior.rs:6` | перенесён | C++-файл — комментарий без кода |
| `src/nodes/robot_controller_node.cpp:10-301` | `quadropted-nodes/src/bin/robot_controller_node.rs` | перенесён с отклонениями | сервис `robot_behavior_command` (`:270`), grace 120 тиков (`:326`), foot_contact (`:183`); но PID считается по `SystemTime` (`:120-124,209-212`), высота тела жёстко `-0.25` (`:336`), параметров нет |
| `src/nodes/odometry_node.cpp:4-30` + `src/odometry/*.cpp` | `quadropted-nodes/src/bin/odometry_node.rs` + `odometry/state.rs:19`, `odometry/update.rs:20` | перенесён частично | те же 4 подписки, odom 50 Гц, stall, маркеры, параметры (`:66-75`); игнорируются `imu_topic`, `verbose`; TF — через `TFMessage` (`:256-271`); дефолт `base_frame_id` отличается (`base_link` vs C++ `base`, `odometry_node.cpp:8`) |
| `src/nodes/cmd_vel_pub.cpp:14-61` | — | **не перенесён** | единственный C++-узел в дефолтном Rust-launch; обязателен для Nav2 и `make teleop` |
| `src/utils/fast_math.hpp` | — | не перенесён (осознанно) | Rust использует точный `atan2`; отсюда допуск IK 2e-3 |
| `src/utils/message_builders.cpp` | — | не перенесён (в рантайме не используется) | единственный потребитель — `test/test_message_builders.cpp:5`; в графе нод не участвует |
| `benchmark/*` | — | не перенесён | C++-бенчмарк остаётся; Rust-бенчмарка нет |
| `test/cpp_xval_harness.cpp` | — | остаётся референсом | C++-эталон для 21 Rust-теста (`tests/cross_validation.rs:16-40`) |

**Вывод по матрице.** Ядро алгоритмов, все четыре походки, state machine и обе ноды мигрированы. Не мигрированы: входной мост `cmd_vel_pub`, бенчмарк и «мёртвые» утилиты C++. Отклонения по нодам — не математика, а время/PID, параметры и QoS.

*Сокращение `final-report` в таблице = `docs/rust-migration-final-report.md`.*

---

## 3. Реестр остаточных зависимостей Rust-стека от C++

| Зависимость | Где | Зачем нужна | Что мешает убрать |
|---|---|---|---|
| Узел `quadropted_controller_cpp/cmd_vel_pub` | `gazebo_multi_nav2_rust.launch.py:290-295,334`; `launch_core.py:125-128,154`; `per_robot_bringup.launch.py:278` | Конвертирует `geometry_msgs/Twist` (`cmd_vel`) → `quadropted_msgs/RobotVelocity` и применяет нелинейное масштабирование 0.035/0.012 (`cmd_vel_pub.cpp:53-61`) | Nav2 публикует `cmd_vel`; `make teleop` по умолчанию идёт через Twist (`scripts/robot_teleop.py:56-58`). Rust-порт не написан |
| Пакет `quadropted_controller_cpp` в colcon | `src/docker/Dockerfile:208-211`; `CMakeLists.txt` пакета | Сборка `cmd_vel_pub`, `cpp_xval_harness`, C++-тестов; `make gazebo-cpp` | Удаление пакета ломает дефолтный launch и 21 кросс-валидационный тест |
| C++ `cpp_xval_harness` | `src/quadropted_controller_cpp/CMakeLists.txt:96`; `tests/cross_validation.rs:16-40` | JSON-эталон реального C++ для 21 теста | Нет альтернативного эталона (golden JSON не завендорен) |
| C++-ноды `robot_controller_node`, `odometry_node` | `launch_cpp.launch.py` → `gazebo_multi_nav2_cpp.launch.py` → `per_robot_bringup.launch.py:203,212` | Референс для сравнения (`make gazebo-cpp`) | Нужны для регрессионного сравнения поведения |
| C++ unit-тесты (63 в 12 бинарях) | `quadropted_controller_cpp/CMakeLists.txt:75-82`; `scripts/test_cross_validation.sh:55-85`; CI job `cpp-tests` | Проверка референса | Удаление C++ убирает и референс |
| Rust-сборка через CMake | `quadropted_controller_rust/CMakeLists.txt:16-30` | `colcon build` вызывает `cargo build --release` на configure-этапе | Нет colcon-cargo; изменение `.rs` не триггерит пересборку — нужен `make rust-build` (`makefiles/rust.mk:3-14`, `scripts/build-rust.sh:22-23`) |
| Docker-стадия `ros-deps` с rustup | `src/docker/Dockerfile:184-186` | Rust toolchain для `cargo build` в образе | Версия Rust не закреплена; `Cargo.lock` не копируется из git |
| «Мёртвые» launch/пакеты | `launch_core.py` (не включён ни одним launch); `ros2_rust_pubsub_test/COLCON_IGNORE`; `install/rclrs`, `install/rosidl_generator_rs`, `install/test_msgs` | — | Мусор от прежних экспериментов; путает аудит зависимостей |

**Вывод.** Единственная **рантайм**-зависимость Rust-стека от C++ — `cmd_vel_pub`. Остальные — сборочные/тестовые/референсные.

---

## 4. Пробелы

### 4.1 Тесты и покрытие

- **Факт.** 144 `#[test]`; на HEAD компиляция падает (`error[E0433]: cannot find type Vector4`, `transform.rs:94,104`). `cargo build --release --workspace` при этом успешен.
- **Факт.** В копии дерева в контейнере с восстановленным импортом: `115 passed` (lib), `21` (cross_validation), `4` (CRAWL), `4` (odometry) — 0 failed.
- **Факт.** Документы фиксируют 32 (`docs/rust-migration-report.md:21`), 38 (`docs/rust-migration-status.md:148`), 46 (`docs/rust-fix-report-2026-04-11.md:104`), 58 (`reports/rust-migration/RUST_MIGRATION_STATUS.md:16`) тестов; коммит `db7f9a0` — 115 (`git show db7f9a0`), фактически — 144.
- **Факт.** Покрытие 97,34/97,40% (`final-report:278`, `reports/testing/2026-08-22_integration-testing-report.md:437`) сейчас не воспроизводится: `cargo tarpaulin` в контейнере не установлен (`no such command: tarpaulin`), артефактов покрытия в репозитории нет, `make test-coverage` (`makefiles/test.mk:89-95`) требует tarpaulin на хосте.
- **Вывод.** На HEAD утверждение «144 теста зелёные» ложно. На tip ветки `feat/rust-migration` блокирующей ошибки импорта не было (`Vector4` удалён позже, коммитом `4616f8c`), но полный прогон именно tip в этой сессии не выполнялся. Покрытие — непроверяемая цифра.

### 4.2 CI

- **Факт.** Job `rust-tests` существует (`.github/workflows/ci.yml:134`), запускает `cargo build`, `cargo test --workspace` (`:199`), C++-харнесс и C++-тесты.
- **Факт.** Триггеры — только `main` и `jazzy_cpp` (`ci.yml:4-7`). `feat/rust-migration` не является предком `main`/`jazzy_cpp` (`git merge-base --is-ancestor` → no); ветка влита только в цепочку feature-веток, включая текущий HEAD.
- **Вывод.** Автоматически `rust-tests` на этом коде не запускается; зелёный CI к нему не относится. Вручную — только `workflow_dispatch`.
- **Факт.** Зелёность маскируется: `makefiles/test.mk:101` делает `cargo test ... | tail -40` (код возврата — у `tail`); `scripts/test_cross_validation.sh:92-137` при ошибке компиляции получает 0 passed / 0 failed и печатает `[PASS] ... 0 passed`. Тест-гейт не отличает «0 тестов» от «все прошли».

### 4.3 Документация

| Документ | Заявлено | Расхождение |
|---|---|---|
| `docs/rust-migration-plan.md:655,690` | 25/32 (78%), 32 теста | устарел (апрель) |
| `docs/rust-migration-report.md:5,21` | 15/16 (94%), 32 теста | устарел |
| `docs/rust-migration-status.md:147-148,168` | 12/13 (92%), 38 тестов | устарел |
| `docs/rust-fix-report-2026-04-11.md:104,231` | 10/13 (77%), 46 тестов | устарел; описывает `shifted_left`/`first_cycle`, позже откатанные |
| `reports/rust-migration/RUST_MIGRATION_COMPLETE.md:4,97` | 92%, 38 тестов | устарел |
| `reports/rust-migration/RUST_MIGRATION_STATUS.md:5,16,19` | «Завершено», 58 тестов, 97,34% | 144 теста; `cmd_vel_pub` — рантайм-зависимость |
| `docs/rust-migration-final-report.md:5,18,304` | «Миграция завершена», 58 тестов, 97,34% | 144 теста; на HEAD тесты красные; C++ не устранён |
| `reports/testing/2026-08-22_integration-testing-report.md:432,437` | 88 тестов, 97,40% | снято до коммита `db7f9a0` (115) в тот же день; сейчас 144 |
| `docs/architecture.md:45,95` | «C++ контроллер 53.5x быстрее Python»; `/robot1/cmd_vel → Controller` | Rust — основной; контроллер подписан на `robot_velocity`, а не `cmd_vel` |
| `docs/ci-cd.md:9` | триггеры `main`/`jazzy` | фактически `main`/`jazzy_cpp` |

**Вывод.** Нет единого источника истины о статусе; документы дают пять разных цифр тестов (32, 38, 46, 58, 88), а «степень завершённости» варьируется от 77% до 100%. «Завершено» в двух отчётах противоречит и коду (C++-узел в launch), и тестам (HEAD red).

### 4.4 Layout `install/` vs `target/release`

- **Факт.** На хосте `install/` не содержит `quadropted_controller_rust` (есть только `quadropted_controller_cpp`, `quadropted_msgs`, `quadropted_perception`); бинари лежат только в `src/quadropted_controller_rust/target/release/` (`robot_controller_node`, `odometry_node`, от 2026-10-26).
- **Факт.** В контейнере `install/quadropted_controller_rust/lib/...` — симлинки на `/root/ws/src/.../target/release/...` (проверено `ls -la`). `/root/ws/src` — volume `project_src`, bind на `./src` (`compose.yml:120,274-280`).
- **Факт.** `CMakeLists.txt:16-30` собирает cargo на configure и устанавливает `PROGRAMS` (фактически симлинки); `makefiles/rust.mk:3-14` и `scripts/build-rust.sh:22-23` требуют отдельного `make rust-build` после правок.
- **Вывод.** Это не «установленный пакет», а симлинк-ферма на host-артефакт: свежий клон без `target/` даёт битые симлинки до первого `rust-build`; образ и хост-дерево расходятся.

### 4.5 `release.yml`

- **Факт.** `.github/workflows/release.yml:22-30` собирает `target/release/audiosub` с фичами `whisper,tui` и `libpulse-dev/libasound2-dev` — это workflow другого проекта.
- **Вывод.** По тегу `v*` он либо упадёт, либо выпустит не тот артефакт. К миграции отношения не имеет, но вводит в заблуждение и должен быть удалён/заменён.

### 4.6 Воспроизводимость сборки

- **Факт.** `Cargo.lock` не отслеживается: `.gitignore:99-100` (`**/Cargo.lock`) и `:143` (`*.lock`); в git есть только `src/ros2_rust_pubsub_test/Cargo.lock`. `Cargo.toml` использует диапазоны (`rclrs = "0.7"`, `rosidl_runtime_rs = "0.6"`, `nalgebra = "0.33"`); Dockerfile ставит rustup без версии (`Dockerfile:184-186`); CI — без `--locked`.
- **Факт.** `.dockerignore` в корне отсутствует; есть `src/dockerignore`, который Docker не читает (файл вне контекста с таким именем). В результате образ содержит `target/` (проверено: 555 МБ в `/root/ws/src/quadropted_controller_rust/target` внутри образа), а контекст сборки — порядка 24 ГБ.
- **Вывод.** Сборка не воспроизводима (плавающие версии), медленна (контекст/`target`) и может переиспользовать чужие артефакты.

### 4.7 Мёртвый код и мусор

- **Факт.** `CrawlGaitController::step` (`src/controllers/crawl/crawl_gait.cpp:21`) не вызывается ни из ноды, ни из тестов; нода использует `step_crawl` (`src/control/crawl_control.cpp:17-34`). Это и есть «мёртвый CRAWL»: не весь CRAWL, а библиотечный `step`.
- **Факт.** `message_builders` в рантайме не вызывается (единственный потребитель — `test/test_message_builders.cpp:5`, через старый заголовок-форвардер); `state_command.cpp` — комментарий без кода; `launch_core.py` не включается ни одним launch-файлом.
- **Факт.** `install/` содержит `rclrs`, `rosidl_generator_rs`, `test_msgs`, `ros2_rust_pubsub_test` (апрель), хотя `ros2_rust_pubsub_test/COLCON_IGNORE` исключён из сборки.

---

## 5. Приоритизированный бэклог

| ID | Действие | Файлы | Оценка | Критерий приёмки | Зависимости |
|---|---|---|---|---|---|
| **P0-1** | Вернуть `Vector4` в импорт и получить зелёный `cargo test --workspace` | `quadropted-core/src/math/transform.rs:5` | 5 мин + прогон | exit 0: 115 lib + 21 cross + 4 + 4, 0 failed | нет |
| **P0-2** | Сделать тест-гейт честным: `set -o pipefail`, падать при 0 passed / ошибке компиляции; добавить ветку в триггеры CI | `makefiles/test.mk:101`, `scripts/test_cross_validation.sh:92-137`, `.github/workflows/ci.yml:4-7` | 2–4 ч | сломанный тест даёт non-zero в `make test-rust` и в CI; CI запускается на PR/ветке | P0-1 |
| **P0-3** | Портировать `cmd_vel_pub` в Rust (Twist→RobotVelocity + та же кривая 0.035/0.012) и убрать C++-узел из дефолтного launch | новый bin в `quadropted-nodes`; `gazebo_multi_nav2_rust.launch.py:290-295,334`; `launch_core.py:125-128`; `per_robot_bringup.launch.py:278` | 0,5–1 день | `ros2 node list` в `make gazebo` не содержит `cmd_vel_pub_cpp`; скорость teleop/Nav2 совпадает с эталоном | P0-1 (иначе нечем проверить) |
| **P1-1** | Свести документацию к одному источнику статуса; пометить старые отчёты историей; исправить `architecture.md`/`ci-cd.md` | 8 документов из §4.3 | 0,5 дня | один актуальный статус, цифры совпадают с кодом, «завершено» заменено на измеримые критерии | P0-1, P0-3 |
| **P1-2** | Завендорить `Cargo.lock`, закрепить версию Rust, собирать с `--locked` | `.gitignore:99-100,143`, `Cargo.toml`, `Dockerfile:184-186`, `ci.yml` | 2–3 ч | чистая сборка даёт те же версии; CI падает при расхождении lock | P0-1 |
| **P1-3** | Перенести `.dockerignore` в корень; исключить `target/`, `build/`, `install/`, логи | новый `.dockerignore` (переименовать `src/dockerignore`) | 1 ч | образ не содержит host-`target`; контекст < 1 ГБ | нет |
| **P1-4** | Покрытие в CI (tarpaulin/llvm-cov) с порогом; сохранять отчёт | `makefiles/test.mk:89-95`, `ci.yml` | 0,5 дня | покрытие измеряется на каждом прогоне и падает при < 90% | P0-2 |
| **P1-5** | Удалить/переписать `release.yml` под этот проект | `.github/workflows/release.yml` | 1–2 ч | тег `v*` не собирает `audiosub` | нет |
| **P1-6** | Убрать мёртвый код и мусор: `CrawlGait::step`, `message_builders`, `state_command.cpp`, `launch_core.py`, старые артефакты `install/` | см. §4.7 | 0,5 дня | grep не находит потребителей; сборка/тесты зелёные | P0-1 |
| **P2-1** | Паритет параметров и времени: ROS-время вместо `SystemTime` в PID, `imu_topic`/`verbose`, `robot_height` из параметра, QoS как в C++ | `robot_controller_node.rs:120-124,209-212,336`; `odometry_node.rs:66-75,132` | 2–3 дня | поведение под sim-time и с паузой совпадает с C++; mixed-stack QoS совместим | P0-1 |
| **P2-2** | Rust-вариант `per_robot_bringup` для мультиробота | `per_robot_bringup.launch.py` | 2–3 дня | мультироботный запуск без C++-нод | P0-3 |
| **P2-3** | Портировать benchmark (или зафиксировать C++ как единственный) | `benchmark/*` | 1–2 дня | сравнение производительности в CI/отчёте | нет |
| **P2-4** | Полное удаление C++ после стабилизации: завендорить golden JSON, удалить пакет | `src/quadropted_controller_cpp/`, `tests/cross_validation.rs` | 3–5 дней | `make gazebo`/`test-rust` не требуют C++ | P0-3, P1-1…P1-6 |

**Порядок исполнения:** P0-1 → P0-2 → P0-3 → P1-1/P1-2/P1-3 (параллельно) → P1-4…P1-6 → P2.

---

## 6. Риски и открытые вопросы

**Риски.**

1. **Удаление C++ обрушит 21 кросс-валидационный тест** — они запускают реальный `cpp_xval_harness`. Без завендоренного эталона это единственный источник доверия к математике. (факт: `tests/cross_validation.rs:16-40`)
2. **Скрытая кривая масштабирования `cmd_vel_pub`** (0.035/0.012, экспоненциальное насыщение): наивный Rust-порт изменит скорость Nav2/teleop. Нужен golden-тест на значения. (факт: `cmd_vel_pub.cpp:53-61`)
3. **Красный тест-гейт** означает отсутствие регрессионного сигнала: любые правки Rust сейчас не проверяются. (факт: exit 101)
4. **`make gazebo` требует C++-пакет в образе**: если CI/Docker начнут собирать только Rust, дефолтный launch сломается. (вывод из §3)
5. **`SystemTime` в PID** расходится с ROS-временем C++: под sim-time/паузой поведение может отличаться, а тесты этого не ловят. (факт: `robot_controller_node.rs:120-124`; C++ `now.seconds()` — `robot_controller_node.cpp:154,160`)
6. **Неотслеживаемый `Cargo.lock` + плавающий rustup** дают невоспроизводимые сборки; «зелёно у меня» не переносится на CI. (факт: `.gitignore:99-100`)
7. **Документы «завершено»** могут привести к преждевременному удалению C++ и потере референса. (вывод)

**Открытые вопросы к Lead.**

1. C++-пакет — постоянный референс или удаляется после стабилизации? Каков критерий «C++ можно удалять»?
2. Кросс-валидация: сохраняем C++-харнесс навсегда или вендорим golden JSON и убираем C++ из тестов?
3. Кривая `cmd_vel_pub` — сохраняем пиксельно (golden-тест) или пересогласовываем скорость с Nav2?
4. Ветка `feat/rust-migration` в `main`: мержим как есть или сначала P0-1/P0-2? Меняем ли триггеры CI?
5. Покрытие: tarpaulin или llvm-cov, порог 90% или иной, где хранить отчёт?
6. Мультироботный `per_robot_bringup` (C++) — входит в миграцию или остаётся C++?
7. `release.yml` — удалить или переписать под проект?

---

## Метод и ограничения

- **Проверено запуском:** `cargo build --release --workspace` (успех); `cargo test --workspace` на HEAD (exit 101, ошибка `Vector4`); тот же тест в копии с восстановленным импортом (144 passed); C++ gtest-бинари (12/12 с `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`; с дефолтным `rmw_cyclonedds_cpp` в контейнере не стартуют из-за отсутствующего `libddsc.so.0` — дефект окружения, не тестов); инспекция `install/`, volume, образа.
- **Не проверялось:** живой запуск Gazebo/Nav2, tarpaulin-покрытие (инструмент отсутствует), фактические прогоны GitHub Actions, поведение под sim-time.
- **Ограничение задачи:** инструментов `team_task_get`/`team_task_update` в сессии нет (и файла доски в репозитории не найдено), поэтому claim/complete для `task-9` не выполнены — это должен сделать Lead или выдать инструмент.
