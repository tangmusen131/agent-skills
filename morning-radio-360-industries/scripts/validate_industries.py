# -*- coding: utf-8 -*-
"""
行业词库批量校验脚本（validate_industries.py）
================================================
用法（在行业平台根目录下，如 industry_hub/）：
    python validate_industries.py [日期YYYY-MM-DD]

校验项：
  1. 所有行业词库可正常导入并生成当日文案
  2. 首尾呼应：CTA 中包含当天钩子提取的关键词（{kw} 占位符正确填充）
  3. 农历字段非空（cnlunar 用法正确：必须传 datetime.datetime）
  4. 封面字段：festival 平日 fallback 为「早安」；cover_subtitle 为「今天是X月X日」
  5. 旁白为完整六槽位（钩子/交代/铺垫/转折/金句/CTA）
"""
import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 兼容：脚本既可放平台根目录，也可放 skill scripts/ 下（通过 --path 指定平台目录）

try:
    from industries import INDUSTRIES, load_copy_module
except ImportError:
    platform_dir = sys.argv[1] if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]) else "."
    sys.path.insert(0, platform_dir)
    os.chdir(platform_dir)
    from industries import INDUSTRIES, load_copy_module


def main():
    date_str = None
    for a in sys.argv[1:]:
        if not a.startswith("-") and a.count("-") == 2:
            date_str = a
    date = datetime.date.fromisoformat(date_str) if date_str else datetime.date.today()

    all_ok = True
    print(f"=== 行业词库校验 {date.isoformat()} ===")
    for iid, name in INDUSTRIES.items():
        try:
            c = load_copy_module(iid).build(date)
        except Exception as e:
            print(f"[FAIL] {name}: 词库导入/生成异常 -> {e}")
            all_ok = False
            continue

        errs = []
        kw = c["highlight_keyword"]
        if kw not in c["slots"]["CTA"]:
            errs.append(f"首尾不呼应(CTA缺关键词{kw})")
        if not c["lunar_info"].get("lunar_month_day"):
            errs.append("农历为空(cnlunar须传datetime.datetime)")
        if not c["festival"]:
            errs.append("封面大字为空(应fallback为早安)")
        if "月" not in c["cover_subtitle"]:
            errs.append(f"封面副标题异常({c['cover_subtitle']})")
        slots = c["slots"]
        for s in ("钩子", "交代", "铺垫", "转折", "金句", "CTA"):
            if not slots.get(s):
                errs.append(f"槽位{s}为空")

        status = "OK " if not errs else "FAIL"
        if errs:
            all_ok = False
        print(f"[{status}] {name:6s} 关键词={kw:4s} 主题={c['theme_name']:6s} "
              f"农历={c['lunar_info']['lunar_month_day']:8s} 封面大字={c['festival']}")
        for e in errs:
            print(f"       - {e}")

    print("=== 全部通过 ===" if all_ok else "=== 存在问题，请修复后重跑 ===")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
