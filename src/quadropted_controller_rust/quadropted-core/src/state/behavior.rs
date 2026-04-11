//! Behavior State — Robot operating modes
//!
//! Direct translation from C++ `state_command.hpp`.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BehaviorState {
    REST,
    TROT,
    CRAWL,
    STAND,
}

impl Default for BehaviorState {
    fn default() -> Self {
        BehaviorState::REST
    }
}

impl BehaviorState {
    /// Parse from string (case-insensitive)
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_uppercase().as_str() {
            "REST" => Some(BehaviorState::REST),
            "TROT" => Some(BehaviorState::TROT),
            "CRAWL" => Some(BehaviorState::CRAWL),
            "STAND" => Some(BehaviorState::STAND),
            _ => None,
        }
    }

    /// Convert to string
    pub fn as_str(&self) -> &'static str {
        match self {
            BehaviorState::REST => "REST",
            BehaviorState::TROT => "TROT",
            BehaviorState::CRAWL => "CRAWL",
            BehaviorState::STAND => "STAND",
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_behavior_state_default() {
        assert_eq!(BehaviorState::default(), BehaviorState::REST);
    }

    #[test]
    fn test_behavior_state_from_str() {
        assert_eq!(BehaviorState::from_str("REST"), Some(BehaviorState::REST));
        assert_eq!(BehaviorState::from_str("trot"), Some(BehaviorState::TROT));
        assert_eq!(BehaviorState::from_str("CRAWL"), Some(BehaviorState::CRAWL));
        assert_eq!(BehaviorState::from_str("Stand"), Some(BehaviorState::STAND));
        assert_eq!(BehaviorState::from_str("invalid"), None);
    }

    #[test]
    fn test_behavior_state_as_str() {
        assert_eq!(BehaviorState::REST.as_str(), "REST");
        assert_eq!(BehaviorState::TROT.as_str(), "TROT");
        assert_eq!(BehaviorState::CRAWL.as_str(), "CRAWL");
        assert_eq!(BehaviorState::STAND.as_str(), "STAND");
    }
}
