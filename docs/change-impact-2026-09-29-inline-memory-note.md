# 变更影响分析：列表卡片独立发音备注

## 问题与完成标准

- 问题：上一版错误地把红色读音右侧入口绑定到 `userNote`，导致标题发音备注与下方 `【…】` 内容说明串字段。
- 用户可观察结果：红色读音右侧的 `＋` 只维护独立发音备注；下方 `【…】` 内容说明保持原样。点击 `＋` 后在标题同一排出现空白输入框用于追加，点击已有发音备注则回填全文并直接修改，末尾 `×` 只删除发音备注。
- 明确不在范围内：不改变 `userNote` 的完整编辑器及详情、复习、相近表达展示；不改变主搜索范围。
- 完成标准：KR/JP 双端的 `pronunciationNote` 与 `userNote` 在新增、追加、回填修改、删除、本地重载、导入导出和云同步中始终互不影响。

## 影响范围

- [x] KR 应用
- [x] JP 应用
- [x] 数据字段或缓存迁移（新增可选 `pronunciationNote`，旧数据默认空，不从 `userNote` 迁移）
- [x] localStorage / IndexedDB
- [x] 云端 payload / RLS / 版本协议（JSON payload 新增 `pronunciationNote` 逐字段同步）
- [x] 列表 / 详情 / 复习 / 相近表达
- [x] 移动端与空状态
- [x] 现有规则或 ADR

## 风险与回滚

- 数据兼容风险：旧数据没有 `pronunciationNote` 时按空值处理；绝不把既有 `userNote` 猜测迁移为发音备注。
- 并发或跨设备风险：`pronunciationNote` 与 `userNote` 分别按自己的字段更新时间参与云端冲突合并。
- 安全与隐私风险：输入继续经过 HTML 转义；不写入页面属性或执行脚本。
- 回滚方法：移除列表卡片 `＋`、原位输入和 `×` 控件，保留 `pronunciationNote` 数据、`userNote` 数据及完整编辑弹窗入口。

## 验证计划

- 新增或更新的测试：两字段隔离、15px 控件紧邻读音、`＋` 输入框同排且初始空白、点击已有文字回填全文并替换保存、空失焦保留、Enter/失焦保存、Escape 取消、`×` 只删除发音备注、事件隔离、本地持久化与 `fieldUpdatedAt.pronunciationNote` 云同步追踪。
- 必须运行的质量门禁：`python scripts/run_quality_gate.py`
- 部署后验证：确认 GitHub Pages KR/JP 均包含 `startWordCardPronunciationNoteEdit`、`saveWordCardPronunciationNote` 与 `deleteWordCardPronunciationNote`，并保留独立 `renderUserNoteHtml`。
