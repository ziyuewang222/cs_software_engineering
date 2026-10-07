"""课程 / 作业新增与编辑对话框：所有修改走 GUI，不用手改 JSON。"""
from __future__ import annotations
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
)

from .models import Course, Homework
from .storage import DataStore


class CourseDialog(QDialog):
    def __init__(self, parent, store: DataStore, course: Course | None = None):
        super().__init__(parent)
        self.setWindowTitle("编辑课程" if course else "添加课程")
        self._course = course
        self.name_edit = QLineEdit(course.name if course else "")
        self.weekday_spin = QSpinBox()
        self.weekday_spin.setRange(1, 7)
        self.weekday_spin.setValue(course.weekday if course else 1)
        self.start_spin = QSpinBox()
        self.start_spin.setRange(1, 12)
        self.start_spin.setValue(course.start_section if course else 1)
        self.end_spin = QSpinBox()
        self.end_spin.setRange(1, 12)
        self.end_spin.setValue(course.end_section if course else 2)
        self.loc_edit = QLineEdit(course.location if course else "")
        self.teacher_edit = QLineEdit(course.teacher if course else "")
        form = QFormLayout()
        form.addRow("课程名*", self.name_edit)
        form.addRow("星期(1-7)*", self.weekday_spin)
        form.addRow("开始节*", self.start_spin)
        form.addRow("结束节*", self.end_spin)
        form.addRow("地点", self.loc_edit)
        form.addRow("老师", self.teacher_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.result: Course | None = None

    def _on_ok(self):
        try:
            c = self._course or Course()
            c.name = self.name_edit.text().strip()
            c.weekday = self.weekday_spin.value()
            c.start_section = self.start_spin.value()
            c.end_section = self.end_spin.value()
            c.location = self.loc_edit.text().strip()
            c.teacher = self.teacher_edit.text().strip()
            c.validate()
        except ValueError as e:
            QMessageBox.warning(self, "输入有误", str(e))
            return
        self.result = c
        self.accept()


class HomeworkDialog(QDialog):
    def __init__(self, parent, store: DataStore, hw: Homework | None = None):
        super().__init__(parent)
        self.setWindowTitle("编辑作业" if hw else "添加作业")
        self._hw = hw
        self.course_combo = QComboBox()
        self.course_combo.addItem("(无关联课程)", "")
        for c in store.courses:
            self.course_combo.addItem(c.name, c.id)
        if hw and hw.course_id:
            idx = self.course_combo.findData(hw.course_id)
            if idx >= 0:
                self.course_combo.setCurrentIndex(idx)
        self.title_edit = QLineEdit(hw.title if hw else "")
        self.deadline_edit = QLineEdit(hw.deadline if hw else "2026-10-10 23:59")
        self.deadline_edit.setPlaceholderText("YYYY-MM-DD HH:MM")
        self.done_check = QCheckBox("已完成")
        if hw:
            self.done_check.setChecked(hw.done)
        self.remark_edit = QLineEdit(hw.remark if hw else "")
        form = QFormLayout()
        form.addRow("所属课程", self.course_combo)
        form.addRow("标题*", self.title_edit)
        form.addRow("截止时间*", self.deadline_edit)
        form.addRow("状态", self.done_check)
        form.addRow("备注", self.remark_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.result: Homework | None = None
        self._store = store

    def _on_ok(self):
        try:
            h = self._hw or Homework()
            h.course_id = self.course_combo.currentData()
            h.course_name = self.course_combo.currentText() if h.course_id else ""
            h.title = self.title_edit.text().strip()
            h.deadline = self.deadline_edit.text().strip()
            h.done = self.done_check.isChecked()
            h.remark = self.remark_edit.text().strip()
            h.validate()
        except ValueError as e:
            QMessageBox.warning(self, "输入有误", str(e))
            return
        self.result = h
        self.accept()
