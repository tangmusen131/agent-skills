# -*- coding: utf-8 -*-
"""
行业版「早安电台」通用一键流水线（daily_pipeline.py）
=====================================================
一个脚本跑所有行业：python daily_pipeline.py <行业> [日期] [--skip-render]

用法：
  python daily_pipeline.py hardware                    # 五金机电，今天
  python daily_pipeline.py food 2026-09-01             # 餐饮美食，指定日期
  python daily_pipeline.py fashion 2026-09-01 --skip-render   # 只出文案+封面+日历层

素材要求：materials/<行业>/ 下放 01_钩子_xxx.mp4 ~ 06_CTA_xxx.mp4 六段素材
产出：output/<行业>_<日期>/ 下：
  cover_<date>.jpg / calendar_overlay_<date>.png /
  morning_radio_<date>.mp4 / morning_radio_<date>_final.mp4
"""
import os
import sys
import json
import datetime
import subprocess
import glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

import replicate_cover
import make_calendar_overlay
import add_calendar_intro
from industries import INDUSTRIES, load_copy_module

# 全局配置（路径请用环境变量或本地 config.py；勿把本机绝对路径写进仓库）
# 环境变量：MORNING_RADIO_PYTHON / MORNING_RADIO_BG_IMAGE / MORNING_RADIO_BGM_DIR / MORNING_RADIO_BGM_DEFAULT
# 本地覆盖：复制同目录 config.example.py 为 config.py 后修改（config.py 勿进发布包）
OUTPUT_ROOT = os.path.join(SCRIPT_DIR, "output")
MATERIALS_ROOT = os.path.join(SCRIPT_DIR, "materials")
PROJECTS_ROOT = os.path.join(SCRIPT_DIR, "projects")


def _load_optional_config():
    cfg = {}
    try:
        import config as _local_cfg  # optional; may be absent in clean clone
        for key in ("BG_IMAGE", "BGM_DIR", "BGM_DEFAULT", "PY"):
            val = getattr(_local_cfg, key, None)
            if val:
                cfg[key] = val
    except ImportError:
        pass
    return cfg


_opt = _load_optional_config()
BG_IMAGE = (
    os.environ.get("MORNING_RADIO_BG_IMAGE")
    or _opt.get("BG_IMAGE")
    or os.path.join(SCRIPT_DIR, "assets", "bg_cover.png")
)
BGM_DIR = (
    os.environ.get("MORNING_RADIO_BGM_DIR")
    or _opt.get("BGM_DIR")
    or os.path.join(SCRIPT_DIR, "bgm")
)
BGM_DEFAULT = (
    os.environ.get("MORNING_RADIO_BGM_DEFAULT")
    or _opt.get("BGM_DEFAULT")
    or os.path.join(BGM_DIR, "valley_sunset.mp3")
)
PY = (
    os.environ.get("MORNING_RADIO_PYTHON")
    or _opt.get("PY")
    or sys.executable
)
RENDER = os.path.join(SCRIPT_DIR, "render.py")


def pick_bgm(date):
    exts = ("*.mp3", "*.wav", "*.m4a", "*.flac", "*.ogg")
    tracks = []
    for e in exts:
        tracks.extend(glob.glob(os.path.join(BGM_DIR, e)))
    tracks = sorted(t for t in tracks if "valley_sunset" not in os.path.basename(t))
    if not tracks:
        return BGM_DEFAULT
    return tracks[date.timetuple().tm_yday % len(tracks)]


def scan_materials(materials_dir):
    slots = []
    for i in range(1, 7):
        pats = [os.path.join(materials_dir, f"{i:02d}_*{ext}")
                for ext in (".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v")]
        found = sorted(p for pat in pats for p in glob.glob(pat))
        if not found:
            raise FileNotFoundError(
                f"素材槽位 {i:02d} 缺失：请在 {materials_dir} 放置以 {i:02d}_ 开头的视频文件")
        slots.append(found[0])
    return slots


def _month_en(m):
    return ["", "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"][m]


def build_project_config(industry_id, copy, date, out_video, materials_dir):
    cfg = {
        "project": f"{industry_id}_radio_{date.isoformat()}",
        "output": out_video.replace("\\", "/"),
        "width": 1080, "height": 1920, "fps": 30,
        "transition_duration": 0.4,
        "clips": [{"path": p.replace("\\", "/")} for p in scan_materials(materials_dir)],
        "structure": [
            {"role": "钩子", "clip_index": 0, "max_duration": 4},
            {"role": "交代", "clip_index": 1, "max_duration": 3.5},
            {"role": "铺垫", "clip_index": 2, "max_duration": 4.5},
            {"role": "转折", "clip_index": 3, "max_duration": 3.5},
            {"role": "金句", "clip_index": 4, "max_duration": 4},
            {"role": "CTA", "clip_index": 5, "max_duration": 4},
        ],
        "narration": {
            "text": copy["narration"],
            "voice": "zh-CN-XiaoxiaoNeural",
            "rate": "+15%",
            "pitch": "+0Hz",
        },
        "subtitles": {
            "max_chars": 12, "font_size": 92, "outline": 4, "margin_v": 380,
            "highlight_keywords": [copy["highlight_keyword"]],
            "highlight_color_rgb": [255, 150, 60],
        },
        "audio": {
            "narration_volume": 0.85,
            "bgm": pick_bgm(date),
            "bgm_volume": 0.12,
        },
        "grade": "morandi",
        "encoder": {"crf": 20, "preset": "medium"},
    }
    return cfg


def run(industry_id, date, skip_render=False, narration_override=None,
        materials_dir=None, out_dir=None, progress_cb=None):
    """执行完整流水线。
    narration_override: 用户手改后的旁白全文（网页版用）
    materials_dir/out_dir: 工作区模式自定义路径（网页版用）
    progress_cb: 进度回调 progress_cb(阶段序号0~5, 描述)
    """
    def _prog(step, desc):
        if progress_cb:
            progress_cb(step, desc)
    if industry_id not in INDUSTRIES:
        raise ValueError(f"未知行业: {industry_id}，可选: {list(INDUSTRIES.keys())}")
    industry_name = INDUSTRIES[industry_id]
    copy_mod = load_copy_module(industry_id)

    if materials_dir is None:
        materials_dir = os.path.join(MATERIALS_ROOT, industry_id)
    if out_dir is None:
        out_dir = os.path.join(OUTPUT_ROOT, f"{industry_id}_{date.isoformat()}")
    os.makedirs(out_dir, exist_ok=True)
    project_dir = os.path.join(PROJECTS_ROOT, industry_id, "daily")
    os.makedirs(project_dir, exist_ok=True)

    # 1. 文案
    _prog(1, "生成文案")
    print(f"[1/5] 生成 {date.isoformat()} {industry_name}文案...")
    copy = copy_mod.build(date)
    if narration_override:
        copy["narration"] = narration_override
    print(f"      主题: {copy['theme_name']} | 关键词: {copy['highlight_keyword']}")
    print(f"      旁白: {copy['narration']}")
    copy_path = os.path.join(project_dir, f"{date.isoformat()}_copy.json")
    with open(copy_path, "w", encoding="utf-8") as f:
        json.dump(copy, f, ensure_ascii=False, indent=2)

    # 2. 封面
    _prog(2, "生成封面")
    print("[2/5] 生成平台封面...")
    cover_path = os.path.join(out_dir, f"cover_{date.isoformat()}.jpg")
    replicate_cover.make_cover(
        BG_IMAGE,
        month_en=_month_en(date.month) + f" {date.year}",
        day_left=f"{date.month:02d}", day_right=f"{date.day:02d}",
        lunar=copy["lunar_info"].get("lunar_month_day", ""),
        weekday="星期" + "一二三四五六日"[date.weekday()],
        festival=copy["festival"],
        subtitle=copy["cover_subtitle"],
        output_path=cover_path,
    )
    print(f"      {cover_path}")

    # 3. 日历层
    _prog(3, "生成日历图层")
    print("[3/5] 生成透明日历图层...")
    overlay_path = os.path.join(out_dir, f"calendar_overlay_{date.isoformat()}.png")
    make_calendar_overlay.make_calendar_overlay(
        month_en=_month_en(date.month) + f" {date.year}",
        day_left=f"{date.month:02d}", day_right=f"{date.day:02d}",
        lunar=copy["lunar_info"].get("lunar_month_day", ""),
        weekday="星期" + "一二三四五六日"[date.weekday()],
        festival=copy["festival"],
        subtitle=copy["cover_subtitle"],
        output_path=overlay_path,
    )
    print(f"      {overlay_path}")

    if skip_render:
        print("[4/5] 跳过渲染（--skip-render）")
        print("[5/5] 跳过片头合成")
        return {"copy": copy_path, "cover": cover_path, "overlay": overlay_path,
                "body": None, "final": None}

    # 4. 渲染
    bgm_file = pick_bgm(date)
    _prog(4, "渲染视频（约1分钟）")
    print(f"[4/5] 渲染视频（BGM: {os.path.basename(bgm_file)}）...")
    body_video = os.path.join(out_dir, f"morning_radio_{date.isoformat()}.mp4")
    cfg = build_project_config(industry_id, copy, date, body_video, materials_dir)
    cfg_path = os.path.join(project_dir, f"morning_radio_{date.isoformat()}.json")
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    subprocess.run([PY, RENDER, cfg_path], check=True, cwd=SCRIPT_DIR)
    print(f"      {body_video}")

    # 5. 片头
    _prog(5, "合成日历片头")
    print("[5/5] 合成日历片头...")
    final_video = os.path.join(out_dir, f"morning_radio_{date.isoformat()}_final.mp4")
    add_calendar_intro.add_calendar_intro(body_video, overlay_path, final_video)

    print("\n全部完成！")
    print(f"  发布封面: {cover_path}")
    print(f"  最终成片: {final_video}")
    return {"copy": copy_path, "cover": cover_path, "overlay": overlay_path,
            "body": body_video, "final": final_video}


if __name__ == "__main__":
    args = sys.argv[1:]
    skip = "--skip-render" in args
    args = [a for a in args if a != "--skip-render"]
    if not args:
        print("用法: python daily_pipeline.py <行业> [日期] [--skip-render]")
        print(f"可选行业: {', '.join(f'{k}({v})' for k, v in INDUSTRIES.items())}")
        sys.exit(1)
    industry = args[0]
    date = datetime.date.fromisoformat(args[1]) if len(args) > 1 else datetime.date.today()
    run(industry, date, skip_render=skip)
