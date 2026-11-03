#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
复刻早安电台封面：1:1 仿制 _analysis_frame0_720x1280.jpg 的样式
输入：底图、文案参数
输出：720x1280 封面 JPG
"""
import os
from PIL import Image, ImageDraw, ImageFont


def load_font(name, size):
    """按优先级加载字体"""
    candidates = [
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/msyh.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_text_center(draw, text, y, font, fill, stroke=0, stroke_fill=(0, 0, 0)):
    w, h = text_size(draw, text, font)
    x = (720 - w) // 2
    kwargs = {}
    if stroke:
        kwargs = {"stroke_width": stroke, "stroke_fill": stroke_fill}
    draw.text((x, y), text, font=font, fill=fill, **kwargs)
    return x, y, w, h


def draw_text_left(draw, text, x, y, font, fill, stroke=0, stroke_fill=(0, 0, 0)):
    kwargs = {}
    if stroke:
        kwargs = {"stroke_width": stroke, "stroke_fill": stroke_fill}
    draw.text((x, y), text, font=font, fill=fill, **kwargs)


def draw_spaced_text(draw, text, y, font, fill, total_width=None, letter_gap=12):
    """均匀拉开字母间距绘制，适配 August 2026 样式"""
    chars = list(text)
    char_sizes = [text_size(draw, ch, font)[0] for ch in chars]
    if total_width is None:
        total_width = sum(char_sizes) + letter_gap * (len(chars) - 1)
    start_x = (720 - total_width) // 2
    x = start_x
    for ch, cw in zip(chars, char_sizes):
        draw.text((x, y), ch, font=font, fill=fill)
        x += cw + letter_gap
    return total_width


def add_gradient_overlay(img, start_alpha, end_alpha, y_start, y_end, color=(0, 0, 0)):
    """在指定区域添加从上到下的透明渐变遮罩"""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(y_start, y_end):
        ratio = (y - y_start) / max(1, (y_end - y_start))
        alpha = int(start_alpha * (1 - ratio) + end_alpha * ratio)
        draw.line([(0, y), (img.width, y)], fill=(*color, alpha))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    return img.convert("RGB")


def make_cover(
    bg_path,
    month_en="August 2026",
    day_left="08",
    day_right="27",
    lunar="农历七月十五",
    weekday="星期四",
    festival="中元节",
    subtitle="",
    output_path=None,
):
    img = Image.open(bg_path).convert("RGB")

    # 去水印：底部裁掉 70px，再 resize 到 720x1280
    w, h = img.size
    crop_h = min(70, h // 20)
    img = img.crop((0, 0, w, h - crop_h))
    img = img.resize((720, 1280), Image.LANCZOS)

    # 顶部压暗渐变：让 August / 日期 可读
    img = add_gradient_overlay(img, start_alpha=90, end_alpha=0, y_start=0, y_end=500)
    # 底部压暗渐变：让副标题可读
    img = add_gradient_overlay(img, start_alpha=0, end_alpha=110, y_start=900, y_end=1280)

    draw = ImageDraw.Draw(img)

    # 字体
    font_month = load_font("msyhbd", 40)
    font_day = load_font("msyhbd", 155)
    font_jixiang = load_font("msyhbd", 26)
    font_lunar = load_font("msyhbd", 36)
    font_weekday = load_font("msyhbd", 36)
    font_festival = load_font("msyhbd", 92)
    font_subtitle = load_font("msyhbd", 32)

    # 配色
    color_gold = (255, 223, 95)
    color_white = (255, 255, 255)
    color_light = (245, 250, 255)
    color_red = (190, 40, 40)

    # 1. 顶部 August 2026（均匀字间距，加描边增强可读性）
    draw_spaced_text(draw, month_en, y=125, font=font_month, fill=color_gold, letter_gap=12)

    # 2. 大号 08  27
    left_w, left_h = text_size(draw, day_left, font_day)
    right_w, _ = text_size(draw, day_right, font_day)
    gap = 72
    total_w = left_w + gap + right_w
    start_x = (720 - total_w) // 2
    left_x = start_x
    right_x = start_x + left_w + gap
    day_y = 205

    draw_text_left(draw, day_left, left_x, day_y, font_day, color_white, stroke=2, stroke_fill=(0, 0, 0))
    draw_text_left(draw, day_right, right_x, day_y, font_day, color_white, stroke=2, stroke_fill=(0, 0, 0))

    # 3. 中间红色竖印章 "吉祥"
    seal_w = 34
    seal_h = 86
    seal_x = start_x + left_w + (gap - seal_w) // 2
    seal_y = day_y + 25
    draw.rounded_rectangle([seal_x, seal_y, seal_x + seal_w, seal_y + seal_h], radius=3, fill=color_red)

    jixiang_text = "吉祥"
    _, char_h = text_size(draw, "吉", font_jixiang)
    char_y_start = seal_y + (seal_h - char_h * 2) // 2
    for idx, ch in enumerate(jixiang_text):
        cw, _ = text_size(draw, ch, font_jixiang)
        ch_x = seal_x + (seal_w - cw) // 2
        draw.text((ch_x, char_y_start + idx * char_h), ch, font=font_jixiang, fill=(255, 255, 255))

    # 4. 农历 / 星期（放在日期数字下方，避免重叠）
    lunar_y = day_y + left_h + 60
    lunar_w, _ = text_size(draw, lunar, font_lunar)
    lunar_x = left_x + (left_w - lunar_w) // 2
    draw.text((lunar_x, lunar_y), lunar, font=font_lunar, fill=color_gold, stroke_width=1, stroke_fill=(0, 0, 0))

    weekday_w, _ = text_size(draw, weekday, font_weekday)
    weekday_x = right_x + (right_w - weekday_w) // 2
    draw.text((weekday_x, lunar_y), weekday, font=font_weekday, fill=color_light)

    # 5. 节日名 "中元节"
    festival_y = lunar_y + 55
    draw_text_center(draw, festival, festival_y, font_festival, color_white, stroke=2, stroke_fill=(0, 0, 0))

    # 6. 底部副标题
    if subtitle:
        draw_text_center(draw, subtitle, 1100, font_subtitle, color_white, stroke=1, stroke_fill=(0, 0, 0))

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, quality=95)
    return img


if __name__ == "__main__":
    # 示例：相对当前工作目录；请自备底图并确认版权
    bg = "./assets/bg_cover.png"
    out_dir = "./output/cover_replicas"
    os.makedirs(out_dir, exist_ok=True)

    # 生成 5 个不同副标题的版本，对应用户给的 5 张封面
    subtitles = [
        "今天是8月27日",
        "ZhongYuan Festival",
        "星期四",
        "中元节",
        "愿我们珍惜眼前人，不负这仅有一次的人间",
    ]

    for i, sub in enumerate(subtitles, 1):
        out = f"{out_dir}/cover_replica_{i:02d}.jpg"
        make_cover(bg, subtitle=sub, output_path=out)
        print(f"Saved: {out}")

    print("Done.")
