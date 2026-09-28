# 单词数据契约

## 核心字段

| 字段 | 约束 |
|---|---|
| `id` | 字符串稳定标识；改词名不能生成重复卡片 |
| `word` | 必填的词或表达正文 |
| `reading` | 仅存放规范读音；不得混入释义 |
| `partOfSpeech` | 独立词性字段；不得重复写入自定义 Tag |
| `meaning` | 纯净释义；不得包含读音或占位翻译 |
| `examples` | `{example, trans}` 数组；两列必须成对出现。AI 新建词条初始至少三组，用户可随后删除至零组 |
| `example` / `exampleTrans` | 与 `examples` 同步的兼容字段 |
| `tags` | 用户管理的自定义标签数组 |
| `userNote` | 单词内容解释备注；以卡片下方 `【…】` 形式展示，通过完整词条编辑器维护；与标题行发音备注完全独立 |
| `pronunciationNote` | 发音或个人记忆方式备注；列表卡片与详情弹窗标题均在读音右侧展示同一字段。点击 `＋` 打开同排空白输入框并追加，点击已有备注文字则回填全文进行替换编辑，末尾 `×` 删除；任一处修改后双视图立即同步；总长度最大 500 字符 |
| `manualSimilarWordIds` | 用户手动维护的双向相近表达关系；数组顺序是当前源词条的自定义展示顺序；对话上下文不得自动写入 |
| `hiddenSimilarWordIds` | 删除关系的持久记忆，防止旧迁移恢复 |
| `mastered` / `rating` | 学习状态和 0～5 星级 |
| `createdAt` / `updatedAt` | 创建及最后更新时间 |
| `fieldUpdatedAt` | 云同步逐字段冲突合并时间戳 |
| `userEditedAt` | 阻止内置样本覆盖用户修改 |
| `krMeaning` | 仅 JP 允许的韩文对应表达 |

## 持久化契约

- `saveData()` 返回失败时，界面不得报告成功或关闭编辑上下文。
- localStorage 不可用时使用 IndexedDB 持久化降级；内存回退不能冒充持久化成功。
- 启动时同时检查 localStorage 与 IndexedDB。通过受内容指纹保护的保存时间、云端基线、数据更新时间及词条集合判定新旧，恢复较新的有效快照；不得仅因 localStorage 非空就跳过 IndexedDB。
- 内置样本升级必须按稳定 ID 合并，不得复活已删除词或覆盖用户编辑。
- KR 与 JP 使用隔离的存储键和云端 `language` 值。
- `autoSimilarWordIds` 在装载时统一清空，展示层只读取人工双向关系。
- 拖动相近表达卡片只重排当前源词条的 `manualSimilarWordIds`，不得连带覆盖反向词条各自的顺序；新增关系追加到当前顺序末尾。
- 列表卡片或详情弹窗对 `pronunciationNote` 的原位新增、全文替换和删除必须更新 `userEditedAt`、`updatedAt` 与 `fieldUpdatedAt.pronunciationNote`，持久化失败时不得显示成功反馈；点击已有备注编辑时必须回填当前全文，点击 `＋` 时仍保持空白；保存后同步刷新列表和详情标题组件；该流程不得修改 `userNote` 或刷新其内容。

## 云同步契约

- 以 `(user_id, language, word_id)` 为唯一键。
- `__sync_meta__` 仅承载整库版本元数据，不得渲染为卡片。
- 删除使用带时间戳的墓碑传播。
- 云端版本变化时先无损合并，再上传仍属于本机的待处理字段。
- 只下载模式可以覆盖本机数据，但必须先向用户明确提示不可逆影响。
