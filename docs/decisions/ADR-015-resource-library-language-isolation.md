# ADR-015：学习资料库按语言隔离

- 状态：Accepted
- 日期：2026-10-20

## 背景

KR 与 JP 页面曾共用同一个资料 IndexedDB 列表，云端 `resource_files` 也没有语言字段，导致在 JP 上传的资料会出现在 KR。用户预期两个单词本的学习资料互相独立，同时仍需保留同账号跨设备同步和手动排序。

## 决策

1. KR 与 JP 继续使用同一物理 IndexedDB `evie_vocab_resource_library_v1`，但 `files` 与 `deletions` 的每条记录必须包含 `language`，页面只读取当前语言分区。
2. IndexedDB 升级到 v3，并为两个 store 建立非唯一 `language` 索引。旧版无语言记录统一迁移为 `jp`，因为本次发现的存量资料明确来自 JP；迁移后 KR 不得显示这些记录。
3. 新增资料、删除墓碑、远端元数据、排序写入和下载缓存都必须携带当前页面语言。任何合并逻辑都只能在同一语言分区内比较 ID、时间戳与顺序。
4. `resource_files` 增加非空 `language`，限定为 `kr` 或 `jp`，唯一键改为 `(user_id, language, resource_id)`；旧云端行统一迁移为 `jp`。所有读取必须同时按登录用户 RLS 与当前语言过滤。
5. 新 Storage 对象路径使用 `user_id/language/resource_id/resource_id.extension`。旧 JP 对象保留原路径并由迁移后的元数据继续引用，不执行破坏性搬移。
6. 若云端尚未执行语言字段迁移，前端必须明确提示先升级 `supabase_vocab_sync.sql` 并中止资料同步，不得回退为读取全部语言。排序列缺失仍可按 ADR-014 单独回退。
7. 资料顺序只在当前语言内部持久化和同步；KR 与 JP 不再共享列表或排序。

## 验证

- 静态契约检查双端语言常量、IndexedDB v3、当前语言过滤、云端语言查询、三字段冲突键及分语言 Storage 路径。
- Selenium 向 IndexedDB 注入另一语言记录与旧版无语言记录，确认 KR 隐藏两者、JP 只接收迁移后的旧记录，并确认新上传资料写入当前语言。
- SQL 静态检查 `language` 约束、旧行迁移、复合主键和按语言索引。
