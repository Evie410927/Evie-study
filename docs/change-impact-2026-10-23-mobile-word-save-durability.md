# 变更影响：手机端词条编辑耐久保存

## 问题与完成标准

- 问题：手机浏览器拒绝 localStorage 写入时，普通编辑虽然已经排队写 IndexedDB，却未等待事务结果便误报失败。
- 用户可观察结果：localStorage 受限而 IndexedDB 可用时正常保存；保存期间按钮锁定；只有两层都失败才保留弹窗并提示重试。
- 明确不在范围内：不改变词条字段、云端协议、同步方向、UI 布局或资料库 IndexedDB。
- 完成标准：KR/JP 两端均等待当前 IndexedDB 快照；成功后关闭且可恢复；双层失败回滚内存与待同步状态、不重复新词、不丢表单草稿。

## 影响范围

- [x] KR 应用
- [x] JP 应用
- [x] 数据字段或缓存迁移
- [x] localStorage / IndexedDB
- [ ] 云端 payload / RLS / 版本协议
- [ ] 列表 / 详情 / 复习 / 相近表达
- [x] 移动端与空状态
- [x] 现有规则或 ADR

## 风险与回滚

- 数据兼容风险：无格式变化；复用现有完整耐久快照。
- 并发或跨设备风险：保存期间锁定重复提交；待同步字段仍由原有逐字段协议生成。
- 安全与隐私风险：无新增外部传输。
- 回滚方法：恢复普通编辑只接受 localStorage 的同步判定；该回滚会重新产生手机端误报，不建议采用。

## 验证计划

- 新增或更新的测试：静态两层耐久契约；真实浏览器模拟 localStorage 失败/IndexedDB 成功；双层失败回滚；保存期间重复激活防护；重新读取 IndexedDB 快照验证新值。
- 必须运行的质量门禁：`python scripts/run_quality_gate.py`
- 部署后验证：KR/JP 页面均包含 `confirmLastSaveDataDurableFallback`、`reportFailure: false`、in-flight 守卫及失败回滚标记。
