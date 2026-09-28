# 变更影响分析：列表卡片独立发音备注

## 问题与完成标准

- 问题：上一版错误地把红色读音右侧入口绑定到 `userNote`，导致标题发音备注与下方 `【…】` 内容说明串字段。
- 交互缺陷：已有发音备注在 `pointerdown` 阶段立即隐藏，原生 `click` 可能因目标消失而落到整张卡片，误开详情弹窗。
- 布局缺陷：黄色发音备注曾被固定限制为 112/132px，右侧尚有空间时也会过早省略。
- 用户可观察结果：列表卡片与详情弹窗顶部的红色读音右侧均提供同一套发音备注组件；下方 `【…】` 内容说明保持原样。点击 `＋` 后在标题同一排出现空白输入框用于追加，点击已有发音备注则回填全文并直接修改，末尾 `×` 只删除发音备注，两处实时同步；非编辑状态的黄色备注可一直使用到右侧学习状态/星级操作区左边，仅在实际空间不足时省略；JP 列表保留专属韩文对应 Badge，备注延伸到该 Badge 左侧。
- 明确不在范围内：不改变 `userNote` 的完整编辑器及详情、复习、相近表达展示；不改变主搜索范围。
- 完成标准：KR/JP 双端列表和详情标题均可新建、追加、回填修改与删除同一 `pronunciationNote` 并实时同步，`userNote` 在本地重载、导入导出和云同步中始终不受影响；列表中明确点击黄色备注或其 `×` 时详情弹窗保持关闭，点击卡片其他区域仍正常打开详情；详情中操作时弹窗保持打开。

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

- 新增或更新的测试：两字段隔离、列表与详情标题组件对称、15px 控件紧邻读音、`＋` 输入框同排且初始空白、点击已有文字回填全文并替换保存、黄色备注无固定像素上限且长内容可扩展到 KR 右侧状态区或 JP 专属韩文 Badge 前、双视图实时同步、详情弹窗保持打开、pointerdown 不改变 DOM、click 后列表详情保持关闭、卡片其他区域仍打开详情、空失焦保留、Enter/失焦保存、Escape 取消、`×` 只删除发音备注、事件隔离、本地持久化与 `fieldUpdatedAt.pronunciationNote` 云同步追踪。
- 必须运行的质量门禁：`python scripts/run_quality_gate.py`
- 部署后验证：确认 GitHub Pages KR/JP 均包含 `startWordCardPronunciationNoteEdit`、`saveWordCardPronunciationNote` 与 `deleteWordCardPronunciationNote`，并保留独立 `renderUserNoteHtml`。
