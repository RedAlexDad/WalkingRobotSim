"""Генерация сцены бенчмарка: 16 объектов, 9 COCO-классов, 24 ракурса."""
import json
import math
import os

R = 6.5
OUT = "data/gazebo/exp"

# model, class, local AABB (min, max), yaw offset, z-offset
OBJECTS = [
    # станция 0
    ("aws_robomaker_residential_ChairA_01", "chair", 0.0),
    # станция 1
    ("aws_robomaker_residential_KitchenTable_01", "dining table", 0.0),
    ("mustard_bottle", "bottle", None),  # на столе
    # станция 2
    ("aws_robomaker_residential_Bed_01", "bed", 0.0),
    # станция 3
    ("aws_robomaker_residential_Sofa_01", "couch", 0.0),
    # станция 4
    ("aws_robomaker_residential_ChairD_01", "chair", 0.0),
    # станция 5
    ("cafe_table", "dining table", 0.0),
    ("aws_robomaker_residential_Vase_01", "vase", None),
    # станция 6
    ("aws_robomaker_residential_Refrigerator_01", "refrigerator", 0.0),
    # станция 7
    ("aws_robomaker_residential_CoffeeTable_01", "dining table", math.pi / 2),
    ("aws_robomaker_residential_Vase_01", "vase", None),
    ("mustard_bottle", "bottle", None),
    # станция 8
    ("aws_robomaker_residential_TV_01", "tv", 0.0),
    # станция 9
    ("aws_robomaker_residential_SofaB_01", "couch", 0.0),
    # станция 10
    ("aws_robomaker_residential_Ball_01", "sports ball", 0.0),
    # станция 11
    ("aws_robomaker_residential_Ball_01", "sports ball", 0.0),
]

AABB = {
    "aws_robomaker_residential_ChairA_01": ([-0.219, -0.237, 0.0], [0.219, 0.237, 0.913]),
    "aws_robomaker_residential_ChairD_01": ([-0.287, -0.246, 0.0], [0.287, 0.246, 0.775]),
    "aws_robomaker_residential_KitchenTable_01": ([-0.35, -0.9, 0.0], [0.35, 0.9, 0.801]),
    "aws_robomaker_residential_CoffeeTable_01": ([-0.651, -0.324, 0.0], [0.664, 0.331, 0.322]),
    "aws_robomaker_residential_Bed_01": ([-1.018, -1.0, 0.0], [1.018, 1.0, 1.26]),
    "aws_robomaker_residential_Sofa_01": ([-1.21, -1.222, 0.0], [1.21, 1.222, 0.965]),
    "aws_robomaker_residential_SofaB_01": ([-0.364, -0.42, 0.0], [0.364, 0.42, 0.901]),
    "aws_robomaker_residential_Vase_01": ([-0.045, -0.061, 0.0], [0.045, 0.061, 0.302]),
    "aws_robomaker_residential_TV_01": ([0.011, -0.676, 0.002], [0.066, 0.622, 0.798]),
    "aws_robomaker_residential_Refrigerator_01": ([-0.521, -0.415, 0.012], [0.521, 0.415, 1.956]),
    "aws_robomaker_residential_Ball_01": ([-0.31, -0.31, -0.31], [0.31, 0.31, 0.31]),
    "mustard_bottle": ([-0.064, -0.057, -0.003], [0.033, 0.01, 0.188]),
    "cafe_table": ([-0.457, -0.457, 0.0], [0.457, 0.457, 0.775]),
}

# высота столешницы для объектов "на столе"
SURFACE = {
    "aws_robomaker_residential_KitchenTable_01": 0.801,
    "cafe_table": 0.775,
    "aws_robomaker_residential_CoffeeTable_01": 0.322,
}

STATIONS = []
for i in range(12):
    STATIONS.append((R, math.radians(i * 30)))

# расстояние камеры до объекта и высота камеры для обзорных видов
STATION_CAM = [
    (4.5, 1.4),   # chair
    (4.5, 2.2),   # table + bottle
    (5.5, 1.4),   # bed
    (5.5, 2.2),   # sofa
    (4.5, 1.4),   # chair D
    (3.5, 2.0),   # cafe table + vase
    (5.5, 1.4),   # fridge
    (3.0, 1.8),   # coffee table + vase + bottle
    (2.5, 1.4),   # tv
    (4.5, 2.0),   # sofa B
    (2.5, 1.2),   # ball
    (2.5, 1.2),   # ball
]


def build():
    objs = []
    # раскладываем вручную: якоря и объекты на столах
    layout = [
        (0, "aws_robomaker_residential_ChairA_01", "chair", 0.0, 0.0, 0.0),
        (1, "aws_robomaker_residential_KitchenTable_01", "dining table", 0.0, 0.0, 0.0),
        (1, "mustard_bottle", "bottle", 0.0, 0.0, None),
        (2, "aws_robomaker_residential_Bed_01", "bed", 0.0, 0.0, 0.0),
        (3, "aws_robomaker_residential_Sofa_01", "couch", 0.0, 0.0, 0.0),
        (4, "aws_robomaker_residential_ChairD_01", "chair", 0.0, 0.0, 0.0),
        (5, "cafe_table", "dining table", 0.0, 0.0, 0.0),
        (5, "aws_robomaker_residential_Vase_01", "vase", 0.0, 0.0, None),
        (6, "aws_robomaker_residential_Refrigerator_01", "refrigerator", 0.0, 0.0, 0.0),
        (7, "aws_robomaker_residential_CoffeeTable_01", "dining table", math.pi / 2, 0.0, 0.0),
        (7, "aws_robomaker_residential_Vase_01", "vase", 0.0, 0.25, None),
        (7, "mustard_bottle", "bottle", 0.0, -0.25, None),
        (8, "aws_robomaker_residential_TV_01", "tv", 0.0, 0.0, 0.0),
        (9, "aws_robomaker_residential_SofaB_01", "couch", 0.0, 0.0, 0.0),
        (10, "aws_robomaker_residential_Ball_01", "sports ball", 0.0, 0.0, 0.31),
        (11, "aws_robomaker_residential_Ball_01", "sports ball", 0.0, 0.0, 0.31),
    ]

    anchors = {}
    for st, model, cls, rel_yaw, lateral, z in layout:
        theta = STATIONS[st][1]
        yaw = theta + math.pi + rel_yaw
        # положение: радиальное + тангенциальное смещение
        base = (R * math.cos(theta), R * math.sin(theta))
        tang = (-math.sin(theta), math.cos(theta))
        x = base[0] + lateral * tang[0]
        y = base[1] + lateral * tang[1]
        lo, hi = AABB[model]
        if z is None:
            # на столешнице
            anchor = anchors[st]
            surf = SURFACE[anchor]
            z = surf - lo[2]
        anchors.setdefault(st, model)
        obj = {
            "station": st,
            "name": f"{cls.replace(' ', '_')}_{st}_{len(objs)}",
            "model": model,
            "class": cls,
            "pose": [x, y, z, 0.0, 0.0, yaw],
            "bbox": [lo, hi],
        }
        objs.append(obj)

    views = []
    for st, (d, h) in enumerate(STATION_CAM):
        theta = STATIONS[st][1]
        cam_r = R - d
        cx, cy = cam_r * math.cos(theta), cam_r * math.sin(theta)
        # высота цели: примерно центр объекта
        anchor = anchors[st]
        lo, hi = AABB[anchor]
        target_h = (lo[2] + hi[2]) / 2.0
        pitch = math.atan2(h - target_h, d)
        views.append({
            "name": f"station_{st:02d}",
            "pose": [cx, cy, h, 0.0, pitch, theta],
        })
    for i in range(12):
        theta = math.radians(i * 30 + 15)
        views.append({
            "name": f"between_{i:02d}",
            "pose": [0.0, 0.0, 1.8, 0.0, 0.12, theta],
        })

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "scene.json"), "w", encoding="utf-8") as f:
        json.dump({"objects": objs, "views": views, "radius": R}, f,
                  ensure_ascii=False, indent=2)

    lines = [
        '<?xml version="1.0"?>',
        '<sdf version="1.9">',
        '  <world name="exp">',
        '    <gravity>0 0 -9.8</gravity>',
        '',
        '    <light type="directional" name="sun">',
        '      <cast_shadows>true</cast_shadows>',
        '      <pose>0 0 10 0 0 0</pose>',
        '      <diffuse>0.9 0.9 0.9 1</diffuse>',
        '      <specular>0.2 0.2 0.2 1</specular>',
        '      <direction>0 0.3 -0.9</direction>',
        '    </light>',
        '',
        '    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">',
        '      <render_engine>ogre2</render_engine>',
        '    </plugin>',
        '    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>',
        '    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>',
        '    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>',
        '',
        '    <model name="ground">',
        '      <static>true</static>',
        '      <link name="link">',
        '        <collision name="c"><geometry><plane><normal>0 0 1</normal><size>40 40</size></plane></geometry></collision>',
        '        <visual name="v"><geometry><plane><normal>0 0 1</normal><size>40 40</size></plane></geometry>',
        '          <material><ambient>0.45 0.45 0.45 1</ambient><diffuse>0.45 0.45 0.45 1</diffuse></material>',
        '        </visual>',
        '      </link>',
        '    </model>',
        '',
        '    <model name="camera">',
        '      <static>false</static>',
        '      <pose>0 0 1.4 0 0 0</pose>',
        '      <link name="link">',
        '        <gravity>false</gravity>',
        '        <sensor name="cam" type="camera">',
        '          <update_rate>10</update_rate>',
        '          <camera>',
        '            <horizontal_fov>1.047</horizontal_fov>',
        '            <image><width>640</width><height>480</height><format>R8G8B8</format></image>',
        '            <clip><near>0.1</near><far>100</far></clip>',
        '          </camera>',
        '          <always_on>1</always_on>',
        '          <visualize>0</visualize>',
        '          <topic>/camera/image</topic>',
        '        </sensor>',
        '      </link>',
        '    </model>',
        '',
    ]
    for o in objs:
        x, y, z, r, p, yaw = o["pose"]
        lines.append(f'    <include>')
        lines.append(f'      <uri>model://{o["model"]}</uri>')
        lines.append(f'      <name>{o["name"]}</name>')
        lines.append(f'      <static>true</static>')
        lines.append(f'      <pose>{x:.4f} {y:.4f} {z:.4f} {r} {p} {yaw:.4f}</pose>')
        lines.append(f'    </include>')
    lines += ['  </world>', '</sdf>', '']

    with open(os.path.join(OUT, "world.sdf"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("objects:", len(objs), "views:", len(views))
    for cls in sorted({o["class"] for o in objs}):
        print(f"  {cls}: {sum(1 for o in objs if o['class'] == cls)}")


if __name__ == "__main__":
    build()
