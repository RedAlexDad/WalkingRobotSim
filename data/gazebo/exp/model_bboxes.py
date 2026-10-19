"""Габариты моделей Gazebo в метрах по их visual-мешам."""
import os
import re
import sys
import xml.etree.ElementTree as ET

import numpy as np
import trimesh

ROOT = "src/gazebo_sim/models"


def dae_unit(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            head = f.read(4000)
        m = re.search(r'<unit[^>]*meter="([0-9.eE+-]+)"', head)
        return float(m.group(1)) if m else 1.0
    except OSError:
        return 1.0


def geom_bounds(geom, model_dir):
    box = geom.find("box/size")
    if box is not None:
        size = np.array([float(v) for v in box.text.split()])
        return np.array([-size / 2, size / 2])
    sph = geom.find("sphere")
    if sph is not None:
        r = float(sph.findtext("radius", "0"))
        return np.array([[-r, -r, -r], [r, r, r]])
    cyl = geom.find("cylinder")
    if cyl is not None:
        r = float(cyl.findtext("radius", "0"))
        h = float(cyl.findtext("length", "0"))
        return np.array([[-r, -r, -h / 2], [r, r, h / 2]])
    mesh = geom.find("mesh")
    if mesh is None:
        return None
    uri = mesh.findtext("uri", "")
    if uri.startswith("file://models/"):
        path = os.path.join(ROOT, uri.replace("file://models/", ""))
    else:
        name = uri.replace("model://", "").split("/")[0]
        rel = uri.replace(f"model://{name}/", "")
        path = os.path.join(ROOT, name, rel)
    if not os.path.exists(path):
        path = os.path.join(model_dir, rel)
    if not os.path.exists(path):
        return None
    scale = mesh.findtext("scale", "1 1 1")
    scale = np.array([float(v) for v in scale.split()])
    obj = trimesh.load(path, force="mesh")
    pts = np.asarray(obj.vertices) * dae_unit(path) * scale
    return np.array([pts.min(axis=0), pts.max(axis=0)])


def model_bounds(name):
    d = os.path.join(ROOT, name)
    sdf = os.path.join(d, "model.sdf")
    if not os.path.exists(sdf):
        return None
    root = ET.parse(sdf).getroot()
    lo = np.array([np.inf] * 3)
    hi = np.array([-np.inf] * 3)
    for visual in root.iter("visual"):
        g = visual.find("geometry")
        if g is None:
            continue
        b = geom_bounds(g, d)
        if b is None:
            continue
        lo = np.minimum(lo, b[0])
        hi = np.maximum(hi, b[1])
    if not np.isfinite(lo).all():
        return None
    return lo, hi


if __name__ == "__main__":
    names = sys.argv[1:] or [
        "chair", "aws_robomaker_residential_ChairA_01",
        "aws_robomaker_residential_ChairD_01",
        "aws_robomaker_residential_KitchenTable_01",
        "aws_robomaker_residential_CoffeeTable_01",
        "aws_robomaker_residential_Bed_01",
        "aws_robomaker_residential_Sofa_01",
        "aws_robomaker_residential_SofaB_01",
        "aws_robomaker_residential_Vase_01",
        "aws_robomaker_residential_TV_01",
        "aws_robomaker_residential_Refrigerator_01",
        "aws_robomaker_residential_Ball_01",
        "mustard_bottle", "prius_hybrid", "cafe_table", "brown_table",
    ]
    for n in names:
        b = model_bounds(n)
        if b is None:
            print(f"{n:52s} NO VISUAL")
            continue
        lo, hi = b
        size = hi - lo
        print(f"{n:52s} size={np.round(size, 3)} min={np.round(lo, 3)} max={np.round(hi, 3)}")
