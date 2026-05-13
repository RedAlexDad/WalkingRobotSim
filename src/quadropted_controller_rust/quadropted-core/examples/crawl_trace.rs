use nalgebra::SMatrix;
use quadropted_core::controllers::crawl::gait::CrawlGaitController;

fn main() {
    let body_length = 0.3762;
    let body_width = 0.0935;
    let l2 = 0.0955;
    let dx_front = body_length * 0.5 + 0.02;
    let dx_back = body_length * 0.5;
    let dy = body_width * 0.5 + l2;

    let mut stance = SMatrix::<f64, 3, 4>::zeros();
    stance[(0, 0)] = dx_front;
    stance[(1, 0)] = -dy;
    stance[(0, 1)] = dx_front;
    stance[(1, 1)] = dy;
    stance[(0, 2)] = -dx_back;
    stance[(1, 2)] = -dy;
    stance[(0, 3)] = -dx_back;
    stance[(1, 3)] = dy;
    for leg in 0..4 {
        stance[(2, leg)] = -0.25;
    }

    let mut crawl = CrawlGaitController::new(0.55, 0.45, 0.02, stance);
    let cmd = [0.011, 0.0, 0.0];
    let mut current = stance;

    for tick in 1..=1260 {
        current = crawl.step(tick, &current, &cmd, -0.25);
        if tick % 60 == 0 {
            let contacts = crawl.contacts(tick);
            println!(
                "[RUNTIME_CRAWL_RUST_SIM] ticks={} phase={} sub={} contacts=[{},{},{},{}] cmd=[{:.4},{:.4},{:.4}] fr=({:.4},{:.4},{:.4}) fl=({:.4},{:.4},{:.4}) rr=({:.4},{:.4},{:.4}) rl=({:.4},{:.4},{:.4})",
                tick,
                crawl.phase_index(tick),
                crawl.subphase_ticks(tick),
                contacts[0], contacts[1], contacts[2], contacts[3],
                cmd[0], cmd[1], cmd[2],
                current[(0, 0)], current[(1, 0)], current[(2, 0)],
                current[(0, 1)], current[(1, 1)], current[(2, 1)],
                current[(0, 2)], current[(1, 2)], current[(2, 2)],
                current[(0, 3)], current[(1, 3)], current[(2, 3)],
            );
        }
    }
}
