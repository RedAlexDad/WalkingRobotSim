//! Параметрический тест: override из `--ros-args -p` реально меняет значения и
//! поведение узлов.
//!
//! В rclrs 0.7 override применяется только в момент `declare_parameter`, поэтому
//! тест поднимает настоящий rclrs-контекст с параметрами командной строки и
//! проверяет, что дескрипторы узлов видят override, а собранные из них
//! параметры попадают в поведение: `child_frame_id` одометрии, период таймера,
//! окно фильтра, состояние контроллера.
//!
//! Тест требует инициализированного ROS 2 (запускается внутри контейнера,
//! как и остальные тесты Rust: `make test-rust` / `cargo test --workspace`).

use std::time::Duration;

use quadropted_nodes::controller::SharedState;
use quadropted_nodes::odometry::OdomShared;
use quadropted_nodes::params::{ControllerParamHandles, OdometryParamHandles};
use rclrs::{Context, CreateBasicExecutor, InitOptions};

#[test]
fn parameter_overrides_change_node_values_and_behavior() {
    let args: Vec<String> = [
        "param_overrides_test",
        "--ros-args",
        "-p",
        "publish_rate:=25",
        "-p",
        "base_frame_id:=base",
        "-p",
        "stall_window:=11",
        "-p",
        "stall_ang_vel_threshold:=0.02",
        "-p",
        "stall_exit_ang_vel_threshold:=0.04",
        "-p",
        "filter_window_size:=7",
        "-p",
        "enable_odom_tf:=true",
        "-p",
        "use_imu:=true",
        "-p",
        "robot_height:=-0.3",
        "-p",
        "control_period_ms:=20",
        "-p",
        "startup_grace_ticks:=5",
    ]
    .iter()
    .map(|s| s.to_string())
    .collect();

    let ctx = Context::new(args, InitOptions::new()).expect("rclrs context");
    let executor = ctx.create_basic_executor();
    let node = executor
        .create_node("param_overrides_test_node")
        .expect("create rclrs node");

    // ── Одометрия: override виден и меняет сообщения/таймер ──────────────
    let odom_handles = OdometryParamHandles::declare(&node).expect("declare odometry params");
    let odom_params = odom_handles.to_params();
    assert_eq!(odom_params.publish_rate, 25, "publish_rate из override");
    assert_eq!(odom_params.base_frame_id, "base");
    assert_eq!(odom_params.stall_window, 11);
    assert!((odom_params.stall_ang_vel_threshold - 0.02).abs() < 1e-12);
    assert!((odom_params.stall_exit_ang_vel_threshold - 0.04).abs() < 1e-12);
    assert_eq!(odom_params.filter_window_size, 7);
    assert!(odom_params.enable_odom_tf);
    // Поведение: 25 Гц даёт период 40 мс, окно фильтра уходит в состояние.
    assert_eq!(odom_params.timer_period(), Duration::from_millis(40));
    let shared = OdomShared::new(&odom_params);
    assert_eq!(shared.state.filter_window_size, 7);
    assert_eq!(shared.state.stall_window, 11);
    let odom_msg = shared.build_odom(0, 0);
    assert_eq!(odom_msg.header.frame_id.to_string(), "odom");
    assert_eq!(
        odom_msg.child_frame_id.to_string(),
        "base",
        "child_frame_id должен прийти из override base_frame_id"
    );
    assert!(odom_handles.enable_odom_tf());

    // ── Контроллер: override виден и меняет состояние/темп цикла ─────────
    let ctrl_handles = ControllerParamHandles::declare(&node).expect("declare controller params");
    let ctrl_params = ctrl_handles.to_params();
    assert!(ctrl_params.use_imu, "use_imu из override");
    assert!((ctrl_params.robot_height + 0.3).abs() < 1e-12);
    assert_eq!(ctrl_params.control_period_ms, 20);
    assert_eq!(ctrl_params.control_period(), Duration::from_millis(20));
    assert_eq!(ctrl_params.startup_grace_ticks, 5);

    let mut state = SharedState::with_params(&ctrl_params);
    for _ in 0..5 {
        assert!(
            state.control_tick(0.0).is_none(),
            "пауза старта должна длиться startup_grace_ticks"
        );
    }
    let out = state
        .control_tick(0.0)
        .expect("после паузы контроллер тикает");
    assert_eq!(out.angles.len(), 12);
    assert!((state.robot_height() + 0.3).abs() < 1e-12);
}
