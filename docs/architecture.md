# 单词本应用架构

## 目标

本项目交付两个可直接打开和部署的单文件应用：韩语单词本与日语单词本。两端共享相同的页面结构、交互和存储协议，仅保留质量契约明确允许的语言差异。

## 系统边界

```text
用户交互
  -> KR / JP 单文件应用
     -> 内存状态 this.words
     -> SafeStorage
        -> localStorage
        -> IndexedDB 持久化降级
     -> Supabase Auth
     -> vocab_items + 同步版本元数据

质量控制
  -> config/quality-contract.json
  -> scripts/validate_project_contract.py
  -> test_vocab_apps.py
  -> GitHub Actions / 本地质量门禁
```

## 主要职责

| 模块 | 职责 | 修改时必须检查 |
|---|---|---|
| `standalone_kr_vocab.html` | 韩语数据和完整应用运行时 | JP 镜像、存储迁移、浏览器回归 |
| `standalone_jp_vocab.html` | 日语数据和完整应用运行时 | KR 镜像、`krMeaning` 特例、浏览器回归 |
| `supabase_vocab_sync.sql` | 云端数据结构、主键和 RLS | 前端 payload、认证、分页和版本协议 |
| `test_vocab_apps.py` | 静态契约及真实浏览器回归 | 两端对称覆盖、测试隔离和可重复性 |
| `AGENTS.md`、`rules/` | AI 行为、语言学习与交付流程 | 不得与质量契约和已接受 ADR 冲突 |

## 架构原则

1. `config/quality-contract.json` 是可执行质量约束的唯一数据源。
2. 架构变化必须新增或更新 ADR，同时更新契约与自动化测试。
3. 用户数据修改必须经过持久化成功确认后才能显示成功反馈。
4. 云端版本变化、删除和本地待上传修改必须通过明确的冲突协议处理。
5. 保持单文件离线交付能力；共享模块拆分应先提供可靠构建与内联产物流程，不能直接破坏 standalone 交付。

## 变更影响路径

```text
字段变化
  -> 新增/编辑表单
  -> 内存模型
  -> 本地持久化
  -> 云端 payload
  -> 缓存迁移
  -> 列表/详情/复习/相近表达视图
  -> KR/JP 对称测试

布局或交互变化
  -> DOM 契约
  -> CSS 与事件绑定
  -> 空状态和移动端
  -> Selenium 回归
```
