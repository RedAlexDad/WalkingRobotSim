//! Behavior state enum
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BehaviorState {
    Rest = 0,
    Trot = 1,
    Crawl = 2,
    Stand = 3,
}
