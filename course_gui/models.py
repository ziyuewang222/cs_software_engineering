"""数据模型：Course / Homework，纯 dataclass，不依赖 GUI。"""
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime


def new_id() -> str:
    return uuid.uuid4().hex[:8]


DATETIME_FMT = "%Y-%m-%d %H:%M"


@dataclass
class Course:
    id: str = field(default_factory=new_id)
    name: str = ""
    weekday: int = 1  # 1=周一 ... 7=周日
    start_section: int = 1
    end_section: int = 2
    location: str = ""
    teacher: str = ""
    color: str = "#4C8DFF"

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("课程名不能为空")
        if not 1 <= self.weekday <= 7:
            raise ValueError("weekday 必须在 1~7 之间")
        if self.start_section < 1 or self.end_section < 1:
            raise ValueError("节次必须 >= 1")
        if self.start_section > self.end_section:
            raise ValueError("开始节不能大于结束节")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Course":
        return cls(
            id=str(d.get("id") or new_id()),
            name=str(d.get("name", "")),
            weekday=int(d.get("weekday", 1)),
            start_section=int(d.get("start_section", 1)),
            end_section=int(d.get("end_section", 2)),
            location=str(d.get("location", "")),
            teacher=str(d.get("teacher", "")),
            color=str(d.get("color", "#4C8DFF")),
        )


@dataclass
class Homework:
    id: str = field(default_factory=new_id)
    course_id: str = ""
    course_name: str = ""  # 冗余存放，方便 CSV 导入导出与显示
    title: str = ""
    deadline: str = ""  # 格式 YYYY-MM-DD HH:MM
    done: bool = False
    remark: str = ""

    def validate(self) -> None:
        if not self.title.strip():
            raise ValueError("作业标题不能为空")
        if not self.deadline.strip():
            raise ValueError("截止时间不能为空")
        parse_deadline(self.deadline)  # 格式校验

    def deadline_dt(self) -> datetime:
        return parse_deadline(self.deadline)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Homework":
        return cls(
            id=str(d.get("id") or new_id()),
            course_id=str(d.get("course_id", "")),
            course_name=str(d.get("course_name", "")),
            title=str(d.get("title", "")),
            deadline=str(d.get("deadline", "")),
            done=bool(d.get("done", False)),
            remark=str(d.get("remark", "")),
        )


def parse_deadline(s: str) -> datetime:
    try:
        return datetime.strptime(s.strip(), DATETIME_FMT)
    except ValueError:
        raise ValueError(f"截止时间格式错误，应为 YYYY-MM-DD HH:MM，例如 2026-10-10 23:59，实际：{s!r}")
