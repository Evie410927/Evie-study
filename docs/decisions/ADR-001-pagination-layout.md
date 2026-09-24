# ADR-001：分页栏位于滚动列表外部

- 状态：Accepted
- 日期：2026-09-24

## 决策

`#paginationBar` 必须是 `#tab-list` 的直接子节点，并紧邻在 `#wordList` 之后。它不能放进可滚动的 `#wordList`，否则分页栏会随卡片滚动并可能遮挡操作区域。

两端统一使用：

```html
<div id="wordList" class="word-list"></div>
<div id="paginationBar" class="pagination-bar word-list-inline-pagination"
     style="margin-top: 2px; margin-bottom: 0px;"></div>
```

## 验证

- 契约验证器检查父节点、前置兄弟节点、Class 和内联间距。
- Selenium 检查滚动时分页栏保持固定，并与底部 Tab 不重叠。
