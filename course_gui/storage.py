"""数据层：DataStore 负责 data.json 读写、CRUD、CSV 导入导出。"""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from .models import Course, Homework, new_id

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_FILE = BASE_DIR / "data.json"


class DataStore:
    def __init__(self, data_file: Path | str = DEFAULT_DATA_FILE):
        self.data_file = Path(data_file)
        self.courses: list[Course] = []
        self.homeworks: list[Homework] = []
        self.load()

    # ---------- 持久化 ----------
    def load(self) -> None:
        if not self.data_file.exists():
            self.courses, self.homeworks = [], []
            return
        try:
            raw = json.loads(self.data_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            self.courses, self.homeworks = [], []
            return
        self.courses = [Course.from_dict(d) for d in raw.get("courses", [])]
        self.homeworks = [Homework.from_dict(d) for d in raw.get("homeworks", [])]

    def save(self) -> None:
        payload = {
            "courses": [c.to_dict() for c in self.courses],
            "homeworks": [h.to_dict() for h in self.homeworks],
        }
        self.data_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---------- Course CRUD ----------
    def add_course(self, course: Course) -> Course:
        course.validate()
        if not course.id:
            course.id = new_id()
        self.courses.append(course)
        self.save()
        return course

    def update_course(self, course: Course) -> Course:
        course.validate()
        for i, c in enumerate(self.courses):
            if c.id == course.id:
                self.courses[i] = course
                self.save()
                return course
        raise KeyError(f"课程不存在：{course.id}")

    def delete_course(self, course_id: str) -> None:
        self.courses = [c for c in self.courses if c.id != course_id]
        self.homeworks = [h for h in self.homeworks if h.course_id != course_id]
        self.save()

    def get_course(self, course_id: str) -> Course | None:
        return next((c for c in self.courses if c.id == course_id), None)

    def find_course_by_name(self, name: str) -> Course | None:
        return next((c for c in self.courses if c.name == name), None)

    # ---------- Homework CRUD ----------
    def add_homework(self, hw: Homework) -> Homework:
        hw.validate()
        if hw.course_id and not hw.course_name:
            c = self.get_course(hw.course_id)
            if c:
                hw.course_name = c.name
        self.homeworks.append(hw)
        self.save()
        return hw

    def update_homework(self, hw: Homework) -> Homework:
        hw.validate()
        for i, h in enumerate(self.homeworks):
            if h.id == hw.id:
                self.homeworks[i] = hw
                self.save()
                return hw
        raise KeyError(f"作业不存在：{hw.id}")

    def delete_homework(self, hw_id: str) -> None:
        self.homeworks = [h for h in self.homeworks if h.id != hw_id]
        self.save()

    def mark_done(self, hw_id: str, done: bool = True) -> Homework:
        hw = next((h for h in self.homeworks if h.id == hw_id), None)
        if hw is None:
            raise KeyError(f"作业不存在：{hw_id}")
        hw.done = done
        self.save()
        return hw

    def pending_sorted(self) -> list[Homework]:
        items = [h for h in self.homeworks if not h.done]
        items.sort(key=lambda h: h.deadline_dt())
        return items

    def due_within(self, hours: float, now: datetime | None = None) -> list[Homework]:
        from datetime import timedelta
        now = now or datetime.now()
        out = []
        for h in self.homeworks:
            if h.done:
                continue
            try:
                delta = h.deadline_dt() - now
            except ValueError:
                continue
            if timedelta(0) <= delta <= timedelta(hours=hours):
                out.append(h)
        out.sort(key=lambda h: h.deadline_dt())
        return out

    # ---------- CSV ----------
    def import_courses_csv(self, path: Path | str) -> tuple[int, list[str]]:
        ok, errors = 0, []
        with open(path, encoding="utf-8-sig", newline="") as f:
            for lineno, row in enumerate(csv.DictReader(f), start=2):
                try:
                    c = Course(
                        name=row.get("课程名", "").strip(),
                        weekday=int(row.get("星期", "1").strip()),
                        start_section=int(row.get("开始节", "1").strip()),
                        end_section=int(row.get("结束节", "2").strip()),
                        location=row.get("地点", "").strip(),
                        teacher=row.get("老师", "").strip(),
                    )
                    self.add_course(c)
                    ok += 1
                except Exception as e:  # noqa: BLE001 - 需要逐行收集错误
                    errors.append(f"第{lineno}行：{e}")
        self.save()
        return ok, errors

    def import_homeworks_csv(self, path: Path | str) -> tuple[int, list[str]]:
        ok, errors = 0, []
        with open(path, encoding="utf-8-sig", newline="") as f:
            for lineno, row in enumerate(csv.DictReader(f), start=2):
                try:
                    cname = row.get("课程名", "").strip()
                    course = self.find_course_by_name(cname)
                    hw = Homework(
                        course_id=course.id if course else "",
                        course_name=cname,
                        title=row.get("标题", "").strip(),
                        deadline=row.get("截止时间", "").strip(),
                        remark=row.get("备注", "").strip(),
                    )
                    self.add_homework(hw)
                    ok += 1
                except Exception as e:  # noqa: BLE001
                    errors.append(f"第{lineno}行：{e}")
        self.save()
        return ok, errors

    def export_courses_csv(self, path: Path | str) -> None:
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["课程名", "星期", "开始节", "结束节", "地点", "老师"])
            for c in self.courses:
                w.writerow([c.name, c.weekday, c.start_section, c.end_section, c.location, c.teacher])

    def export_homeworks_csv(self, path: Path | str) -> None:
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["课程名", "标题", "截止时间", "备注"])
            for h in self.homeworks:
                w.writerow([h.course_name, h.title, h.deadline, h.remark])


def _selftest() -> None:
    import tempfile
    tmp = Path(tempfile.mkdtemp()) / "data.json"
    ds = DataStore(tmp)
    c = ds.add_course(Course(name="高等数学", weekday=1, start_section=1, end_section=2, location="教3-201"))
    ds.add_homework(Homework(course_id=c.id, course_name=c.name, title="第三章习题", deadline="2026-10-10 23:59"))
    assert len(ds.courses) == 1 and len(ds.homeworks) == 1
    ds2 = DataStore(tmp)  # 验证持久化
    assert len(ds2.courses) == 1, "JSON 持久化失败"
    assert ds2.pending_sorted()[0].title == "第三章习题"
    print("存储自测通过: CRUD + JSON持久化 + 排序 OK")


if __name__ == "__main__":
    _selftest()
