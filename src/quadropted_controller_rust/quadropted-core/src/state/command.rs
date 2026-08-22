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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_command_default() {
        let cmd = Command::default();
        assert_eq!(cmd.velocity, [0.0; 3]);
        assert_eq!(cmd.yaw_rate, [0.0; 3]);
        assert_eq!(cmd.robot_height, -0.25);
        assert!(cmd.trot_event);
        assert!(cmd.rest_event);
        assert!(!cmd.crawl_event);
        assert!(!cmd.stand_event);
        assert!(!cmd.center_event);
    }

    #[test]
    fn test_command_clone_and_fields() {
        let mut cmd = Command::default();
        cmd.velocity = [0.05, 0.0, 0.0];
        cmd.yaw_rate = [0.0, 0.0, 0.1];
        cmd.crawl_event = true;
        let copy = cmd.clone();
        assert_eq!(copy.velocity, [0.05, 0.0, 0.0]);
        assert_eq!(copy.yaw_rate[2], 0.1);
        assert!(copy.crawl_event);
        assert_eq!(format!("{:?}", cmd).len() > 0, true);
    }
}
