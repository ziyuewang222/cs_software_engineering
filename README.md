# cs_software_engineering · 课程作业管理系统（PySide6 GUI）

课程作业管理桌面应用：三栏界面管理课表与作业，JSON 本地持久化，定时扫描截止提醒，支持 CSV 导入导出。

## 功能

- **本周课表（左栏）**：12 节 × 周一~周日表格渲染，添加 / 双击编辑 / 删除课程（含地点、老师、颜色）。
- **作业列表（中栏）**：按截止时间自动排序，标记完成/未完成，双击编辑，删除。
- **详情 + 日历（右栏）**：点击作业显示课程、标题、截止、状态、备注；日历辅助查看日期。
- **定时提醒**：每 60 秒扫描一次，状态栏显示 `待办 / 24h内 / 已过期 / 已完成` 统计；24 小时内标红，过期置灰，不足 1 小时弹窗（每个作业只弹一次）。
- **持久化**：所有数据存 `course_gui/data.json`，启动自动加载，增删改自动保存。
- **导入导出**：CSV 导入课程/作业（按文件名是否含 `homework`/`作业` 自动区分），一键导出 `courses.csv` / `homeworks.csv`。
- **QSS 美化**：`course_gui/style.qss` 统一按钮、表格、列表样式。

## 目录结构

```
course_gui/
  main.py        程序入口
  main_window.py 三栏主窗口 + 提醒 Timer + 导入导出交互
  models.py      Course / Homework 数据模型与校验
  storage.py     DataStore：data.json 读写、CRUD、CSV 导入导出
  dialogs.py     添加/编辑课程与作业的对话框
  reminder.py    截止提醒扫描（classify/scan 纯函数）
  style.qss      界面样式
  data.json      本地数据文件
  requirements.txt
```

数据格式：`deadline` 为 `YYYY-MM-DD HH:MM`（如 `2026-10-10 23:59`）。

## 用法

### 1. 环境要求

- Python 3.10+
- 依赖只有 `PySide6>=6.6`

### 2. 安装运行

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r course_gui/requirements.txt
python -m course_gui.main
```

### 3. 日常使用

- 顶部工具栏：`添加课程` / `添加作业` / `导入CSV` / `导出`。
- 课表双击空白格可直接新建该位置课程；双击已有格编辑。
- 作业按截止排序：红色 = 24h 内截止，灰色 = 已过期，`✓` = 已完成。
- 导入 CSV：
  - 课程列：`课程名,星期,开始节,结束节,地点,老师`
  - 作业列：`课程名,标题,截止时间,备注`
- 导出：选择目录后生成 `courses.csv` / `homeworks.csv`。

### 4. 数据存储自测（可选）

```bash
python -m course_gui.storage
# 输出"存储自测通过"即 CRUD + JSON持久化 + 排序正常
```

