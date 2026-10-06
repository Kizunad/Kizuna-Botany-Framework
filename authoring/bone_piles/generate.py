#!/usr/bin/env python3
"""从骨堆造型生成自带贴图的 bbmodel 与原生 Java 方块模型。

运行：python3 authoring/bone_piles/generate.py
输出限定在本目录；不需要 Bong、OBJ 插件或 bbmodel_maker。
"""

import base64
import io
import json
import random
import uuid
from pathlib import Path

from PIL import Image, ImageDraw

from model import Box, build


ROOT = Path(__file__).resolve().parent
TEXTURE_SIZE = 64
NAMESPACE = "kizuna_botany"
MATERIALS = {
    "bone": (210, 207, 188),
    "chalk": (230, 227, 209),
    "aged": (169, 166, 148),
    "fracture": (190, 181, 157),
    "tooth": (237, 234, 215),
    "cavity": (67, 65, 57),
    "cracked": (218, 213, 192),
}
DISPLAY = {
    "gui": {"rotation": [30, 225, 0], "translation": [0, 2, 0], "scale": [.85, .85, .85]},
    "ground": {"translation": [0, 3, 0], "scale": [.5, .5, .5]},
    "fixed": {"rotation": [0, 180, 0], "translation": [0, 3, 0], "scale": [.75, .75, .75]},
    "thirdperson_righthand": {"rotation": [75, 45, 0], "translation": [0, 2.5, 0],
                             "scale": [.375, .375, .375]},
    "firstperson_righthand": {"rotation": [0, 45, 0], "scale": [.4, .4, .4]},
}


def stable_id(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"kizuna-botany/BonePiles/{name}"))


def make_texture() -> Image.Image:
    """手工定义色板、短裂纹与断口像素；固定随机种子只用于分布风化斑点。"""
    atlas = Image.new("RGBA", (TEXTURE_SIZE, TEXTURE_SIZE), (0, 0, 0, 0))
    for index, (name, color) in enumerate(MATERIALS.items()):
        tile = Image.new("RGBA", (16, 16), (*color, 255))
        draw = ImageDraw.Draw(tile)
        rng = random.Random(6200 + index)
        for _ in range(23):
            x, y = rng.randrange(16), rng.randrange(16)
            delta = rng.choice([-15, -9, -5, 6, 9])
            shade = tuple(max(0, min(255, c + delta)) for c in color)
            draw.rectangle((x, y, min(15, x + rng.randrange(2)), y), fill=(*shade, 255))
        if name in ("bone", "chalk", "aged"):
            shade = tuple(c - 13 for c in color)
            draw.line([(3, 5), (3, 7), (4, 7), (4, 9)], fill=(*shade, 255))
            draw.line([(12, 11), (11, 11), (11, 13)], fill=(*shade, 255))
        if name == "fracture":
            for x, y in [(2, 3), (5, 7), (9, 4), (12, 12), (3, 13), (8, 10)]:
                draw.point((x, y), fill=(132, 124, 106, 255))
                draw.point((x + 1, y), fill=(213, 204, 179, 255))
        if name == "cracked":
            draw.line([(7, 0), (7, 3), (8, 3), (8, 5), (6, 5), (6, 8), (5, 9)],
                      fill=(126, 123, 106, 255))
            draw.line([(8, 5), (10, 6), (11, 6)], fill=(155, 150, 130, 255))
        atlas.paste(tile, ((index % 4) * 16, (index // 4) * 16))
    return atlas


def faces(box: Box) -> dict:
    index = list(MATERIALS).index(box.material)
    u, v = (index % 4) * 16, (index // 4) * 16
    x, y, z = box.size
    dimensions = {"north": (x, y), "south": (x, y), "west": (z, y),
                  "east": (z, y), "up": (x, z), "down": (x, z)}
    # 所有部件约 2 texel/模型单位，避免每个小方块拉满一整张噪点贴图。
    result = {}
    for direction, (width, height) in dimensions.items():
        w, h = min(14, max(1, round(width * 2))), min(14, max(1, round(height * 2)))
        result[direction] = {"uv": [u + 1, v + 1, u + 1 + w, v + 1 + h], "texture": 0}
    return result


def element(box: Box) -> dict:
    rotation = [0, 0, 0]
    rotation["xyz".index(box.axis)] = box.angle
    return {"name": box.name, "type": "cube", "uuid": stable_id(box.name),
            "from": [round(c - s / 2, 6) for c, s in zip(box.center, box.size)],
            "to": [round(c + s / 2, 6) for c, s in zip(box.center, box.size)],
            "origin": list(box.pivot or box.center), "rotation": rotation,
            "rescale": False, "box_uv": False, "autouv": 0,
            "color": list(MATERIALS).index(box.material), "faces": faces(box)}


def validate(boxes: list[Box]) -> tuple[list[float], list[float]]:
    names = [box.name for box in boxes]
    if len(names) != len(set(names)):
        raise ValueError("部件名称重复")
    for box in boxes:
        if min(box.size) <= 0 or box.angle not in (-45, -22.5, 0, 22.5, 45):
            raise ValueError(f"不支持的尺寸或 Java 方块旋转: {box.name}")
        for corner in box.corners():
            if any(value < -1e-6 or value > 16 for value in corner):
                raise ValueError(f"部件超出一格: {box.name} {corner}")
    corners = [corner for box in boxes for corner in box.corners()]
    return ([round(min(p[i] for p in corners), 3) for i in range(3)],
            [round(max(p[i] for p in corners), 3) for i in range(3)])


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    boxes = build()
    lower, upper = validate(boxes)
    atlas = make_texture()
    png = io.BytesIO()
    atlas.save(png, format="PNG")
    elements = [element(box) for box in boxes]
    groups = list(dict.fromkeys(box.group for box in boxes))
    model = {
        "meta": {"format_version": "4.10", "model_format": "java_block", "box_uv": False},
        "name": "BonePiles", "model_identifier": "bone_pile",
        "resolution": {"width": TEXTURE_SIZE, "height": TEXTURE_SIZE},
        "elements": elements,
        "outliner": [{"name": group, "uuid": stable_id(group), "origin": [8, 0, 8],
                      "rotation": [0, 0, 0], "export": True, "visibility": True,
                      "isOpen": True, "children": [stable_id(b.name) for b in boxes if b.group == group]}
                     for group in groups],
        "textures": [{"name": "bone_pile.png", "id": "0", "uuid": stable_id("texture"),
                      "path": "bone_pile.png", "folder": "block", "namespace": NAMESPACE,
                      "width": TEXTURE_SIZE, "height": TEXTURE_SIZE,
                      "uv_width": TEXTURE_SIZE, "uv_height": TEXTURE_SIZE,
                      "particle": True, "render_mode": "default",
                      "source": "data:image/png;base64," + base64.b64encode(png.getvalue()).decode()}],
        "display": DISPLAY,
    }
    write_json(ROOT / "BonePiles.bbmodel", model)
    (ROOT / "bone_pile.png").write_bytes(png.getvalue())

    java_elements = []
    for box, source in zip(boxes, elements):
        exported = {key: source[key] for key in ("name", "from", "to")}
        if box.angle:
            exported["rotation"] = {"origin": source["origin"], "axis": box.axis,
                                    "angle": box.angle, "rescale": False}
        exported["faces"] = {face: {"uv": [n * 16 / TEXTURE_SIZE for n in data["uv"]],
                                     "texture": "#bone"} for face, data in source["faces"].items()}
        java_elements.append(exported)
    assets = ROOT / "export" / "assets" / NAMESPACE
    write_json(assets / "models/block/bone_pile.json", {
        "credit": "Kizuna's Botany Framework / BonePiles",
        "textures": {"bone": f"{NAMESPACE}:block/bone_pile", "particle": f"{NAMESPACE}:block/bone_pile"},
        "ambientocclusion": True, "display": DISPLAY, "elements": java_elements,
    })
    write_json(assets / "models/item/bone_pile.json", {"parent": f"{NAMESPACE}:block/bone_pile"})
    texture_path = assets / "textures/block/bone_pile.png"
    texture_path.parent.mkdir(parents=True, exist_ok=True)
    texture_path.write_bytes(png.getvalue())
    print(f"BonePiles: {len(boxes)} cubes, {len(groups)} groups; bounds {lower} .. {upper}")


if __name__ == "__main__":
    main()
