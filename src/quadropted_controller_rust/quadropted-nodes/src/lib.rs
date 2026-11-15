//! Quadropted ROS 2 Nodes
//!
//! Вся логика, которой не нужен живой rclrs-контекст, живёт в этих модулях и
//! покрыта юнит-тестами: конвертация скоростей, шаг контроллера ходьбы,
//! обработчики одометрии и сборка сообщений. Бинарники
//! (`robot_controller_node`, `odometry_node`, `cmd_vel_pub`) содержат только
//! связку с rclrs: узел, паблишеры, подписки, таймер и spin.

pub mod cmd_vel;
pub mod controller;
pub mod odometry;
pub mod params;
