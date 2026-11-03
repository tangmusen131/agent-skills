# -*- coding: utf-8 -*-
"""本地路径配置示例。
复制本文件为 config.py 后按本机修改；config.py 勿提交 / 勿打进发布包。
也可不建 config.py，改用环境变量：
  MORNING_RADIO_PYTHON / MORNING_RADIO_BG_IMAGE /
  MORNING_RADIO_BGM_DIR / MORNING_RADIO_BGM_DEFAULT
"""

# Python 解释器（需可用 ffmpeg，并安装 edge-tts / cnlunar / Pillow / Flask）
# 例：r"<YOUR_PYTHON>" 或留空则使用当前解释器 sys.executable
PY = r"<YOUR_PYTHON>"

# 封面干净底图（竖版、构图干净、少边角台标；包内不附带，请自备且确认版权）
BG_IMAGE = r"<PLATFORM_ROOT>/assets/bg_cover.png"

# BGM 曲库目录与默认曲（包内不附带；请自备授权素材，勿未授权分发）
BGM_DIR = r"<PLATFORM_ROOT>/bgm"
BGM_DEFAULT = r"<PLATFORM_ROOT>/bgm/valley_sunset.mp3"
