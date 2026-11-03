# -*- coding: utf-8 -*-
"""行业注册表：新增行业只需在此登记，词库文件放本目录"""
import importlib

INDUSTRIES = {
    "beauty": "美业",
    "hardware": "五金机电",
    "food": "餐饮美食",
    "fashion": "服装穿搭",
    "home": "家居生活",
    "fitness": "健身运动",
}


def load_copy_module(industry_id: str):
    """动态加载行业词库模块，需提供 build(date) 函数"""
    if industry_id not in INDUSTRIES:
        raise ValueError(f"未知行业: {industry_id}，可选: {list(INDUSTRIES.keys())}")
    return importlib.import_module(f"industries.{industry_id}")
