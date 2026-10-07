"""步骤4：截止提醒扫描逻辑（纯函数，方便单测，不依赖 GUI）。"""
from __future__ import annotations

from datetime import datetime

from .models import Homework

WARN_HOURS = 24.0   # 列表标红阈值
POPUP_HOURS = 1.0   # 弹窗阈值


def classify(hw: Homework, now: datetime | None = None) -> str:
    """返回作业紧急程度：done / overdue / urgent(<24h) / popup(<1h) / normal。"""
    if hw.done:
        return "done"
    now = now or datetime.now()
    try:
        delta = hw.deadline_dt() - now
    except ValueError:
        return "normal"
    secs = delta.total_seconds()
    if secs < 0:
        return "overdue"
    if secs <= POPUP_HOURS * 3600:
        return "popup"
    if secs <= WARN_HOURS * 3600:
        return "urgent"
    return "normal"


def scan(hws: list[Homework], now: datetime | None = None) -> dict[str, list[Homework]]:
    """扫一遍全部作业，按紧急程度分组。"""
    out: dict[str, list[Homework]] = {"overdue": [], "popup": [], "urgent": [], "normal": [], "done": []}
    for h in hws:
        level = classify(h, now)
        if level == "popup":
            # 既标红也弹窗：同时进两组
            out["popup"].append(h)
            out["urgent"].append(h)
        else:
            out[level if level in out else "normal"].append(h)
    return out
