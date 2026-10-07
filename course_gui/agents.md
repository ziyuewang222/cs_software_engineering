# Course GUI - Agents 进度记录

> 本文件负责记录 Agent 工作进度，每完成一步追加更新。

## 项目简介
课程作业管理 GUI 程序：管理课程和作业，展示课表，提醒作业截止时间。
技术选型：PySide6 + JSON 本地持久化 + 手动录入 + CSV 导入。提醒仅在程序运行时生效。

## 进度
- [x] 步骤 1：数据层（models.py + storage.py），JSON 增删改查 + CSV 导入导出 + 自测通过
- [x] 步骤 2：主界面框架（main_window.py + main.py），三栏空壳可运行，offscreen 自测 7列x12行通过
- [x] 步骤 3：课表 + 作业列表真实渲染 + GUI 全交互（dialogs.py 新增/编辑弹窗，增删改查走界面自动写回 data.json，自测通过）
- [x] 步骤 4：定时提醒 + CSV 导入导出接 UI + 美化（QSS）——全部完成

## 步骤 4 交付物
- `course_gui/reminder.py`（新建）：纯函数提醒逻辑——`classify(hw)` 按 done/overdue/popup(<1h)/urgent(<24h)/normal 分级，`scan(hws)` 分组；popup 作业同时进 urgent 组（既标红又弹窗）
- `course_gui/main_window.py`（增量）：QTimer 每 60s 触发 `check_reminders()`，启动 2s 后先扫一次；状态栏实时显示 `待办 N｜24h内 N｜已过期 N｜已完成 N`；`<1h` 作业 QMessageBox 弹窗，每个作业只弹一次（`_warned_ids` 去重，完成/删除后自动清理）；提醒阈值常量收敛到 reminder.WARN_HOURS / POPUP_HOURS
- `course_gui/style.qss`（新建）：浅色圆角主题——按钮蓝底白字+hover 加深，表格/列表白底圆角边框，选中行浅蓝底，表头浅灰蓝；`apply_style()` 启动自动加载，QSS 缺失则静默回退默认样式
- 自测：提醒分级单测（30min→popup+urgent，5h→urgent，3天→normal，-2h→overdue，已完成→done）全绿；窗口 offscreen 自测（Timer 间隔 60000ms + QSS 非空 + 状态栏统计刷新）全绿
- 运行验证：`python -m course_gui.main`，窗口带美化样式；添加一个截止=现在+30分钟的作业，2 秒内应弹窗一次，作业行标红
- 注意：提醒仅程序运行时生效（QTimer），关闭程序即停止，符合需求

## 步骤 3 交付物
- `course_gui/dialogs.py`：CourseDialog / HomeworkDialog，表单校验，错误弹窗提示
- `course_gui/main_window.py`：重写为交互版——课表按 weekday/节次渲染色块（双击空白新建/双击课程编辑），作业按截止排序（<24h标红/过期置灰/✓已完成），右侧详情联动，顶部导入/导出接 DataStore
- 交互清单：添加课程/编辑/删除（含级联删作业）、添加作业/双击编辑/标记完成/删除，全部自动 save()，无需手改 JSON
- 自测：offscreen 渲染断言（课表 cell 含课程名 + 作业数==1）全绿

## 步骤 1 交付物
- `course_gui/models.py`：Course / Homework 数据类
- `course_gui/storage.py`：DataStore，负责 data.json 读写、CSV 导入导出
- `course_gui/data.json`：本地数据文件（自动创建）
- `course_gui/requirements.txt`：依赖声明
- 自测：`python -m course_gui.storage` 全绿
