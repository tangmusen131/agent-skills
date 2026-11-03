# 平台架构与部署（architecture.md）

## 平台定位

「多行业早安电台」平台（industry_hub）：给任意实体行业商家生产**日更早安软广告短视频**的一键流水线。
一条成片 = 预言式互动钩子 + 日期问候 + 行业软广三段（铺垫/转折/金句）+ 互动 CTA 收尾，约 20~25 秒，1080×1920 竖屏。

## 目录结构

```
industry_hub/
├── daily_pipeline.py          ← 通用流水线（所有行业共用入口）
├── render.py                  ← 渲染引擎 v2.2.2（六槽位/字幕卡点/旁白守卫/淡化收尾）
├── replicate_cover.py         ← 封面生成（农历/星期/节日/早安大字）
├── make_calendar_overlay.py   ← 透明日历片头图层
├── add_calendar_intro.py      ← 3 秒日历片头合成 + 淡出
├── webapp.py                  ← 网页版后端（Flask，商家自助用）
├── webapp_static/index.html   ← 网页版前端
├── industries/                ← 行业词库（插件化）
│   ├── __init__.py            ← 行业注册表 INDUSTRIES = {"hardware": "五金机电", ...}
│   ├── copy_base.py           ← 词库通用基座（农历/钩子提取/CTA填充/六槽位组装）
│   ├── beauty.py / hardware.py / food.py / fashion.py / home.py / fitness.py
├── materials/<行业>/          ← 各行业 6 槽位素材（文件名 01_钩子_xxx.mp4 ~ 06_CTA_xxx.mp4 自动识别）
├── projects/<行业>/daily/     ← 每日文案 JSON（<日期>_copy.json）
├── output/<行业>_<日期>/      ← 产物：cover_<日期>.jpg / calendar_overlay_<日期>.png /
│                                 morning_radio_<日期>.mp4（正文）/ morning_radio_<日期>_final.mp4（最终）
└── workspaces/<ws_id>/        ← 网页版商家工作区（上传素材存放处）
```

## 渲染引擎能力（render.py v2.2.2）

| 能力 | 参数/机制 |
|---|---|
| 六槽位结构 | 钩子→交代→铺垫→转折→金句→CTA，按槽位素材自动对位 |
| 词级卡点字幕 | edge-tts 旁白 + ASS 字幕，关键词橙色放大 |
| 关键词放大 | `kw_font_size` 默认 font_size×1.25（92→115），可在 config 覆盖 |
| trim 防黑屏 | 每段素材链 `trim=duration=X,setpts=PTS-STARTPTS`，视频实际长度=设计总长 |
| 旁白守卫 | `fit_durations_to_narration()`：TTS 完成后用 audio_dur+tail 反推总长，等比例撑长槽位；余量不足末槽 tpad=clone 冻帧 |
| 淡化收尾 | `narration_tail=0.6s`；视频淡出起点=旁白结束点 0.6s；音频 afade 起点=max(旁白时长, 总长-0.6) |
| 响度标准化 | loudnorm I=-14 TP=-1.5 LRA=11 |
| BGM | 按年内第几天取模轮换（跨行业共用一个 BGM 库） |

## 流水线接口（daily_pipeline.py）

命令行：`python daily_pipeline.py <行业id> [日期YYYY-MM-DD] [--skip-render]`

函数式（网页版复用）：
```python
run(industry_id, date, skip_render=False, narration_override=None,
    materials_dir=None, out_dir=None, progress_cb=None)
```
- `narration_override`：用户手改后的旁白全文
- `progress_cb(stage, text)`：5 阶段进度回调（文案/封面/日历层/渲染/片头）

## 网页版（webapp.py，Flask）

启动：`python webapp.py [host] [port]`（默认 8000）

商家流程：填商家名建工作区 → 选行业 → 6 槽位素材上传（一次即可）→ 生成文案可手改 → 点生成（约 1 分钟）→ 下载封面+成片。

要点：
- 行业表是**启动时载入**的，加新行业后必须重启 webapp 才生效
- 前端 `index.html` 的 `IND_EMOJI` 映射需为新行业补表情
- 渲染用 Semaphore 串行防 CPU 打满；任务后台线程执行，`/api/task/<id>` 轮询进度
- 工作区素材在 `workspaces/<ws_id>/<行业>/01_~06_*.mp4`

## 部署配置（路径勿写死本机绝对路径）

优先用环境变量，或复制 `config.example.py` → `config.py`（本地文件，勿进发布包）：

| 配置 / 环境变量 | 说明 |
|---|---|
| `BG_IMAGE` / `MORNING_RADIO_BG_IMAGE` | 封面底图（竖版干净构图，建议 720×1280，无水印；**用户自备，版权自负**） |
| `BGM_DIR` / `MORNING_RADIO_BGM_DIR` | BGM 库目录（默认相对平台根 `./bgm`；**用户自备授权曲目**） |
| `BGM_DEFAULT` / `MORNING_RADIO_BGM_DEFAULT` | 曲库为空时的回退曲 |
| `PY` / `MORNING_RADIO_PYTHON` | Python 解释器（需可用 ffmpeg + edge-tts + cnlunar + Pillow）；未设则用当前解释器 |
| 字体 | 封面/日历默认依赖 Windows `C:/Windows/Fonts/msyh*.ttc` / `simhei.ttf`；Linux/macOS 请换成思源黑体等并改脚本内字体候选列表 |

相对路径默认值（相对 `assets/platform/` = `<PLATFORM_ROOT>`）：`./assets/bg_cover.png`、`./bgm/`、`./output/`、`./materials/<行业>/`。

环境依赖：`ffmpeg`（含 subtitles/loudnorm 滤镜）、`edge-tts`、`cnlunar`、`Pillow`、`Flask`。

## 网页版安全注意

`webapp.py` 默认可绑定 `0.0.0.0`，**无登录鉴权**。仅建议本机或受信内网试用；公网暴露前务必加鉴权、HTTPS 与反向代理。

## 与单账号流水线文档的关系

- 可运行引擎与多行业词库以本包 `assets/platform/` 为准
- 可选文档包 `morning-radio-pipeline`（v2.2.2）描述单账号日更流程；其中脚本相对路径指向本引擎的同源实现
- 行业平台为多行业插件化扩展，不依赖外部本机私有目录
