# -*- coding: utf-8 -*-
"""
模板化短视频渲染流水线 (v1.0)
================================
一条视频 = 一份 JSON 配置。本脚本做全部剩下的工作:
  1. edge-tts 合成旁白 + 词级时间戳 (WordBoundary)
  2. 由词级时间戳自动生成 ASS 综艺字幕, 关键词自动高亮, 逐句卡点旁白
  3. 自动探测每个素材的分辨率/时长, 智能裁 9:16, 自动计算 xfade 转场 offset
  4. 调色预设 (莫兰迪等) + 结尾淡出 + BGM 混音 + 响度标准化 (-14 LUFS)
  5. 渲染完成自动抽帧质检

用法:
  python render.py projects/example.json
"""
import asyncio
import json
import re
import subprocess
import sys
from pathlib import Path

PIPE_DIR = Path(__file__).resolve().parent
OUT_DIR = PIPE_DIR.parent / "output"

# ---------------- 调色预设 ----------------
GRADES = {
    # 莫兰迪低饱和: 压饱和/提对比/阴影加青/提黑压白, 高级 spa 调性
    "morandi": ("eq=saturation=0.8:contrast=1.06,"
                "colorbalance=rs=-0.04:bs=0.06:rm=-0.03:bm=0.03,"
                "curves=all='0/0.04 0.5/0.52 1/0.96'"),
    # 原片直出
    "none": "null",
}

# ---------------- 小工具 ----------------
def _get(chunk, key, default=None):
    """edge-tts 的 chunk 可能是 dict 也可能是对象, 统一取值"""
    if isinstance(chunk, dict):
        return chunk.get(key, default)
    return getattr(chunk, key, default)


def probe(path: Path, entries: str, cs=False) -> str:
    cmd = ["ffprobe", "-v", "error", "-show_entries", entries,
           "-of", "default=noprint_wrappers=1:nokey=1"]
    if cs:
        cmd.insert(3, "-select_streams"); cmd.insert(4, "v:0")
    r = subprocess.run(cmd + [str(path)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"ffprobe 失败: {path}\n{r.stderr}")
    return r.stdout.strip()


def probe_duration(path: Path) -> float:
    return float(probe(path, "format=duration"))


def probe_size(path: Path):
    out = probe(path, "stream=width,height", cs=True)
    nums = [int(x) for x in re.findall(r"\d+", out)]
    if len(nums) < 2:
        raise RuntimeError(f"无法解析分辨率: {path} -> {out!r}")
    return nums[0], nums[1]


# ---------------- 文案标记提取 ----------------
def extract_markers(text: str):
    """从文案中提取【关键词】标记: 剥离括号后的干净文本 + 自动高亮词列表。
    例: "她家【翻床】" -> ("她家翻床", ["翻床"])
    写脚本时直接用【】标金句/关键词, 无需再手填 highlight_keywords。"""
    kws = re.findall(r"【([^】]+)】", text)
    clean = re.sub(r"【([^】]+)】", r"\1", text)
    # 去重且保持出现顺序
    seen, ordered = set(), []
    for k in kws:
        if k not in seen:
            seen.add(k); ordered.append(k)
    return clean, ordered


# ---------------- 1. 旁白 TTS + 词级时间戳 ----------------
async def synth_narration(text: str, voice: str, rate: str, pitch: str,
                          mp3_path: Path, words_path: Path):
    import edge_tts
    # edge-tts 7.x: 必须显式指定 boundary="WordBoundary" 才输出词级时间戳
    last_err = None
    for attempt in range(4):  # 最多重试 4 次, 应对限流/网络抖动
        try:
            com = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch,
                                       boundary="WordBoundary")
            audio = bytearray()
            words = []
            async for chunk in com.stream():
                ctype = _get(chunk, "type")
                if ctype == "audio":
                    audio.extend(_get(chunk, "data", b""))
                elif ctype in ("WordBoundary", "SentenceBoundary"):
                    words.append({
                        "t": _get(chunk, "offset", 0) / 1e7,   # 100ns -> 秒
                        "d": _get(chunk, "duration", 0) / 1e7,
                        "w": _get(chunk, "text", ""),
                    })
            if not audio:
                raise RuntimeError("TTS 返回空音频")
            mp3_path.write_bytes(bytes(audio))
            words_path.write_text(json.dumps(words, ensure_ascii=False, indent=1),
                                  encoding="utf-8")
            return words, probe_duration(mp3_path)
        except Exception as e:  # NoAudioReceived / 网络错误 / 空音频
            last_err = e
            print(f"  TTS 第 {attempt + 1} 次失败: {e}，{'重试中...' if attempt < 3 else '放弃'}")
            await asyncio.sleep(2 * (attempt + 1))  # 递增退避 2/4/6 秒
    raise RuntimeError(f"TTS 连续 4 次失败, 最后错误: {last_err}")


# ---------------- 2. 字幕: 分句 + 词级时间戳卡点 ----------------
def split_segments(text: str, max_chars: int = 12):
    parts = [p.strip() for p in re.split(r"[。！？，,.!?:：\n]", text) if p.strip()]
    segs = []
    for p in parts:
        while len(p) > max_chars:
            segs.append(p[:max_chars])
            p = p[max_chars:]
        if p:
            segs.append(p)
    return segs


def assign_times(segs, words, audio_dur):
    """把词级时间戳按字数分配到每个字幕段, 实现逐句精确卡点"""
    events = []
    if words:
        wi = 0
        for seg in segs:
            need = len(seg)
            got, start, end = 0, None, None
            while wi < len(words) and got < need:
                w = words[wi]; wi += 1
                got += len(w["w"])
                if start is None:
                    start = w["t"]
                end = w["t"] + w["d"]
            if start is None:
                break
            events.append({"text": seg, "start": start, "end": end})
    if not events:  # 兜底: 无时间戳时按时长均分
        step = audio_dur / max(len(segs), 1)
        for i, seg in enumerate(segs):
            events.append({"text": seg, "start": i * step,
                           "end": (i + 1) * step})
    # 收尾: 最短停留 / 不重叠 / 不超出音频
    for i, e in enumerate(events):
        if e["end"] - e["start"] < 0.5:
            e["end"] = e["start"] + 0.5
        if i + 1 < len(events):
            e["end"] = min(e["end"], events[i + 1]["start"] - 0.02)
        else:
            e["end"] = min(e["end"], audio_dur + 0.3)
    return events


def ass_time(t: float) -> str:
    t = max(t, 0)
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def build_ass(events, keywords, rgb, out_path: Path, style: dict | None = None):
    """style 可覆盖字幕样式: font_size/font/outline/margin_v/primary_rgb"""
    s = style or {}
    r, g, b = rgb
    hc = f"{b:02X}{g:02X}{r:02X}"  # ASS 是 BGR
    fsize = int(s.get("font_size", 92))
    outline = s.get("outline", 4)
    margin_v = int(s.get("margin_v", 380))
    pr, pg, pb = s.get("primary_rgb", (255, 255, 255))
    header = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n"
        "WrapStyle: 0\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, "
        "SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, "
        "StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
        "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Sub,{s.get('font', 'Microsoft YaHei')},{fsize},"
        f"&H00{pb:02X}{pg:02X}{pr:02X},&H00FFFFFF,&H00161A20,"
        f"&H96000000,-1,0,0,0,100,100,0,0,1,{outline},2,2,80,80,"
        f"{margin_v},1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, "
        "MarginV, Effect, Text\n"
    )
    lines = []
    # 关键词高亮：橙色 + 放大（kw_font_size 可覆盖，默认 1.25 倍）
    kw_fsize = int(s.get("kw_font_size", round(fsize * 1.25)))
    reset = f"{{\\fs{fsize}\\c&H{pb:02X}{pg:02X}{pr:02X}&}}"
    for e in events:
        text = e["text"]
        for kw in sorted(keywords, key=len, reverse=True):
            if kw in text:
                text = text.replace(
                    kw, f"{{\\c&H{hc}&\\fs{kw_fsize}}}{kw}{reset}")
        lines.append(f"Dialogue: 0,{ass_time(e['start'])},"
                     f"{ass_time(e['end'])},Sub,,0,0,0,,{text}")
    out_path.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")


# ---------------- 3. 滤镜链构建 ----------------
def portrait_crop_filter(w: int, h: int) -> str:
    """任意分辨率智能裁成 9:16 中心画幅"""
    ratio = 9 / 16
    if w / h > ratio:
        cw = int(h * ratio // 2 * 2); ch = h
        return f"crop={cw}:{ch}:(in_w-{cw})/2:0"
    cw = w; ch = int(w / ratio // 2 * 2)
    return f"crop={cw}:{ch}:0:(in_h-{ch})/2"


# ---------------- 九段式结构骨架 ----------------
REQUIRED_ROLES = {"钩子", "金句"}

# 六槽位骨架: 钩子(3秒冲突) -> 交代(这是哪) -> 铺垫(反差/预期)
#               -> 转折(情绪起) -> 金句(核心落点, 自动白闪) -> CTA(收口)
SLOT_ORDER = ["钩子", "交代", "铺垫", "转折", "金句", "CTA"]


def validate_structure(cfg, n_clips):
    """校验 structure 字段: 必填槽位(钩子/金句)齐全 + clip_index 合法 + 无重复"""
    struct = cfg.get("structure")
    if not struct:
        return None
    roles = [s.get("role") for s in struct]
    missing = REQUIRED_ROLES - set(roles)
    if missing:
        sys.exit(f"结构校验失败: 缺少必要槽位 {missing} (钩子/金句为爆款骨架必填)")
    for s in struct:
        ci = s.get("clip_index")
        if ci is None or not (0 <= ci < n_clips):
            sys.exit(f"结构校验失败: 槽位 {s.get('role')} 的 "
                     f"clip_index={ci} 超出范围(0-{n_clips-1})")
    idxs = [s["clip_index"] for s in struct]
    if len(set(idxs)) != len(idxs):
        sys.exit("结构校验失败: 存在 clip_index 重复的槽位")
    print(f"  结构骨架: {' -> '.join(roles)}")
    return struct


def resolve_transitions(cfg, n):
    """决定每段转场: 显式 transition_out 优先 > 结构槽位 transition_in >
    金句槽位自动 fadewhite > 默认 fade"""
    clips = cfg["clips"]
    struct = cfg.get("structure")
    trans = []
    for i in range(n - 1):
        explicit = clips[i].get("transition_out")
        if explicit:
            trans.append(explicit); continue
        if struct:
            nxt = next((s for s in struct
                        if s.get("clip_index") == i + 1), None)
            if nxt:
                ti = nxt.get("transition_in")
                if ti:
                    trans.append(ti); continue
                if nxt.get("role") == "金句":
                    trans.append("fadewhite"); continue
        trans.append("fade")
    return trans


def apply_duration_guards(cfg, durations):
    """按结构槽位 max_duration 自动截断超长素材, 返回有效时长列表"""
    struct = cfg.get("structure")
    if not struct:
        return list(durations)
    eff = list(durations)
    for s in struct:
        ci = s.get("clip_index")
        mx = s.get("max_duration")
        if ci is not None and mx and ci < len(eff) and eff[ci] > mx:
            print(f"  时长守卫: 槽位 {s.get('role')} (clip {ci}) "
                  f"{eff[ci]:.1f}s > {mx}s, 自动截断为 {mx}s")
            eff[ci] = mx
    return eff


def fit_durations_to_narration(config, durations, raw, audio_dur):
    """旁白守卫: 旁白比设计总长还长时, 按素材余量等比例撑长各槽位,
    保证旁白完整播完 (素材不足部分由末槽冻帧兜底),
    避免音频被 -shortest 截断出现"视频结束旁白没说完" """
    t = config.get("transition_duration", 0.3)
    n = len(durations)

    def total_of(ds):
        return sum(ds) - t * (n - 1) if n > 1 else ds[0]

    need = audio_dur + config.get("narration_tail", 0.6)
    cur = total_of(durations)
    if cur >= need:
        return durations
    deficit = need - cur
    head = [max(0.0, raw[i] - durations[i]) for i in range(n)]
    tot_head = sum(head)
    if tot_head > 0:
        take = min(deficit, tot_head)
        for i in range(n):
            durations[i] += head[i] * take / tot_head
    new_total = total_of(durations)
    if new_total < need - 0.01:  # 素材余量不够 → 末槽超出部分冻帧补齐
        durations[-1] += need - new_total
    print(f"  旁白守卫: 旁白 {audio_dur:.1f}s > 设计总长 {cur:.1f}s, "
          f"槽位已自动撑长, 视频总长 {total_of(durations):.1f}s")
    return durations


def build_render(config, clip_paths, durations, ass_name, audio_dur=0.0):
    n = len(clip_paths)
    t_dur = config.get("transition_duration", 0.3)
    w, h, fps = (config.get(k, d) for k, d in
                 (("width", 1080), ("height", 1920), ("fps", 30)))
    parts = []
    sizes = [probe_size(p) for p in clip_paths]

    for i, p in enumerate(clip_paths):
        chain = (f"[{i}:v]{portrait_crop_filter(*sizes[i])},"
                 f"scale={w}:{h}:flags=lanczos,fps={fps},setsar=1")
        raw_d = probe_duration(p)
        pad = durations[i] - raw_d
        if pad > 0.05:  # 槽位需求超过素材长度 → 冻帧补齐
            chain += f",tpad=stop_mode=clone:stop_duration={pad + 0.2:.3f}"
        chain += (f",trim=duration={durations[i]:.3f},setpts=PTS-STARTPTS,"
                  f"format=yuv420p[v{i}]")
        parts.append(chain)

    # xfade offset 自动计算: off_i = off_{i-1} + d_i - t
    offs, acc = [], 0.0
    for i in range(n - 1):
        acc += durations[i]
        offs.append(acc - t_dur * (i + 1))
    total = offs[-1] + durations[-1] if offs else durations[0]

    trans = resolve_transitions(config, n)
    prev = "v0"
    for i in range(1, n):
        parts.append(f"[{prev}][v{i}]xfade=transition={trans[i-1]}:"
                     f"duration={t_dur}:offset={offs[i-1]:.3f}[x{i}]")
        prev = f"x{i}"

    grade = GRADES.get(config.get("grade", "none"), "null")
    # 结尾淡化: 旁白结束后 0.6s 利落淡出, 不留长黑尾
    fade_d = config.get("end_fade", 0.6)
    v_fade_st = max(0.0, total - fade_d)
    parts.append(f"[{prev}]{grade},fade=t=out:st={v_fade_st:.2f}:d={fade_d:.2f},"
                 f"subtitles={ass_name},format=yuv420p[v]")

    # 音频: 旁白 + BGM 混音 + 响度标准化 + 结尾淡出
    a = config["audio"]
    nv, bv = a.get("narration_volume", 0.8), a.get("bgm_volume", 0.13)
    parts.append(f"[{n}:a]volume={nv}[vo]")
    parts.append(f"[{n+1}:a]volume={bv}[bgm]")
    # 音频淡出不早于旁白结束, 防削尾字
    a_fade_st = max(audio_dur, v_fade_st)
    a_fade_d = max(0.3, total - a_fade_st)
    parts.append(f"[vo][bgm]amix=inputs=2:duration=longest,"
                 f"loudnorm=I=-14:TP=-1.5:LRA=11,"
                 f"afade=t=out:st={a_fade_st:.2f}:d={a_fade_d:.2f}[a]")
    return ";".join(parts), total, offs


# ---------------- 封面自动生成 ----------------
def _title_segments(title: str):
    """把标题拆成 (文本, 是否关键词) 片段, 【】标记词 = 关键词"""
    clean, kws = extract_markers(title)
    segs, rest = [], clean
    for kw in kws:
        if kw in rest:
            before, rest = rest.split(kw, 1)
            if before:
                segs.append((before, False))
            segs.append((kw, True))
    if rest:
        segs.append((rest, False))
    return segs


def make_covers(cfg, proj, out_video: Path, total: float):
    """从成片抽帧 + PIL 合成候选封面:
    大号雅黑粗体白字 / 深色半透明圆角底条 / 【】关键词橙色高亮
    配置: cfg["cover"] = {"titles": [...], "frame_times": [...], ...}
    """
    ccfg = cfg.get("cover")
    if not ccfg:
        return []
    titles = ccfg.get("titles", [])
    if not titles:
        return []
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("  [封面] 未安装 Pillow, 跳过封面生成 (pip install pillow)")
        return []

    # 1. 抽候选帧 (默认: 钩子段 1s + 结尾余韵段)
    times = ccfg.get("frame_times") or [1.0, max(total - 1.5, 1.0)]
    frames = []
    for i, t in enumerate(times):
        fp = OUT_DIR / f"{proj}_coverframe_{i}.jpg"
        subprocess.run(["ffmpeg", "-y", "-ss", f"{t:.2f}", "-i", str(out_video),
                        "-vframes", "1", "-q:v", "2", str(fp)],
                       capture_output=True)
        if fp.exists():
            frames.append(fp)
    if not frames:
        print("  [封面] 抽帧失败, 跳过")
        return []

    W, H = 1080, 1920
    font_path = ccfg.get("font", "C:/Windows/Fonts/msyhbd.ttc")
    fsize = ccfg.get("font_size", 112)
    accent = tuple(ccfg.get("accent_rgb", [255, 150, 60]))
    box_alpha = ccfg.get("box_alpha", 168)
    max_w = ccfg.get("max_text_width", 880)
    center_y = ccfg.get("center_y", 860)
    made = []

    for i, title in enumerate(titles):
        font = ImageFont.truetype(font_path, fsize)
        img = Image.open(frames[i % len(frames)]).convert("RGB")
        if img.size != (W, H):
            img = img.resize((W, H))
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)

        # 2. 按宽度逐字换行 (中文标题一行 7-9 字最佳)
        segs = _title_segments(title)
        chars = [(ch, kw) for text, kw in segs for ch in text]
        lines, cur, cur_w = [], [], 0
        for ch, kw in chars:
            cw = d.textlength(ch, font=font)
            if cur and cur_w + cw > max_w:
                lines.append(cur); cur, cur_w = [], 0
            cur.append((ch, kw)); cur_w += cw
        if cur:
            lines.append(cur)
        if len(lines) > 3:            # 太长自动缩字号
            fsize = int(fsize * 0.82)
            font = ImageFont.truetype(font_path, fsize)

        # 3. 画深色半透明圆角底条
        line_h = int(fsize * 1.32)
        block_h = line_h * len(lines)
        pad_x, pad_y = int(fsize * 0.5), int(fsize * 0.36)
        widest = max(d.textlength("".join(c for c, _ in ln), font=font)
                     for ln in lines)
        bx0 = (W - widest) / 2 - pad_x
        bx1 = (W + widest) / 2 + pad_x
        by0 = center_y - block_h / 2 - pad_y
        by1 = center_y + block_h / 2 + pad_y
        d.rounded_rectangle([bx0, by0, bx1, by1], radius=32,
                            fill=(16, 18, 24, box_alpha))

        # 4. 居中逐行绘制, 关键词用品牌橙
        y = center_y - block_h / 2
        for ln in lines:
            lw = d.textlength("".join(c for c, _ in ln), font=font)
            x = (W - lw) / 2
            for ch, kw in ln:
                color = accent if kw else (255, 255, 255, 255)
                d.text((x, y), ch, font=font, fill=color)
                x += d.textlength(ch, font=font)
            y += line_h

        out_jpg = OUT_DIR / f"{proj}_cover_{i + 1}.jpg"
        Image.alpha_composite(img.convert("RGBA"), overlay)\
             .convert("RGB").save(out_jpg, quality=92)
        made.append(out_jpg)
    return made


# ---------------- 主流程 ----------------
async def main(cfg_path: str):
    cfg = json.loads(Path(cfg_path).read_text(encoding="utf-8"))
    OUT_DIR.mkdir(exist_ok=True)
    proj = cfg["project"]
    print(f"[1/5] 项目: {proj}")

    # 素材路径解析 (相对路径基于 pipeline 目录)
    clip_paths = [(PIPE_DIR / c["path"]).resolve() for c in cfg["clips"]]
    for p in clip_paths:
        if not p.exists():
            sys.exit(f"素材不存在: {p}")
    durations = [probe_duration(p) for p in clip_paths]
    struct = validate_structure(cfg, len(clip_paths))
    raw_durations = list(durations)
    durations = apply_duration_guards(cfg, durations)
    print(f"[2/5] 素材 {len(clip_paths)} 段, 时长: "
          + ", ".join(f"{d:.1f}s" for d in durations))

    # 旁白 TTS + 词级时间戳 (先剥离【】标记, TTS 只念干净文本)
    ncfg = cfg["narration"]
    clean_text, marker_kws = extract_markers(ncfg["text"])
    mp3 = OUT_DIR / f"{proj}_narration.mp3"
    words_json = OUT_DIR / f"{proj}_words.json"
    words, audio_dur = await synth_narration(
        clean_text, ncfg.get("voice", "zh-CN-XiaoxiaoNeural"),
        ncfg.get("rate", "+0%"), ncfg.get("pitch", "+0Hz"), mp3, words_json)
    print(f"[3/5] 旁白 {audio_dur:.1f}s, 词级时间戳 {len(words)} 个")

    # 旁白守卫: 旁白比设计总长还长时自动撑长槽位, 防止音频被截断
    durations = fit_durations_to_narration(cfg, durations, raw_durations,
                                           audio_dur)

    # 字幕自动卡点 (【】标记词自动高亮, 与配置内 keywords 合并, 标记优先)
    scfg = cfg.get("subtitles", {})
    segs = split_segments(clean_text, scfg.get("max_chars", 12))
    events = assign_times(segs, words, audio_dur)
    keywords = marker_kws + [k for k in scfg.get("highlight_keywords", [])
                             if k not in marker_kws]
    ass = OUT_DIR / f"{proj}_subtitles.ass"
    build_ass(events, keywords,
              scfg.get("highlight_color_rgb", [255, 150, 60]), ass, scfg)
    print(f"[4/5] 字幕 {len(events)} 句, 关键词高亮: {keywords}")

    # 滤镜链 + 渲染
    fc, total, offs = build_render(cfg, clip_paths, durations, ass.name, audio_dur)
    enc = cfg.get("encoder", {})
    bgm_path = Path(cfg["audio"]["bgm"])
    out = Path(cfg["output"])
    cmd = ["ffmpeg", "-y"]
    for p in clip_paths:
        cmd += ["-i", str(p)]
    cmd += ["-i", str(mp3), "-i", str(bgm_path),
            "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-crf", str(enc.get("crf", 23)),
            "-preset", enc.get("preset", "medium"), "-r",
            str(cfg.get("fps", 30)),
            "-c:a", "aac", "-b:a", "256k", "-ar", "44100",
            "-shortest", "-movflags", "+faststart", str(out)]
    print(f"[5/5] 渲染中... 总时长约 {total:.1f}s, "
          f"转场点: {', '.join(f'{o:.1f}s' for o in offs)}")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(OUT_DIR))
    if r.returncode != 0:
        print(r.stderr[-3000:])
        sys.exit("ffmpeg 渲染失败")

    # 自动质检: 抽 3 帧
    for ts, tag in ((2.0, "a"), (total / 2, "b"), (total - 3, "c")):
        subprocess.run(["ffmpeg", "-y", "-ss", str(ts), "-i", str(out),
                        "-vframes", "1", "-q:v", "2",
                        str(OUT_DIR / f"{proj}_qc_{tag}.jpg")],
                       capture_output=True)

    # 封面候选: 抽帧 + 大字标题合成
    covers = make_covers(cfg, proj, out, total)

    print(f"完成: {out} ({out.stat().st_size/1e6:.1f}MB, {total:.1f}s)")
    print(f"旁白词级时间戳: {words_json}")
    print(f"字幕文件: {ass}")
    print(f"质检帧: {proj}_qc_a/b/c.jpg")
    if covers:
        print(f"候选封面: {', '.join(p.name for p in covers)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("用法: python render.py <配置.json>")
    asyncio.run(main(sys.argv[1]))
