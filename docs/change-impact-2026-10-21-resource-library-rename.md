# 学习资料文件重命名变更影响分析

## 问题与完成标准

- 问题：资料卡片目前只能打开、下载、删除和排序，上传后无法修正文件名。
- 用户可观察结果：下载按钮左侧新增重命名图标；页内弹窗修改主名称并固定保留扩展名，成功后列表和下载文件名立即更新。
- 明确不在范围内：不修改文件二进制内容、格式、大小、哈希、稳定 ID 或 Storage 对象路径；不提供扩展名修改。
- 完成标准：KR/JP 镜像一致；空名、非法字符、尾部句点或空格与当前语言重名被拦截；IndexedDB 成功后才更新；云同步只传播元数据且不重新上传 Blob；完整质量门禁通过。

## 影响范围

- [x] KR 应用
- [x] JP 应用
- [x] 数据字段或缓存迁移
- [x] localStorage / IndexedDB
- [x] 云端 payload / RLS / 版本协议
- [ ] 列表 / 详情 / 复习 / 相近表达
- [x] 移动端与空状态
- [x] 现有规则或 ADR

## 风险与回滚

- 数据兼容风险：旧 IndexedDB 记录没有 `metadataDirty`；装载时补为 `cloudState !== synced`，已同步记录补为 `false`。
- 并发或跨设备风险：名称继续使用 `updatedAt/resource_files.updated_at` 最新者获胜；稳定 ID 和对象路径不变，其他设备同步目录后获得新名称。
- 安全与隐私风险：文件名仍属于账号私有元数据；输入拒绝常见文件系统非法字符与控制字符，不注入 HTML。
- 回滚方法：移除重命名 UI 和方法并停止生成 `metadataDirty`；旧记录中的额外布尔字段可被旧代码安全忽略，已修改名称继续作为普通元数据读取。

## 验证计划

- 新增或更新的测试：双端 DOM/按钮顺序、弹窗校验、扩展名保留、重名拦截、IndexedDB 重载、下载名更新、元数据单独同步且 Blob 上传调用为零。
- 必须运行的质量门禁：`python scripts/run_quality_gate.py`
- 部署后验证：GitHub Pages 的 KR/JP 页面均包含 `resourceRenameModal`、`renameResourceFile` 与 `metadataDirty` 元数据同步分支。
