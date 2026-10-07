"""步骤3+4：真实数据渲染 + GUI 全交互 + 定时提醒 + QSS 美化。"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QCalendarWidget,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from . import reminder
from .dialogs import CourseDialog, HomeworkDialog
from .models import Course, Homework
from .storage import DataStore

WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


class MainWindow(QMainWindow):
    def __init__(self, store: DataStore | None = None) -> None:
        super().__init__()
        self.store = store or DataStore()
        self.setWindowTitle("课程作业管理系统")
        self.resize(1100, 650)
        self._build_ui()
        self.refresh_all()

    # ---------- 界面搭建 ----------
    def _build_ui(self) -> None:
        # 顶部工具栏
        top_bar = QHBoxLayout()
        self.btn_add_course = QPushButton("添加课程")
        self.btn_add_hw = QPushButton("添加作业")
        self.btn_import = QPushButton("导入CSV")
        self.btn_export = QPushButton("导出")
        for b in (self.btn_add_course, self.btn_add_hw, self.btn_import, self.btn_export):
            b.setMinimumHeight(32)
            top_bar.addWidget(b)
        top_bar.addStretch(1)
        self.btn_add_course.clicked.connect(self.on_add_course)
        self.btn_add_hw.clicked.connect(self.on_add_homework)
        self.btn_import.clicked.connect(self.on_import)
        self.btn_export.clicked.connect(self.on_export)

        # 左：课表
        left = QVBoxLayout()
        left.addWidget(QLabel("本周课表（双击编辑 / 右键删除）"))
        self.schedule_table = QTableWidget(12, 7)
        self.schedule_table.setHorizontalHeaderLabels(WEEKDAYS)
        self.schedule_table.setVerticalHeaderLabels([f"第{i + 1}节" for i in range(12)])
        self.schedule_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.schedule_table.cellDoubleClicked.connect(self.on_course_cell)
        left.addWidget(self.schedule_table)
        course_btns = QHBoxLayout()
        self.btn_edit_course = QPushButton("编辑选中课程")
        self.btn_del_course = QPushButton("删除选中课程")
        self.btn_edit_course.clicked.connect(self.on_edit_course_btn)
        self.btn_del_course.clicked.connect(self.on_del_course_btn)
        course_btns.addWidget(self.btn_edit_course)
        course_btns.addWidget(self.btn_del_course)
        left.addLayout(course_btns)

        # 中：作业列表
        middle = QVBoxLayout()
        middle.addWidget(QLabel("作业列表（按截止排序，双击编辑）"))
        self.homework_list = QListWidget()
        self.homework_list.itemDoubleClicked.connect(self.on_edit_homework)
        self.homework_list.currentItemChanged.connect(lambda *_: self.show_hw_detail())
        middle.addWidget(self.homework_list)
        hw_btns = QHBoxLayout()
        self.btn_done = QPushButton("标记完成/未完成")
        self.btn_del_hw = QPushButton("删除作业")
        self.btn_done.clicked.connect(self.on_toggle_done)
        self.btn_del_hw.clicked.connect(self.on_del_homework)
        hw_btns.addWidget(self.btn_done)
        hw_btns.addWidget(self.btn_del_hw)
        middle.addLayout(hw_btns)

        # 右：详情 + 日历
        right = QVBoxLayout()
        right.addWidget(QLabel("详情"))
        self.detail_label = QLabel("点击作业查看详情")
        self.detail_label.setWordWrap(True)
        self.detail_label.setMinimumHeight(150)
        right.addWidget(self.detail_label)
        right.addWidget(QLabel("日历"))
        self.calendar = QCalendarWidget()
        right.addWidget(self.calendar)

        body = QHBoxLayout()
        for layout, stretch in ((left, 3), (middle, 2), (right, 2)):
            w = QWidget()
            w.setLayout(layout)
            body.addWidget(w, stretch)

        root = QVBoxLayout()
        top = QWidget()
        top.setLayout(top_bar)
        center = QWidget()
        center.setLayout(body)
        root.addWidget(top)
        root.addWidget(center, 1)
        window = QWidget()
        window.setLayout(root)
        self.setCentralWidget(window)
        self._selected_course: Course | None = None
        # 状态栏：显示待办/紧急统计
        self.statusBar().showMessage("就绪")
        self.apply_style()
        # 提醒 Timer：每 60s 扫描一次
        self._warned_ids: set[str] = set()  # 已弹窗过的作业，避免重复打扰
        self.remind_timer = QTimer(self)
        self.remind_timer.setInterval(60_000)
        self.remind_timer.timeout.connect(self.check_reminders)
        self.remind_timer.start()
        # 启动即扫一次
        QTimer.singleShot(2000, self.check_reminders)

    def apply_style(self) -> None:
        qss = Path(__file__).with_name("style.qss")
        if qss.exists():
            self.setStyleSheet(qss.read_text(encoding="utf-8"))

    # ---------- 定时提醒 ----------
    def check_reminders(self, now: datetime | None = None) -> None:
        """每分钟调用：刷新颜色 + 状态栏统计 + <1h 作业弹窗（每个作业只弹一次）。"""
        self.store.load()
        result = reminder.scan(self.store.homeworks, now)
        self.refresh_homeworks()
        n_todo = len(result["urgent"]) + len(result["normal"]) + len(result["overdue"]) + len(result["popup"])
        self.statusBar().showMessage(
            f"待办 {n_todo}｜24h内 {len(result['urgent'])}｜已过期 {len(result['overdue'])}｜已完成 {len(result['done'])}"
        )
        fresh = [h for h in result["popup"] if h.id not in self._warned_ids]
        for h in fresh:
            self._warned_ids.add(h.id)
        if fresh:
            names = "\n".join(f"· [{h.course_name}] {h.title}（{h.deadline}）" for h in fresh[:5])
            QMessageBox.warning(self, "作业即将截止（<1h）", f"以下作业不足1小时截止：\n{names}")
        # 已完成/已删除的 id 移出记忆集合，防止无限增长
        alive = {h.id for h in self.store.homeworks}
        self._warned_ids &= alive

    # ---------- 刷新 ----------
    def refresh_all(self) -> None:
        self.store.load()
        self.refresh_schedule()
        self.refresh_homeworks()
        self.show_hw_detail()

    def refresh_schedule(self) -> None:
        self.schedule_table.clearContents()
        for c in self.store.courses:
            col = c.weekday - 1
            for sec in range(c.start_section, c.end_section + 1):
                row = sec - 1
                if 0 <= row < 12 and 0 <= col < 7:
                    item = QTableWidgetItem(f"{c.name}\n{c.location}")
                    item.setBackground(QBrush(QColor(c.color)))
                    item.setData(256, c.id)  # 存课程 id
                    self.schedule_table.setItem(row, col, item)

    def refresh_homeworks(self) -> None:
        self.homework_list.clear()
        now = datetime.now()
        for h in sorted(self.store.homeworks, key=lambda x: x.deadline):
            status = "✓" if h.done else "○"
            item = QListWidgetItem(f"{status} [{h.course_name}] {h.title} | {h.deadline}")
            item.setData(256, h.id)
            if not h.done:
                try:
                    delta = h.deadline_dt() - now
                    if delta.total_seconds() < 0:
                        item.setForeground(QBrush(QColor("#999999")))
                    elif delta.total_seconds() < 24 * 3600:
                        item.setForeground(QBrush(QColor("#D32F2F")))
                except ValueError:
                    pass
            self.homework_list.addItem(item)

    def show_hw_detail(self) -> None:
        item = self.homework_list.currentItem()
        if item is None:
            self.detail_label.setText("点击作业查看详情")
            return
        h = next((x for x in self.store.homeworks if x.id == item.data(256)), None)
        if h is None:
            return
        self.detail_label.setText(
            f"课程：{h.course_name}\n标题：{h.title}\n截止：{h.deadline}\n"
            f"状态：{'已完成' if h.done else '未完成'}\n备注：{h.remark}"
        )

    # ---------- 课程交互 ----------
    def on_add_course(self) -> None:
        dlg = CourseDialog(self, self.store)
        if dlg.exec() and dlg.result:
            self.store.add_course(dlg.result)
            self.refresh_all()

    def _course_from_table(self) -> Course | None:
        cell = self.schedule_table.currentItem()
        if cell is None:
            # 兜底：选第一门课
            return self.store.courses[0] if self.store.courses else None
        cid = cell.data(256)
        return self.store.get_course(cid)

    def on_course_cell(self, row: int, col: int) -> None:
        item = self.schedule_table.item(row, col)
        if item is None:
            self.on_add_course()
            return
        course = self.store.get_course(item.data(256))
        if course:
            self.edit_course(course)

    def on_edit_course_btn(self) -> None:
        c = self._course_from_table()
        if c is None:
            QMessageBox.information(self, "提示", "暂无课程，请先添加")
            return
        self.edit_course(c)

    def edit_course(self, course: Course) -> None:
        dlg = CourseDialog(self, self.store, course)
        if dlg.exec() and dlg.result:
            self.store.update_course(dlg.result)
            self.refresh_all()

    def on_del_course_btn(self) -> None:
        c = self._course_from_table()
        if c is None:
            return
        if QMessageBox.question(self, "确认", f"删除课程《{c.name}》？其作业也会一起删除。") != QMessageBox.Yes:
            return
        self.store.delete_course(c.id)
        self.refresh_all()

    # ---------- 作业交互 ----------
    def _current_hw(self) -> Homework | None:
        item = self.homework_list.currentItem()
        if item is None:
            return None
        return next((x for x in self.store.homeworks if x.id == item.data(256)), None)

    def on_add_homework(self) -> None:
        dlg = HomeworkDialog(self, self.store)
        if dlg.exec() and dlg.result:
            if dlg.result.course_id:
                c = self.store.get_course(dlg.result.course_id)
                if c:
                    dlg.result.course_name = c.name
            self.store.add_homework(dlg.result)
            self.refresh_all()

    def on_edit_homework(self) -> None:
        h = self._current_hw()
        if h is None:
            return
        dlg = HomeworkDialog(self, self.store, h)
        if dlg.exec() and dlg.result:
            if dlg.result.course_id:
                c = self.store.get_course(dlg.result.course_id)
                if c:
                    dlg.result.course_name = c.name
            self.store.update_homework(dlg.result)
            self.refresh_all()

    def on_toggle_done(self) -> None:
        h = self._current_hw()
        if h is None:
            return
        self.store.mark_done(h.id, not h.done)
        self.refresh_all()

    def on_del_homework(self) -> None:
        h = self._current_hw()
        if h is None:
            return
        self.store.delete_homework(h.id)
        self.refresh_all()

    # ---------- 导入导出 ----------
    def on_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "选择CSV文件", "", "CSV (*.csv)")
        if not path:
            return
        try:
            if "homework" in path.lower() or "作业" in path:
                ok, errs = self.store.import_homeworks_csv(path)
            else:
                ok, errs = self.store.import_courses_csv(path)
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, "导入失败", str(e))
            return
        msg = f"成功导入 {ok} 条"
        if errs:
            msg += "\n" + "\n".join(errs[:5])
        QMessageBox.information(self, "导入结果", msg)
        self.refresh_all()

    def on_export(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if not d:
            return
        from pathlib import Path as _P

        self.store.export_courses_csv(_P(d) / "courses.csv")
        self.store.export_homeworks_csv(_P(d) / "homeworks.csv")
        QMessageBox.information(self, "导出", "已导出 courses.csv / homeworks.csv")
