#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
给早安电台短视频添加 3 秒透明日历覆盖片头。
背景视频正常播放，日历文字覆盖其上，3 秒后淡出。
用法：
    python add_calendar_intro.py <video.mp4> <calendar_overlay.png> [out.mp4] [--duration 3] [--fade 0.6]
"""
import os
import sys
import subprocess
import argparse


def add_calendar_intro(video_path, overlay_path, output_path=None, duration=3.0, fade=0.6):
    if not output_path:
        base, ext = os.path.splitext(video_path)
        output_path = f"{base}_calendar_intro{ext}"

    fade_start = max(0.0, duration - fade)
    filter_complex = (
        f"[1:v]format=yuva420p,scale=1080:1920,fade=t=out:st={fade_start}:d={fade}:alpha=1[ov];"
        f"[0:v][ov]overlay=0:0:enable='between(t,0,{duration})'[v]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-loop", "1", "-t", str(duration), "-i", overlay_path,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "0:a",
        "-c:v", "libx264", "-crf", "20",
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path,
    ]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print("Saved:", output_path)
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="给短视频添加透明日历覆盖片头")
    parser.add_argument("video", help="成片视频路径")
    parser.add_argument("overlay", help="透明日历图层 PNG（720x1280 RGBA）")
    parser.add_argument("output", nargs="?", help="输出路径，默认在原片名后加 _calendar_intro")
    parser.add_argument("--duration", type=float, default=3.0, help="片头持续时间，默认 3 秒")
    parser.add_argument("--fade", type=float, default=0.6, help="淡出时间，默认 0.6 秒")
    args = parser.parse_args()
    add_calendar_intro(args.video, args.overlay, args.output, args.duration, args.fade)
