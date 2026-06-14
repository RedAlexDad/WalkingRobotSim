#pragma once
#include <Eigen/Dense>
#include <array>

namespace quadropted {

using JointAngles = std::array<double, 12>;
using FootPositions = std::array<Eigen::Vector3d, 4>;

struct LegBasePositions {
    static Eigen::Vector2d get(int leg_index, double body_length, double body_width);
};

[[nodiscard]] Eigen::Vector3d compute_leg_fk_chain(double theta_hip, double theta_thigh, double theta_calf,
                                                   const Eigen::Matrix4d& T_base, const Eigen::Matrix4d& T_thigh_t,
                                                   const Eigen::Matrix4d& T_calf_t,
                                                   const Eigen::Matrix4d& T_foot) noexcept;

class ForwardKinematics {
  public:
    ForwardKinematics(double body_length, double body_width, double l1, double l2, double l3, double l4);
    [[nodiscard]] FootPositions forward_kinematics_all_legs(const std::vector<double>& joint_angles) const;
    [[nodiscard]] FootPositions forward_kinematics_all_legs(const JointAngles& joint_angles) const;

  private:
    double l1_, l2_, l3_, l4_;
    Eigen::Matrix4d T_thigh_t_, T_calf_t_, T_foot_;
    Eigen::Matrix4d T_base_[4]{};
};

}  // namespace quadropted
