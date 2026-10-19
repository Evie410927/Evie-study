# ADR-012：学习资料私有云同步

- 状态：Accepted
- 日期：2026-10-14

## 背景

ADR-011 已提供 IndexedDB 本地资料库。用户进一步要求资料在登录同一云同步账号的设备间可见，同时不能把大体积 Blob 混入词条 JSON、破坏现有 `vocab_items` 版本协议或在页面启动时消耗大量流量。

## 决策

1. 二进制文件存入私有 Supabase Storage bucket `vocab-resources`，元数据存入独立 `resource_files` 表；两者按 `user_id` 目录或行启用 RLS。前端继续只暴露 publishable key 与用户 access token，绝不使用 service role。
2. 资料库跨 KR/JP 共享，不增加语言列。对象路径固定为 `user_id/resource_id/resource_id.extension`，避免原始文件名中的特殊字符影响 Storage key；原始名称仅存元数据。
3. IndexedDB 升级为版本 2：`files` 保存可空 Blob、SHA-256、Storage 路径和云状态，`deletions` 保存待传播墓碑。旧版记录在装载时自动补齐 `updatedAt` 并标记 `pending`。
4. 云朵方向选择弹窗增加独立的“同步学习资料”选项。资料同步可单独执行，也可与词库上传/下载同时执行；未勾选时不得隐式上传附件。
5. 新增文件先落盘并进入待上传队列。上传使用浏览器原生二进制请求，显示文件级进度并对瞬时失败有限重试；Storage 成功后先保存对象路径，再 Upsert 元数据，二者完成后才能标记 `synced`。失败保留本地 Blob 和 `pending` 状态。
6. 云端同步首先拉取元数据。远端独有资料只创建无 Blob 的本地元数据卡片；用户打开或下载时才从私有 Storage 获取 Blob，并在成功后写入 IndexedDB 离线缓存。
7. 删除先在 IndexedDB 写入墓碑并移除可见记录。云同步时先 Upsert `resource_files.deleted_at`，成功后再通过 Storage API 删除对象；其他设备读到墓碑时删除本地缓存并保留删除记忆。
8. 同一 `resource_id` 以最新 `updated_at` 决定元数据版本；本机 `pending` 修改不得被较旧远端记录覆盖。文件内容使用 SHA-256（Web Crypto 可用时）辅助验证和去重，但稳定 ID 仍是主键。
9. 图片点击后在当前页面的独立预览层显示，不再新建浏览器页面。预览层保留资料库作为下层上下文，右上角 `×`、遮罩点击或 Escape 只关闭图片预览并回到资料列表；关闭时立即释放专用 Blob URL。PDF、文本和 Office 文件继续沿用浏览器原生打开或下载路径。
10. 资料文件的人工展示顺序由 ADR-014 单独约束；排序元数据与 Blob 内容版本分离，避免仅调整顺序时重复上传文件。

## 验证

- SQL 静态断言覆盖私有 bucket、元数据表、复合主键、RLS、授权和四类 Storage 策略。
- 双端静态测试覆盖云同步选项、IndexedDB v2 迁移、待上传、进度/重试、按需下载、页内图片预览、墓碑顺序和词条 payload 隔离。
- Selenium 使用隔离的假 Supabase 接口验证上传、元数据合并、远端占位卡片、点击下载缓存、跨设备删除传播与失败保留待办。
