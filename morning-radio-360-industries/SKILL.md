---
name: morning-radio-360-industries
description: 「360行业早安电台」日更短视频生成平台（三百六十行通用版）。当用户要为任意行业商家（美业、五金机电、餐饮美食、服装穿搭、家居生活、健身运动及一切实体行业）批量生成日更早安软广告短视频、新增行业词库、运行行业流水线出片、或启动/使用行业网页版（商家自助上传素材生成视频）时使用本 skill。触发词：360行业、360行业skill、三百六十行、行业早安电台、industry_hub、行业流水线、给某行业做早安视频、多行业平台、行业版早安电台、商家日更视频平台。完整平台代码模板在 assets/platform/。
agent_created: true
---

# 360行业早安电台平台（morning-radio-360-industries）

> 又名「360行业skill」：一套流水线，三百六十行通用——任何实体行业 10 分钟接入，每天一键生成自己行业的早安软广告短视频。

## 概述

为任意实体行业商家生产**日更早安软广告短视频**的一键流水线平台。一条成片（20~25s，1080×1920）= 预言式互动钩子 + 日期问候 + 行业软广三段（铺垫/转折/金句）+ 互动 CTA 收尾，含封面、日历片头、词级卡点字幕、BGM 混音。商家视角：每天一条行业正能量的同时打自己的软广告。

部署根目录请设为 `<PLATFORM_ROOT>`（任意本机路径均可）。skill 的 `assets/platform/` 内含全套平台代码模板：复制到目标机后，按 `references/architecture.md` 与 `assets/platform/config.example.py` 配置路径即可。

## 工作流决策树

1. **为现有行业出片** → 确认素材就位 → 跑 `daily_pipeline.py <行业> [日期]` → 质检
2. **新增行业** → 读 `references/add-industry-guide.md` → 写词库文件 + 登记 → 跑 `scripts/validate_industries.py` 校验 → 渲染样本片
3. **给外部商家用（网页版）** → 启动 `webapp.py` → 浏览器操作流程见 `references/architecture.md`
4. **部署到新机器/服务器** → 复制 `assets/platform/` → 按 `config.example.py` / 环境变量配置 `BG_IMAGE`/`BGM_*`/`PY`（详见 `references/architecture.md`）

## 快速命令

```bash
# 出片（在平台根目录 industry_hub/ 下）
python daily_pipeline.py beauty 2026-08-29          # 指定行业+日期
python daily_pipeline.py hardware                    # 默认今天
python daily_pipeline.py food 2026-08-30 --skip-render  # 只出文案+封面+日历层

# 词库批量校验（首尾呼应/农历/封面字段/六槽位完整性）
python validate_industries.py 2026-08-29

# 网页版（Flask，商家自助：建工作区→传6槽位素材→文案可手改→渲染→下载）
python webapp.py 127.0.0.1 8000    # 浏览器打开 http://127.0.0.1:8000
```

Python 解释器需为含 ffmpeg 调用环境：设置环境变量 `MORNING_RADIO_PYTHON=<YOUR_PYTHON>`，或复制 `assets/platform/config.example.py` 为 `config.py` 填写 `PY`（依赖：edge-tts、cnlunar、Pillow、Flask）。未配置时默认使用当前 `python`/`sys.executable`。

## 核心机制（勿破坏）

- **词库插件化**：行业 = `industries/<id>.py` 纯数据文件（8 预言钩子 + 5 CTA 模板 + 14 主题 + 称呼），共用 `copy_base.py` 组装。新增行业不改任何引擎代码。
- **按日轮换（非随机）**：钩子/主题/CTA 均按 `年内第几天 % 库长` 取值——同一天可复现，8/14/5 周期互质约 56 天不重样；节日/节气优先于日常轮换。
- **首尾呼应**：CTA 模板用 `{kw}` 占位符，`_extract_kw()` 从当天钩子【】提取关键词自动填充——钩子说"【财源】"，结尾就让人打"财源"。
- **封面字段**：`festival = 节日 or 节气 or "早安"`（平日必须 fallback 显示"早安"大字）；`cover_subtitle = 今天是{月}月{日}日`；农历取自 cnlunar。
- **渲染引擎 v2.2.2**：trim 防黑屏 + 旁白守卫（`fit_durations_to_narration`，视频不会早于旁白结束）+ 淡化收尾（narration_tail=0.6s、淡出起点=旁白结束点）+ 关键词字幕放大（kw_font_size 默认 1.25 倍）。改动需求先读 `references/architecture.md` 的引擎能力表。
- **素材自动识别**：`materials/<行业>/` 下文件名以 `01_`~`06_` 编号开头即对应槽位（钩子→交代→铺垫→转折→金句→CTA）。

## 出片后质检清单

1. 首尾呼应：开场钩子关键词 = 结尾 CTA 让观众打的词
2. 封面：农历X月X日、星期、早安大字、今天是X月X日齐全
3. 成片时长 ≈ 旁白时长 + 0.6s，无黑屏死尾（结尾为 0.6s 淡出）
4. 最后一句 CTA 完整可听清（旁白守卫生效标志）
5. 关键词在字幕中有橙色放大效果

## 常见坑（历史修复记录）

| 症状 | 根因与修法 |
|---|---|
| 封面无农历 | cnlunar 的 `Lunar()` 必须传 `datetime.datetime`（不是 `date`），异常被吞会静默返回空 |
| 封面无「早安」大字 | `festival` 未做 `or "早安"` fallback |
| 首尾不呼应 | CTA 模板漏写 `{kw}` 占位符，或钩子关键词没用【】包裹 |
| 视频结束旁白没结束 | 旁白守卫 `fit_durations_to_narration` 被改掉或移除 |
| 结尾 2s 黑屏 | 某槽位 trim 链被破坏；或淡出参数被改回长尾 |
| 网页版看不到新行业 | 行业表启动时载入，需重启 webapp；前端 `IND_EMOJI` 也要补表情 |
| 词库 ImportError | 词库首行要用相对导入 `from .copy_base import build_copy` |

## 资源清单

- `assets/platform/` — 全套平台代码模板（渲染引擎 4 脚本 + 通用流水线 + 网页版前后端 + 6 行业词库），部署新机器时整体复制
- `scripts/validate_industries.py` — 行业词库批量校验（首尾呼应/农历/封面字段/槽位完整性）
- `references/architecture.md` — 平台架构、渲染引擎能力表、流水线接口、网页版要点、部署路径配置
- `references/add-industry-guide.md` — 新增行业词库规范（钩子/CTA/主题写法）、素材槽位分配、验证流程

## 路线背景

网页版可用于商家自助出片验证；默认仅监听本机 `127.0.0.1`，模板不附带登录校验——对公网开放前请自行加登录校验与反代。完整引擎代码即本包 `assets/platform/`。单账号文档型说明见可选包 `morning-radio-pipeline`（v2.2.2）；可运行实现以本包为准。BGM/底图需用户自备并确认版权。
