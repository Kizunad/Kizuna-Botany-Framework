"""BonePiles 的造型：单位为 1/16 格，地面 y=0，兽颅朝 +z。

只使用 Java 方块模型支持的单轴旋转；解剖部件分组与导出格式相互独立。
"""

from dataclasses import dataclass
from math import cos, radians, sin, sqrt, tan


@dataclass(frozen=True)
class Box:
    group: str
    name: str
    center: tuple[float, float, float]
    size: tuple[float, float, float]
    material: str = "bone"
    axis: str = "y"
    angle: float = 0
    pivot: tuple[float, float, float] | None = None

    def corners(self):
        """输出旋转后顶点，检查实际占地而非旋转前包围盒。"""
        pivot = self.pivot or self.center
        a, b = {"x": (1, 2), "y": (2, 0), "z": (0, 1)}[self.axis]
        c, s = cos(radians(self.angle)), sin(radians(self.angle))
        for bits in range(8):
            point = [self.center[i] + self.size[i] * (.5 if bits & (1 << i) else -.5)
                     - pivot[i] for i in range(3)]
            point[a], point[b] = c * point[a] - s * point[b], s * point[a] + c * point[b]
            yield tuple(point[i] + pivot[i] for i in range(3))


def skull() -> list[Box]:
    """颅顶、颧弓围出真实眼眶；细长吻部与犬齿区分兽颅和人颅。"""
    anchor = (5.1, 1.05, 9.0)
    boxes = []

    def add(name, center, size, material="bone"):
        boxes.append(Box("01_skull", name, tuple(a + b for a, b in zip(anchor, center)),
                         size, material, "y", 22.5, anchor))

    add("occipital_base", (0, 1.75, -1.55), (3.5, 2.65, 1.55), "aged")
    add("cranium", (0, 3.05, -1.0), (3.85, 2.4, 2.6))
    add("crown", (-.2, 4.35, -.9), (3.05, .75, 2.25), "chalk")
    add("crown_broken_edge", (-1.65, 3.95, -.4), (.7, .55, 1.0), "fracture")
    add("sagittal_crest", (0, 4.78, -1.1), (.42, .32, 2.1), "chalk")
    add("forehead", (0, 3.4, .65), (2.6, 1.45, 1.25), "cracked")
    add("nasal_bridge", (0, 2.6, 1.6), (1.45, 1.45, 2.3), "chalk")
    # 内壁向内退，眼窝的边框与阴影具有可从侧面核对的厚度。
    for side, label in [(-1, "left"), (1, "right")]:
        add(f"{label}_orbit_recess", (side * 1.25, 2.55, .25), (.22, 1.35, 1.35), "cavity")
        add(f"{label}_brow", (side * 1.75, 3.38, .25), (1.35, .65, 1.8), "chalk")
        add(f"{label}_cheek_arch", (side * 2.03, 1.83, .2), (.62, .56, 2.15))
        add(f"{label}_orbit_back", (side * 1.9, 2.58, -.72), (.75, 1.3, .5))
        add(f"{label}_orbit_front", (side * 1.8, 2.45, 1.0), (.68, 1.05, .5))
        add(f"{label}_maxilla", (side * .89, 1.83, 2.05), (.7, .85, 2.65), "aged")
        add(f"{label}_nose_rim", (side * .66, 2.32, 3.26), (.42, 1.0, .7), "chalk")
        add(f"{label}_canine_root", (side * .97, 1.0, 2.18), (.56, .95, .65), "tooth")
        add(f"{label}_canine_tip", (side * .98, .38, 2.32), (.32, .42, .36), "tooth")
        for i in range(2):
            add(f"{label}_molar_{i}", (side * 1.12, 1.23, .68 + i * .5),
                (.38, .4, .34), "tooth")
    add("nose_hollow", (0, 2.13, 2.83), (.85, .7, .15), "cavity")
    add("nose_cap", (0, 2.8, 3.1), (1.15, .33, .9), "chalk")
    add("nose_septum", (0, 2.26, 3.3), (.2, .72, .52), "aged")
    return boxes


def ribcage() -> list[Box]:
    """残存四根弧肋；最后一根只留半边，避免完整胸腔的整齐轮廓。"""
    boxes = []
    for i, (z, top) in enumerate([(3.5, 4.7), (5.0, 5.35), (6.5, 5.65), (8.0, 5.2)]):
        x = 9.1
        group = "02_ribs_and_spine"
        boxes.append(Box(group, f"vertebra_{i}", (x, top, z), (1.45, .9, 1.0), "aged"))
        boxes.append(Box(group, f"spinous_process_{i}", (x, top + .7, z - .1),
                         (.42, .9, .52), "chalk"))
        boxes.append(Box(group, f"transverse_process_{i}", (x, top - .13, z),
                         (2.2, .4, .55)))
        if i < 3:
            boxes.append(Box(group, f"spine_joint_{i}", (x, top - .1, z + .75),
                             (.74, .66, .65), "fracture"))
        for side in [-1, 1]:
            if i == 3 and side == -1:
                continue
            prefix = f"rib_{i}_{'left' if side == -1 else 'right'}"
            shoulder_half = 2.4 / (2 * sqrt(2))
            joint_x = 1.6 + shoulder_half
            joint_y = top - .75 - shoulder_half
            lower_y = 1.58
            flank_height = joint_y - lower_y
            lower_x = joint_x + flank_height * tan(radians(22.5))
            boxes.append(Box(group, prefix + "_shoulder", (x + side * 1.6, top - .75, z),
                             (2.4, .43, .5), "bone", "z", -side * 45))
            boxes.append(Box(group, prefix + "_flank",
                             (x + side * (joint_x + lower_x) / 2, (joint_y + lower_y) / 2, z),
                             (.45, flank_height / cos(radians(22.5)), .5), "bone", "z", side * 22.5))
            if i != 0:
                return_half = 1.35 / (2 * sqrt(2))
                boxes.append(Box(group, prefix + "_return",
                                 (x + side * (lower_x - return_half), lower_y - return_half, z),
                                 (1.35, .39, .48), "aged", "z", side * 45))
    return boxes


def long_bone(name, center, length, angle, *, broken=False) -> list[Box]:
    """细骨干与双髁关节共用旋转支点，不把长骨画成一根直木棍。"""
    group = "03_crossed_long_bones"
    boxes = []

    def add(suffix, offset, size, material="bone"):
        boxes.append(Box(group, f"{name}_{suffix}", tuple(a + b for a, b in zip(center, offset)),
                         size, material, "y", angle, center))

    add("shaft", (0, 0, 0), (.72, .72, length - 1.3))
    add("ridge", (-.16, .35, -.3), (.28, .2, length - 2.2), "chalk")
    for end in [-1, 1]:
        z = end * (length / 2 - .65)
        if broken and end == 1:
            add("broken_rim", (0, 0, z), (1.05, .94, .65), "fracture")
            add("marrow", (0, 0, z + .34), (.44, .42, .04), "cavity")
        else:
            add(f"neck_{end}", (0, 0, z - end * .4), (1.1, .94, 1.15), "aged")
            for side in [-1, 1]:
                add(f"condyle_{end}_{side}", (side * .43, .05, z), (.75, 1.15, .96), "chalk")
    return boxes


def fragments() -> list[Box]:
    boxes = [
        Box("04_jaw_and_fragments", "jaw_body", (8.0, .62, 13.72), (3.4, .6, .66), "aged"),
        Box("04_jaw_and_fragments", "jaw_return", (6.36, .68, 13.25), (.62, .72, 1.5), "bone"),
        Box("04_jaw_and_fragments", "jaw_ramus", (9.6, 1.0, 13.15), (.65, 1.35, 1.65), "bone"),
    ]
    for i in range(4):
        boxes.append(Box("04_jaw_and_fragments", f"jaw_tooth_{i}",
                         (6.9 + i * .62, 1.05, 13.69), (.38, .35, .43), "tooth"))
    for i, (center, size, angle) in enumerate([
        ((2.15, .3, 7.8), (1.5, .6, .75), 22.5),
        ((3.6, .25, 13.2), (.9, .5, .6), -45),
        ((12.75, .3, 4.6), (1.65, .6, .74), -22.5),
        ((13.5, .32, 8.8), (.75, .64, 1.4), 45),
        ((7.1, .3, 2.0), (1.4, .6, .7), -22.5),
        ((10.0, .24, 2.2), (1.1, .48, .7), 45),
    ]):
        boxes.append(Box("04_jaw_and_fragments", f"chip_{i}", center, size, "fracture", "y", angle))
    return boxes


def build() -> list[Box]:
    return [*skull(), *ribcage(),
            *long_bone("rear_femur", (4.45, .63, 4.9), 8.4, 45),
            *long_bone("buried_femur", (9.4, .63, 6.5), 9.4, -45),
            *long_bone("front_femur", (10.3, .74, 10.65), 8.0, 45),
            *long_bone("broken_humerus", (3.0, .62, 9.3), 4.1, -22.5, broken=True),
            *fragments()]
