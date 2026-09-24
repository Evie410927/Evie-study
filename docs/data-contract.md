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
| `manualSimilarWordIds` | 用户手动维护的双向相近表达关系；对话上下文不得自动写入 |
| `hiddenSimilarWordIds` | 删除关系的持久记忆，防止旧迁移恢复 |
| `mastered` / `rating` | 学习状态和 0～5 星级 |
| `createdAt` / `updatedAt` | 创建及最后更新时间 |
| `fieldUpdatedAt` | 云同步逐字段冲突合并时间戳 |
| `userEditedAt` | 阻止内置样本覆盖用户修改 |
| `krMeaning` | 仅 JP 允许的韩文对应表达 |

## 持久化契约

- `saveData()` 返回失败时，界面不得报告成功或关闭编辑上下文。
- localStorage 不可用时使用 IndexedDB 持久化降级；内存回退不能冒充持久化成功。
- 内置样本升级必须按稳定 ID 合并，不得复活已删除词或覆盖用户编辑。
- KR 与 JP 使用隔离的存储键和云端 `language` 值。
- `autoSimilarWordIds` 在装载时统一清空，展示层只读取人工双向关系。

## 云同步契约

- 以 `(user_id, language, word_id)` 为唯一键。
- `__sync_meta__` 仅承载整库版本元数据，不得渲染为卡片。
- 删除使用带时间戳的墓碑传播。
- 云端版本变化时先无损合并，再上传仍属于本机的待处理字段。
- 只下载模式可以覆盖本机数据，但必须先向用户明确提示不可逆影响。
