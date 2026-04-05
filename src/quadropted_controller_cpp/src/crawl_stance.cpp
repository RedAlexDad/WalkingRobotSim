#include "quadropted_controller_cpp/crawl_gait.hpp"

namespace quadropted {

Eigen::Vector3d CrawlStanceController::position_delta(const Eigen::Vector3d&) { return Eigen::Vector3d::Zero(); }
Eigen::Vector3d CrawlStanceController::next_foot_location(int, const Eigen::MatrixXd&, const Eigen::Vector3d&) {
    return Eigen::Vector3d::Zero();
}

} // namespace quadropted
