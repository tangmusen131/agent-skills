# -*- coding: utf-8 -*-
"""
行业版「早安电台」文案通用基座（copy_base.py）
=============================================
所有行业词库共用：预言钩子轮换 + 日期问候 + 铺垫 + 转折 + 金句 + 互动CTA
行业文件只需提供：PREDICTION_HOOKS / CTA_TEMPLATES / THEMES / ADDRESS

旁白公式：预言钩子 → 日期问候 → 铺垫 → 转折 → 金句 → 互动 CTA
关键词自动从钩子提取，保证首尾呼应。
"""
import datetime
import re
from typing import Dict, List


# ============= 农历/节气/节日检测（cnlunar） =============
def _lunar_info(date: datetime.date) -> Dict:
    try:
        from cnlunar import Lunar
    except ImportError:
        return {"festival": "", "solar_term": "", "lunar_month_day": ""}
    try:
        dt = datetime.datetime(date.year, date.month, date.day)
        l = Lunar(dt, godType="8char")
        festival = l.get_legalHolidays() or ""
        solar_term = l.todaySolarTerms if l.todaySolarTerms != "无" else ""
        lunar_month = l.lunarMonthCn.rstrip("大小") if l.lunarMonthCn else ""
        lunar_day = l.lunarDayCn
        return {
            "festival": festival,
            "solar_term": solar_term,
            "lunar_month_day": f"农历{lunar_month}{lunar_day}",
        }
    except Exception:
        return {"festival": "", "solar_term": "", "lunar_month_day": ""}


# ============= CTA 关键词自动提取 =============
def _extract_kw(pred_hook: str) -> str:
    """从预言钩子里提取【关键词】，作为 CTA 填充（取最后一个【】）"""
    matches = re.findall(r"【([^】]+)】", pred_hook)
    if len(matches) >= 2:
        return matches[-1]
    if len(matches) == 1:
        return matches[0]
    return "好运"


# ============= 日期问候 =============
def _greeting(date: datetime.date, address: str) -> str:
    weekday_cn = "一二三四五六日"[date.weekday()]
    return f"今天是{date.month}月{date.day}日，星期{weekday_cn}，{address}早安"


# ============= 通用主函数 =============
def build_copy(
    date: datetime.date,
    industry_id: str,
    industry_name: str,
    address: str,
    prediction_hooks: List[str],
    cta_templates: List[str],
    themes: List[Dict],
) -> Dict:
    yday = date.timetuple().tm_yday
    pred_hook = prediction_hooks[yday % len(prediction_hooks)]
    theme = themes[yday % len(themes)]
    kw = _extract_kw(pred_hook)
    inter_cta = cta_templates[yday % len(cta_templates)].format(kw=kw)
    greeting = _greeting(date, address)
    lunar = _lunar_info(date)
    festival = lunar.get("festival", "") or lunar.get("solar_term", "") or "早安"

    narration = (
        f"{pred_hook}。"
        f"{greeting}。"
        f"{theme['lead']}。"
        f"{theme['turn']}。"
        f"{theme['golden']}。"
        f"{inter_cta}。"
    )
    return {
        "date": date.isoformat(),
        "industry": industry_id,
        "industry_name": industry_name,
        "slots": {
            "钩子": pred_hook,
            "交代": greeting,
            "铺垫": theme["lead"],
            "转折": theme["turn"],
            "金句": theme["golden"],
            "CTA": inter_cta,
        },
        "theme_name": theme["name"],
        "highlight_keyword": kw,
        "lunar_info": lunar,
        "festival": festival,
        "narration": narration,
        "cover_subtitle": f"今天是{date.month}月{date.day}日",
    }
