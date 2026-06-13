#include <gz/transport/Node.hh>
#include <gz/msgs/laserscan.pb.h>
#include <gz/msgs/pointcloud_packed.pb.h>
#include <chrono>
#include <cmath>
#include <cstring>
#include <functional>
#include <iostream>
#include <thread>

static const std::string kSubTopic = "/robot1/scan";
static const std::string kPubTopic = "/robot1/scan/points";

void cb(const gz::msgs::LaserScan &msg,
        gz::transport::Node::Publisher &pub)
{
  int v_count = msg.vertical_count();
  int h_count = msg.count();
  if (v_count < 1 || h_count < 1) return;

  int per_ring = h_count / v_count;
  if (per_ring < 1) return;

  double h_angle_min = msg.angle_min();
  double h_angle_step = msg.angle_step();
  double v_angle_min = msg.vertical_angle_min();
  double v_angle_max = msg.vertical_angle_max();
  double v_angle_step = (v_count > 1)
    ? (v_angle_max - v_angle_min) / (v_count - 1)
    : 0.0;
  double r_min = msg.range_min();
  double r_max = msg.range_max();

  // count valid points
  int n = 0;
  for (int vi = 0; vi < v_count; ++vi) {
    for (int hi = 0; hi < per_ring; ++hi) {
      int idx = vi * per_ring + hi;
      if (idx >= msg.ranges_size()) break;
      double r = msg.ranges(idx);
      if (r >= r_min && r <= r_max) ++n;
    }
  }
  if (n == 0) return;

  const int point_step = 12;
  std::string data;
  data.resize(n * point_step);
  int out = 0;

  for (int vi = 0; vi < v_count; ++vi) {
    double v_angle = v_angle_min + vi * v_angle_step;
    for (int hi = 0; hi < per_ring; ++hi) {
      int idx = vi * per_ring + hi;
      if (idx >= msg.ranges_size()) break;
      double r = msg.ranges(idx);
      if (r < r_min || r > r_max) continue;

      double h_angle = h_angle_min + hi * h_angle_step;
      float x = r * std::cos(v_angle) * std::cos(h_angle);
      float y = r * std::cos(v_angle) * std::sin(h_angle);
      float z = r * std::sin(v_angle);

      std::memcpy(&data[out * point_step], &x, 4);
      std::memcpy(&data[out * point_step + 4], &y, 4);
      std::memcpy(&data[out * point_step + 8], &z, 4);
      ++out;
    }
  }

  gz::msgs::PointCloudPacked cloud;
  cloud.mutable_header()->CopyFrom(msg.header());
  cloud.set_height(1);
  cloud.set_width(n);
  cloud.set_is_bigendian(false);
  cloud.set_point_step(point_step);
  cloud.set_row_step(n * point_step);
  cloud.set_is_dense(true);

  auto *fx = cloud.add_field();
  fx->set_name("x"); fx->set_offset(0);
  fx->set_datatype(gz::msgs::PointCloudPacked_Field::FLOAT32);
  fx->set_count(1);

  auto *fy = cloud.add_field();
  fy->set_name("y"); fy->set_offset(4);
  fy->set_datatype(gz::msgs::PointCloudPacked_Field::FLOAT32);
  fy->set_count(1);

  auto *fz = cloud.add_field();
  fz->set_name("z"); fz->set_offset(8);
  fz->set_datatype(gz::msgs::PointCloudPacked_Field::FLOAT32);
  fz->set_count(1);

  cloud.set_data(data);
  pub.Publish(cloud);
}

int main(int, char**)
{
  gz::transport::Node node;
  auto pub = node.Advertise<gz::msgs::PointCloudPacked>(kPubTopic);

  if (!pub) {
    std::cerr << "[laser_to_cloud] ERROR: Failed to advertise on " << kPubTopic << std::endl;
    return 1;
  }

  std::function<void(const gz::msgs::LaserScan&)> subCb =
    [pub](const gz::msgs::LaserScan &msg) mutable { cb(msg, pub); };

  // sleep(1) to ensure discovery
  std::this_thread::sleep_for(std::chrono::seconds(1));
  auto sub = node.Subscribe(kSubTopic, subCb);

  if (!sub) {
    std::cerr << "[laser_to_cloud] ERROR: Failed to subscribe to " << kSubTopic << std::endl;
    return 1;
  }

  std::cout << "[laser_to_cloud] INFO: LaserScan -> PointCloudPacked converter running" << std::endl;
  std::cout << "[laser_to_cloud] INFO:   Sub: " << kSubTopic << std::endl;
  std::cout << "[laser_to_cloud] INFO:   Pub: " << kPubTopic << std::endl;

  gz::transport::waitForShutdown();
  return 0;
}
