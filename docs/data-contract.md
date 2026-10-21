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
| `pronunciationNote` | 发音或个人记忆方式备注；列表卡片与详情弹窗均在标题下方、词性与释义上方的独立整宽第二行展示红色读音、`＋` 和黄色备注，完整新增/编辑词条弹窗在读音字段之后提供独立输入字段。点击 `＋` 打开同排空白输入框并追加，点击已有备注文字或打开完整编辑弹窗则回填全文进行替换编辑，末尾 `×` 删除；任一处修改后双视图立即同步；总长度最大 500 字符；非空时 `tags` 必须自动包含 `发音` |
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
- 云同步改变词库及云端基线时，必须等待至少一层持久化介质确认保存包含两者的一致快照后才报告成功；不得先持久化词库、再异步更新基线并提前结束同步。
- 对没有有效内容指纹保存时间的历史状态，若 IndexedDB 在排除本地删除墓碑后是 localStorage 的严格超集且不存在本地独有词条，必须先恢复 IndexedDB，再比较可能已被旧版本单独提前写入的云端基线。
- 内置样本升级必须按稳定 ID 合并，不得复活已删除词或覆盖用户编辑。
- KR 与 JP 使用隔离的存储键和云端 `language` 值。
- `autoSimilarWordIds` 在装载时统一清空，展示层只读取人工双向关系。
- 详情或复习视图拖动相近表达卡片只重排当前源词条的 `manualSimilarWordIds`，不得连带覆盖反向词条各自的顺序；新增/编辑词条弹窗中的整卡拖动先只重排 `editingModalSimilarWordIds`，不更新时间、不写本地存储也不进入云同步，点击保存词条后才按该草稿顺序写入当前源词条；关闭弹窗则丢弃草稿排序。新增关系追加到当前草稿或正式顺序末尾。
- 列表卡片或详情弹窗对 `pronunciationNote` 的原位新增、全文替换和删除必须更新 `userEditedAt`、`updatedAt` 与 `fieldUpdatedAt.pronunciationNote`，持久化失败时不得显示成功反馈；点击已有备注编辑时必须回填当前全文，点击 `＋` 时仍保持空白；保存后同步刷新列表标题组件与详情独立发音行；该流程不得修改 `userNote` 或刷新其内容。
- 完整新增/编辑词条弹窗必须以 `inputPronunciationNote` 独立维护 `pronunciationNote`：字段排列在 `reading` 后、`meaning` 前，新建时为空，编辑时回填当前全文，保存时原样替换（允许用户清空）；非空输入必须在同一次 `input` 事件中把 `发音` 去重加入 `editingModalTags` 并立即刷新下方标签草稿，但正式保存前不得改写词库、持久化存储或云同步待办；不得以默认空字符串覆盖未显示或未读取的既有值，也不得读写 `userNote`。
- 新增或修改为非空 `pronunciationNote` 时，必须在同一持久化事务中向自定义 `tags` 去重加入 `发音`，同步更新时间与 `fieldUpdatedAt.tags`，并立即刷新列表、详情及复习 Tag 视图。装载旧本地数据、IndexedDB 备用快照、导入数据或云端合并结果时须对所有非空发音备注执行同样的全量补齐；删除发音备注不自动移除 `发音` Tag。

## 云同步契约

- 以 `(user_id, language, word_id)` 为唯一键。
- `__sync_meta__` 仅承载整库版本元数据，不得渲染为卡片。
- 删除使用带时间戳的墓碑传播。
- 云端版本变化时先无损合并，再上传仍属于本机的待处理字段。
- 只下载模式可以覆盖本机数据，但必须先向用户明确提示不可逆影响。
- 每次词库同步必须在写入本地或云端前，将本地完整词库、待上传字段、删除墓碑、基线与刚读取的云端完整行、revision 共同保存为同步前 IndexedDB 快照；只同步学习资料时不得创建词库快照。
- 同步撤销历史使用与当前耐久快照隔离的键，最多保留最近 5 份，不得进入 localStorage、词库导出、`vocab_items` 或资料库。历史写入失败时必须中止词库同步。
- 只恢复本地必须原样恢复快照中的词库、待上传字段、删除墓碑和基线；恢复本地与云端必须把两侧分别恢复到各自的同步前状态，为快照外当前云端词写删除墓碑，并创建高于当前云端 revision 的新 revision。任何恢复失败都必须保留所选快照。

## 学习资料库契约

- 资料文件不属于单词数据，不得添加到 `this.words`、词库 localStorage 快照、JSON/HTML 词库导出或 `vocab_items` payload。
- KR/JP 同源页面共用物理 IndexedDB `evie_vocab_resource_library_v1`，但按 `language=kr|jp` 逻辑分区；`files` store 的每条记录至少包含稳定 `id`、`language`、原始 `name`、可信白名单内的 `type`、`size`、`addedAt`、`updatedAt`、`sha256`、`storagePath`、`cloudState` 与可空原始 `blob`，`deletions` store 的墓碑也必须包含 `language`。页面只可读取当前语言；旧版无语言记录统一迁移为 `jp`。
- 允许 PDF、Word、Excel、CSV、纯文本及常见位图格式；拒绝不在白名单内的可执行或网页类文件。单文件大小上限为 50 MiB，支持一次选择多个文件。
- 只有 IndexedDB 事务完成后才能提示上传成功；失败时保留弹窗上下文并展示明确错误，不得以内存缓存冒充持久化成功。
- 删除必须经过用户确认并等待 IndexedDB 删除事务完成；文件列表随后重新读取并更新空状态。
- PNG、JPEG、WebP 等常见位图必须在当前单词本页面的 `#resourceImagePreviewModal` 中预览，右上角 `×` 关闭后恢复资料列表且不得新开标签页；PDF、文本继续使用浏览器原生能力，Office 文件以原始 Blob 打开，浏览器无法内联显示时允许下载后由系统应用查看。
- 云端二进制文件只保存在私有 Storage bucket `vocab-resources`，新对象路径固定为 `user_id/language/resource_id/resource_id.extension`；`resource_files` 表只保存元数据与墓碑，以 `(user_id, language, resource_id)` 唯一标识资料。Storage 和元数据表都必须启用 RLS，并仅允许已登录用户访问自己的目录或行；所有元数据读取还必须按当前语言过滤。旧云端无语言行统一迁移为 `jp` 并保留原对象路径。
- 新增文件先作为 `cloudState=pending` 持久化到 IndexedDB；点击云同步并勾选“同步学习资料”后才上传。已有旧版本地文件在装载时迁移为待上传，不得静默丢弃。
- 云端列表同步只下载元数据；远端独有文件的 `blob` 保持为空，点击打开或下载时再使用当前有效登录令牌获取 Blob，成功后写入 IndexedDB 作为离线缓存。
- 删除先写本地 `deletions` 墓碑，再向 `resource_files` Upsert `deleted_at`；只有墓碑写入成功后才调用 Storage API 删除对象。其他设备读到更新的墓碑时必须删除本地缓存并保留删除记忆，防止旧数据复活。
- 上传必须展示文件级进度、对瞬时失败进行有限重试，并在失败后保留本地 Blob 与待上传状态。元数据成功写入后才可把 `cloudState` 改为 `synced`。
- 每条资料额外保存数值型 `sortOrder`、排序更新时间 `orderUpdatedAt` 和仅本地使用的 `orderDirty`。当前语言列表严格按 `sortOrder` 升序展示；历史记录缺少排序字段时，按原有新增时间倒序生成稳定顺序并标记待同步。
- 鼠标拖动、触屏拖动或键盘移动完成后，必须在同一个 IndexedDB 事务中重写当前语言全部可见资料的连续 `sortOrder` 和同一 `orderUpdatedAt`；事务失败时恢复原顺序并禁止提示成功，另一语言记录不得被改写。
- 排序版本与文件内容 `updatedAt` 独立。云端元数据使用 `sort_order` 与 `order_updated_at`，逐条采用较新的排序时间，纯排序不得重新上传 Blob。旧云表缺少排序列时继续使用旧元数据协议，本地顺序和 `orderDirty` 必须保留到未来成功同步。

## Excel 导出契约

- 导出是只读快照操作，只读取当前 `this.words`，不得更新时间戳、写入 localStorage/IndexedDB、改变筛选状态或创建云同步待办。
- 范围固定为全部、`mastered=false` 的学习中、`mastered=true` 的已掌握、自定义 Tag 多选，以及星级多选。Tag 比较须去除可选的 `#`、清理首尾空白并忽略大小写；星级须归一化为 0～5 的整数后精确匹配。两种多选均采用 OR，命中任一所选项即导出。
- `.xlsx` 工作表提供八个可勾选列：`word`、`partOfSpeech`、释义、第一组例句、`reading`、`pronunciationNote`、`userNote` 和相近词汇。前四列默认勾选，后四列默认不勾选；用户可取消任一默认列或追加任一其他列，但至少保留一列。最终列按上述固定相对顺序输出。KR 释义为 `meaning`；JP 为 `meaning` 与非空 `krMeaning` 以换行连接。
- 第一组例句使用统一例句归一化方法取得第一条现存记录，只输出原句与非空中文翻译并以换行连接；不得输出第二条及后续例句。所有值必须经过 XML 非法字符清理和实体转义。
- 相近词汇列只解析当前词条按人工顺序保存且未隐藏的 `manualSimilarWordIds`。每个有效关联词只生成一行 `word：meaning`，多个关联词以换行连接；JP 不追加 `krMeaning`。不得输出关联词的 `reading`、`pronunciationNote`、`userNote`、`partOfSpeech`、Tag、例句、星级、学习状态或其他字段。
- 空词库、未选择 Tag、未选择星级、未选择任何导出列或筛选结果为空时必须阻止下载并显示原因；成功提示必须包含实际导出词条数量。
- `#excelExportChooseLocation` 开启时，支持 File System Access API 的浏览器必须使用 `showSaveFilePicker` 和可写文件句柄保存；用户取消时不得触发后备下载。API 不支持时使用浏览器默认下载机制，并在成功提示中明确说明无法自定义位置。
