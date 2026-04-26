# NoteRx 本地记忆（MEMORY）

本文件为**长期说明区**，可随意增删改；诊断流水按日写在 `memory/YYYY-MM-DD.md`，完整 JSON 在 `memory/records/`。

## 用途

- 人类可读：`grep`、编辑器、版本管理（若你愿意把本目录纳入 git）均可。
- 完整数据仍以 `memory/records/<id>.json` 与 SQLite `diagnosis_history` 双写；数据库便于列表检索，文件便于备份与恢复。

## 提示

- 删除某条历史时，对应 `records` 下的 JSON 会一并删除；当日志 md 中仍保留摘要行，便于审计。
