#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成透明背景的日历覆盖图层 PNG（720x1280 RGBA）。
用于短视频片头：视频画面正常播放，日历文字覆盖其上，3 秒后淡出。
版式与 replicate_cover.py 定格模板一致（2026-08-27 用户确认）。
"""
import os
from PIL import Image, ImageDraw

from replicate_cover import (
    load_font,
    text_size,
    draw_text_center,
    draw_text_left,
    draw_spaced_text,
)


def make_calendar_overlay(
    month_en="August 2026",
    day_left="08",
    day_right="27",
    lunar="农历七月十五",
    weekday="星期四",
    festival="中元节",
    subtitle="",
    output_path=None,
    with_gradient=True,
):
    # 透明画布
    img = Image.new("RGBA", (720, 1280), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 半透明压暗渐变（保证视频画面上文字可读；随图层一起淡出）
    if with_gradient:
        # 顶部：0-500，alpha 90 -> 0
        for y in range(0, 500):
            alpha = int(90 * (1 - y / 500))
            draw.line([(0, y), (720, y)], fill=(0, 0, 0, alpha))
        # 底部：900-1280，alpha 0 -> 110
        for y in range(900, 1280):
            alpha = int(110 * (y - 900) / 380)
            draw.line([(0, y), (720, y)], fill=(0, 0, 0, alpha))

    # 字体（与定格模板一致）
    font_month = load_font("msyhbd", 40)
    font_day = load_font("msyhbd", 155)
    font_jixiang = load_font("msyhbd", 26)
    font_lunar = load_font("msyhbd", 36)
    font_weekday = load_font("msyhbd", 36)
    font_festival = load_font("msyhbd", 92)
    font_subtitle = load_font("msyhbd", 32)

    # 配色（与定格模板一致）
    color_gold = (255, 223, 95, 255)
    color_white = (255, 255, 255, 255)
    color_light = (245, 250, 255, 255)
    color_red = (190, 40, 40, 255)
    stroke_black = (0, 0, 0, 255)

    # 1. 顶部 August 2026
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

    draw_text_left(draw, day_left, left_x, day_y, font_day, color_white, stroke=2, stroke_fill=stroke_black)
    draw_text_left(draw, day_right, right_x, day_y, font_day, color_white, stroke=2, stroke_fill=stroke_black)

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
        draw.text((ch_x, char_y_start + idx * char_h), ch, font=font_jixiang, fill=color_white)

    # 4. 农历 / 星期
    lunar_y = day_y + left_h + 60
    lunar_w, _ = text_size(draw, lunar, font_lunar)
    lunar_x = left_x + (left_w - lunar_w) // 2
    draw.text((lunar_x, lunar_y), lunar, font=font_lunar, fill=color_gold, stroke_width=1, stroke_fill=stroke_black)

    weekday_w, _ = text_size(draw, weekday, font_weekday)
    weekday_x = right_x + (right_w - weekday_w) // 2
    draw.text((weekday_x, lunar_y), weekday, font=font_weekday, fill=color_light)

    # 5. 节日名
    festival_y = lunar_y + 55
    draw_text_center(draw, festival, festival_y, font_festival, color_white, stroke=2, stroke_fill=stroke_black)

    # 6. 底部副标题
    if subtitle:
        draw_text_center(draw, subtitle, 1100, font_subtitle, color_white, stroke=1, stroke_fill=stroke_black)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path)
    return img


if __name__ == "__main__":
    out = "./output/calendar_overlay_demo.png"
    make_calendar_overlay(
        month_en="August 2026",
        day_left="08",
        day_right="27",
        lunar="农历七月十五",
        weekday="星期四",
        festival="中元节",
        subtitle="今天是8月27日",
        output_path=out,
    )
    print("Saved:", out)
