---
name: morning-radio-pipeline
version: 2.2.2
description: 早安电台日更短视频一键生产流水线：日期 → 自动文案（预言式互动钩子+农历/节气/节日+主题金句+互动CTA首尾呼应）→ 定格模板封面 → 透明日历片头 → 六槽位剪辑（edge-tts 旁白/ASS 卡点字幕/关键词橙色放大/莫兰迪调色/BGM 按日轮换/旁白守卫）→ 最终成片。触发词：早安电台、日更视频、生成今日视频、daily_pipeline。
agent_created: true
---

# 早安电台日更流水线（一键版 v2.2）

> **说明**：本包主要为流程文档。完整可运行引擎与多行业扩展见 `morning-radio-360-industries/assets/platform/`（同源 fork）。请将下文 `<PLATFORM_ROOT>` / `<YOUR_PYTHON>` 换成你的本机路径，或设置环境变量 `MORNING_RADIO_PYTHON`。

## 文案公式（2026-08-28 对标抖音爆款升级，P0 互动机制）

```
预言钩子 → 日期问候 → 铺垫 → 转折 → 金句 → 互动CTA
```

- **预言钩子**（`PREDICTION_HOOKS`，8 条按日轮换）：如「我有预感，今天敢发好运的人，最近一定会有好运发生」——引导观众在评论区打出关键词，拉互动量触发算法推流
- **互动CTA**（`INTERACTIVE_CTAS`，5 条模板按日轮换）：**含 `{kw}` 占位符，用 re.search 从当天钩子自动提取【关键词】填充**——保证首尾呼应（开头让发【成功】，结尾就喊打【成功】），不写死词
- 钩子关键词 8 天一轮：好运/成功/顺利/开心/发财/平安/上岸/幸福；CTA 模板同一关键词自动对齐
- 主题金句库（14 日常 + 5 节日）不变；主题原 hook 只用于封面标题，不再进旁白
- 拆解依据：抖音「早安电台」3 条爆款（25~27s），公式=预言+金句雨+祝福

## 一句话用法

```
"<YOUR_PYTHON>" "<PLATFORM_ROOT>/daily_pipeline.py" <行业> [YYYY-MM-DD]
```

推荐直接使用 360 主包引擎（示例）：

```
python morning-radio-360-industries/assets/platform/daily_pipeline.py beauty
```

也可设置 `MORNING_RADIO_PYTHON=<YOUR_PYTHON>` 后调用相对路径脚本。不填日期默认今天。约 45~60 秒出全套产物。

## 固定资产（相对 `<PLATFORM_ROOT>`，勿写死本机盘符）

| 资产 | 路径 |
|---|---|
| Python 环境（含 PIL/edge-tts/numpy/cnlunar） | `<YOUR_PYTHON>` 或环境变量 `MORNING_RADIO_PYTHON` |
| 流水线总入口 | `<PLATFORM_ROOT>/daily_pipeline.py`（完整实现见 360 `assets/platform/`） |
| 每日文案 / 行业词库 | `<PLATFORM_ROOT>/industries/` + `copy_base.py`（cnlunar 算农历/节气/节日，主题按日轮换） |
| 封面模板脚本 | `<PLATFORM_ROOT>/replicate_cover.py`（版式已定格，勿改坐标） |
| 透明日历层脚本 | `<PLATFORM_ROOT>/make_calendar_overlay.py` |
| 片头合成脚本 | `<PLATFORM_ROOT>/add_calendar_intro.py` |
| 渲染引擎 | `<PLATFORM_ROOT>/render.py` |
| 封面干净底图 | `<PLATFORM_ROOT>/assets/bg_cover.png`（用户自备；换季才换） |
| 六槽位视频素材 | `<PLATFORM_ROOT>/materials/<行业>/`（文件名 `01_`~`06_` 开头） |
| BGM 曲库 | `<PLATFORM_ROOT>/bgm/`（mp3/wav/m4a/flac/ogg，按年内天数取模轮换；空则回退默认曲） |
| 成品输出 | `<PLATFORM_ROOT>/output/<行业>_<日期>/` |

## 流水线内部步骤（排障时才需要看）

1. 文案组装（行业词库 / `copy_base`）→ 六槽位旁白 + 封面副标题 + 日历节日名 → 存 `<PLATFORM_ROOT>/projects/<行业>/daily/<日期>_copy.json`
2. `replicate_cover.py` 逻辑 → 平台封面 `cover_<日期>.jpg`（720×1280，定格版式）
3. `make_calendar_overlay.py` 逻辑 → 透明日历层 `calendar_overlay_<日期>.png`（720×1280 RGBA）
4. 生成项目 JSON → `render.py` 渲染正文（edge-tts 晓晓女声 / 词级 ASS 卡点字幕 / 【关键词】橙色+放大 1.25 倍高亮 / 莫兰迪调色 / BGM 混音 / 响度标准化 / **旁白守卫自动撑长槽位**）
5. `add_calendar_intro.py` → 前 3 秒透明日历覆盖在**播放中的视频**上，0.6s 淡出 → `morning_radio_<日期>_final.mp4`

## 字幕关键词放大（v2.2）

- `render.py` 的 `build_ass()`：命中关键词的 ASS 标签为 `{\c&H橙色&\fs<放大字号>}`，关键词后自动重置字号/颜色
- 默认放大 1.25 倍（font_size 92 → 115）；要固定值可在项目 JSON 的 subtitles 样式里加 `"kw_font_size": <数值>`
- 效果：钩子/CTA 里的关键词（好运/成功/开心…）比周围字幕大且橙色，观众扫一眼就知道今天该发什么词

## 渲染时长保障（v2.2 防结尾黑屏 / v2.2.1 防旁白被截 / v2.2.2 防暗尾）

- `build_render()` 每段素材链带 `trim=duration={槽位有效时长},setpts=PTS-STARTPTS`，确保**视频实际长度 = 设计总长**（各槽 max_duration 之和 - 转场重叠）
- 无 trim 时素材全长参与 xfade 合成，视频被拉长、片尾淡出后又挂出数秒死黑屏（2026-08-28 曾出现 1.7s 黑屏，已修复）
- **旁白守卫（v2.2.1）**：`render.py` 在 TTS 完成后用 `audio_dur + narration_tail` 反推设计总长；若旁白比设计总长长，按素材余量等比例撑长各槽位，素材不够则末槽自动冻帧兜底，避免 `-shortest` 截断最后一句 CTA
- **结尾淡化（v2.2.2）**：`narration_tail` 默认 0.6s、片尾视频淡出 `end_fade` 默认 0.6s（淡出起点 = 旁白结束点）；音频 afade 起点取 `max(旁白时长, 视频淡出起点)`，防削尾字。旁白说完 → 0.6s 利落淡出 → 结束即黑，不再有 1~2s 暗黑尾（旧参数 1.2s 尾 + 1.0s 淡出曾造成观感黑屏）
- 质检可用：
  - 黑屏：`ffmpeg -i 成片.mp4 -vf "blackdetect=d=0.5:pic_th=0.98" -an -f null -`，应无 >0.5s 黑场
  - 结尾淡化：抽帧量亮度 `signalstats YAVG`，旁白结束前应全亮，淡出只占最后 0.6s，结束即黑无死黑尾
  - 旁白完整：`ffprobe -select_streams a:0 -show_entries stream=duration 成片.mp4`，应 > 旁白音频本身时长且末句不突兀结束

## 定格封面版式（720×1280，勿动坐标）

1. `August 2026` 金色大字距月历头（y=125，字距12）
2. 大号白色日期数字 `08 吉祥 27`（day_y=205，中间红色圆角竖印章「吉祥」，描边2px）
3. 农历（金色）/ 星期（浅色）：`lunar_y = day_y + left_h + 60`（**用户定格，勿上调**，否则压数字底部）
4. 节日名白色描边（lunar_y + 55；无节日时放「早安」）
5. 底部副标题（y=1100，白字描边）
6. 顶部+底部压暗渐变，文字全部带黑描边

## 素材替换规则（给用户看的）

- 视频放 `<PLATFORM_ROOT>/materials/<行业>/`（或自备素材目录），文件名以 `01_` ~ `06_` 开头（01钩子/02交代/03铺垫/04转折/05金句/06CTA），后缀描述随便写
- 横屏/竖屏/4K/手机拍均可，自动居中裁切到 1080×1920；支持 mp4/mov/mkv/avi/webm/m4v
- 素材原声丢弃（成片只有旁白+BGM），每段建议 3~5 秒
- 同编号多文件取排序第一个；替换时删旧文件或去掉旧文件编号
- BGM 新曲直接丢进 `<PLATFORM_ROOT>/bgm/`（或 `MORNING_RADIO_BGM_DIR`），无需改代码；**请确认曲目授权，勿未授权分发**

## 交付前质检清单

- [ ] 封面：日期数字与农历/星期不重叠、印章居中、副标题完整、农历正确（cnlunar 偶有偏差，发布前对照手机日历）
- [ ] 成片抽帧：t≈0.5（日历满覆盖）、t≈2.7（淡出中）、t≈4.5（正文+字幕）、t≈结尾（CTA 字幕）
- [ ] 听 BGM 音量（当前 0.12）是否压过旁白
- [ ] 输出时长 ≈20~25s（旁白守卫会自动撑长到能完整播完旁白）、1080×1920；blackdetect 应无 >0.5s 黑场
- [ ] 钩子/CTA 关键词首尾呼应且字幕放大生效（抽帧 t≈0.5 和 t≈结尾对照）
- [ ] 最后一句 CTA 要听完，不能明显感觉被截断

## 常见问题

| 现象 | 处理 |
|---|---|
| 报「素材槽位 NN 缺失」 | 素材目录缺对应 `NN_` 编号文件，补齐即可 |
| BGM 报错无法解码 | 多为酷狗 `.kgma` 加密格式，让用户换无加密版本（mp3/flac） |
| 农历/节日不对 | cnlunar 个别日期有偏差，手动改当日 copy.json 后重跑 |
| 结尾出现数秒黑屏 | 渲染引擎缺 trim 裁剪（旧版 bug），确认 `render.py` 每段素材链带 `trim=duration=…`；本仓 v2.2 已修复 |
| 视频结束旁白没结束 / CTA 被切 | 旁白比设计总长长被 `-shortest` 截断；确认 `render.py` 已加 `fit_durations_to_narration` 守卫；本仓 v2.2.1 已修复 |
| 钩子/CTA 关键词对不上 | `daily_copy.py` 的 INTERACTIVE_CTAS 必须含 `{kw}` 占位符且钩子含【关键词】，缺失则首尾不呼应 |
| 片头日历是静态图盖屏 | 用错了整张封面 JPG；必须用透明 PNG（make_calendar_overlay 产物） |
| 换季想换底图 | 用 ImageGen 生成同构图（上部留白、无文字）新底图，替换 BG_IMAGE，版式不变 |

## 周边约定

- 发布后可按自身节奏复盘数据
- 文案公式对标公开平台常见「早安电台」互动钩子结构，按需调整词库即可
- 封面/日历层默认用 Windows 自带 simhei/msyh；跨平台请换思源等字体并改脚本候选路径
