//! Command structure
#[derive(Debug, Clone)]
pub struct Command {
    pub velocity: [f64; 3],
    pub yaw_rate: [f64; 3],
    pub robot_height: f64,
    pub trot_event: bool,
    pub rest_event: bool,
    pub crawl_event: bool,
    pub stand_event: bool,
    pub center_event: bool,
}

impl Default for Command {
    fn default() -> Self {
        Self {
            velocity: [0.0; 3],
            yaw_rate: [0.0; 3],
            robot_height: -0.25,
            trot_event: true,
            rest_event: true,
            crawl_event: false,
            stand_event: false,
            center_event: false,
        }
    }
}
