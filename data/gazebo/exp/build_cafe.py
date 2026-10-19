"""Текстурированная сцена кафе: мир, объекты и ракурсы."""
import json
import math
import os

BASE = "data/gazebo/exp"
SRC = "src/gazebo_sim/world/cafe.world"

TABLE_BBOX = [[-0.457, -0.457, 0.0], [0.457, 0.457, 0.775]]
CHAIR_BBOX = [[-0.289, -0.215, 0.0], [0.289, 0.298, 0.817]]
BOTTLE_BBOX = [[-0.064, -0.057, -0.003], [0.033, 0.01, 0.188]]
CAR_BBOX = [[-2.25, -0.875, 0.0], [2.25, 0.875, 1.48]]

TABLES = [(0.5, -1.6), (2.4, -5.5), (-1.5, -5.5), (2.4, -9.0), (-1.5, -9.0)]
CHAIRS = [(1.4, -2.4, 0.0), (0.2, -2.6, 0.6), (2.9, -4.6, -1.2),
          (-2.0, -4.6, 1.2), (2.9, -8.0, -1.2)]
BOTTLES = [(0.5, -1.3, 0.955), (2.4, -5.5, 0.972), (-1.5, -5.5, 0.972)]


def look(cam, target):
    dx, dy, dz = target[0] - cam[0], target[1] - cam[1], target[2] - cam[2]
    yaw = math.atan2(dy, dx)
    pitch = math.atan2(cam[2] - target[2], math.hypot(dx, dy))
    return [cam[0], cam[1], cam[2], 0.0, pitch, yaw]


VIEWS = [
    ("cafe_table1", (2.2, 0.8, 1.6), (0.9, -2.0, 0.6)),
    ("cafe_table2", (3.8, -3.0, 1.6), (2.4, -5.5, 0.6)),
    ("cafe_table3", (-2.8, -3.0, 1.6), (-1.5, -5.5, 0.6)),
    ("cafe_table4", (1.5, -6.8, 1.6), (2.4, -9.0, 0.6)),
    ("cafe_table5", (-0.5, -6.8, 1.6), (-1.5, -9.0, 0.6)),
    ("cafe_wide", (0.0, 2.4, 1.8), (0.0, -3.0, 0.8)),
    ("cafe_chair1", (2.4, -0.8, 1.4), (1.4, -2.4, 0.5)),
    ("cafe_bottle", (1.4, -0.2, 1.5), (0.5, -1.3, 1.0)),
    ("cafe_car", (0.0, -8.5, 1.6), (0.0, -13.0, 0.8)),
    ("cafe_chair2", (2.0, -4.0, 1.8), (2.9, -4.6, 0.5)),
    ("cafe_chair3", (-1.0, -4.0, 1.8), (-2.0, -4.6, 0.5)),
    ("cafe_chair4", (0.5, -7.5, 1.8), (2.9, -8.0, 0.5)),
]


def main():
    world = open(SRC, encoding="utf-8").read()
    world = world.replace('<world name="default">', '<world name="exp">')

    extra = []
    for i, (x, y, yaw) in enumerate(CHAIRS):
        if i == 0:
            continue
        extra.append(f'''    <include>
      <uri>model://chair</uri><name>chair_extra_{i}</name>
      <pose>{x} {y} 0 0 0 {yaw}</pose>
    </include>''')
    for i, (x, y, z) in enumerate(BOTTLES):
        if i == 0:
            continue
        extra.append(f'''    <include>
      <uri>model://mustard_bottle</uri><name>bottle_extra_{i}</name>
      <pose>{x} {y} {z} 0 0 0</pose>
    </include>''')

    camera = '''    <model name="camera">
      <static>false</static>
      <pose>0 2.4 1.8 0 0.1 4.7124</pose>
      <link name="link"><gravity>false</gravity>
        <sensor name="cam" type="camera">
          <update_rate>10</update_rate>
          <camera><horizontal_fov>1.047</horizontal_fov>
            <image><width>640</width><height>480</height><format>R8G8B8</format></image>
            <clip><near>0.1</near><far>100</far></clip>
          </camera>
          <always_on>1</always_on><topic>/camera/image</topic>
        </sensor>
      </link>
    </model>'''

    world = world.replace("</world>", "\n".join(extra) + "\n" + camera + "\n  </world>")
    open(os.path.join(BASE, "cafe_bench.world"), "w", encoding="utf-8").write(world)

    objects = []
    for i, (x, y) in enumerate(TABLES):
        objects.append({"name": f"table_{i}", "model": "cafe_table",
                        "class": "dining table", "pose": [x, y, 0.2, 0, 0, 0],
                        "bbox": TABLE_BBOX})
    for i, (x, y, yaw) in enumerate(CHAIRS):
        objects.append({"name": f"chair_{i}", "model": "chair",
                        "class": "chair", "pose": [x, y, 0.0, 0, 0, yaw],
                        "bbox": CHAIR_BBOX})
    for i, (x, y, z) in enumerate(BOTTLES):
        objects.append({"name": f"bottle_{i}", "model": "mustard_bottle",
                        "class": "bottle", "pose": [x, y, z, 0, 0, 0],
                        "bbox": BOTTLE_BBOX})
    objects.append({"name": "car_0", "model": "prius_hybrid", "class": "car",
                    "pose": [0.0, -13.0, 0.0, 0, 0, 1.57], "bbox": CAR_BBOX})

    views = [{"name": n, "pose": look(c, t)} for n, c, t in VIEWS]
    with open(os.path.join(BASE, "scene_cafe.json"), "w", encoding="utf-8") as f:
        json.dump({"objects": objects, "views": views}, f, ensure_ascii=False, indent=2)
    print("objects", len(objects), "views", len(views))
    print("classes", {c: sum(1 for o in objects if o["class"] == c)
                      for c in sorted({o["class"] for o in objects})})


if __name__ == "__main__":
    main()
