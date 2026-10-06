#!/usr/bin/env python3
"""直接渲染落盘的 bbmodel，生成主视图与等比例三视图。

预览工具依赖已安装的 bbmodel_maker、Pillow、NumPy；生成/导出模型不依赖渲染工具。
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from bbmodel_maker.render.framing import View, focus_for, render_views


ROOT = Path(__file__).resolve().parent
BACKGROUND = (38, 43, 47)


def font(size):
    path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def main():
    model = ROOT / "BonePiles.bbmodel"
    hero_view = (View("THREE QUARTER", -38, 28, ""),)
    hero = render_views(model, hero_view, size=960, bg=BACKGROUND,
                        focus=focus_for(model, hero_view, margin=1.16))[0][1]
    draw = ImageDraw.Draw(hero)
    draw.text((36, 27), "BONE PILES", fill=(234, 231, 216), font=font(30))
    draw.text((38, 70), "KIZUNA'S BOTANY FRAMEWORK", fill=(158, 170, 170), font=font(14))
    draw.text((38, 913), "BBMODEL / 64 PX ATLAS / 1 BLOCK FOOTPRINT", fill=(158, 170, 170), font=font(14))
    hero.save(ROOT / "preview.png")

    views = (View("FRONT +Z", 0, 0, "+z"), View("RIGHT +X", -90, 0, "+x"),
             View("TOP +Y", 0, 90, "+y"))
    renders = render_views(model, views, size=440, bg=BACKGROUND,
                           focus=focus_for(model, views, margin=1.12))
    sheet = Image.new("RGB", (1320, 480), BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    for i, (view, picture) in enumerate(renders):
        sheet.paste(picture, (i * 440, 40))
        draw.text((i * 440 + 24, 18), view.name, fill=(211, 216, 207), font=font(17))
    sheet.save(ROOT / "views.png")
    print("Rendered preview.png and views.png from BonePiles.bbmodel")


if __name__ == "__main__":
    main()
