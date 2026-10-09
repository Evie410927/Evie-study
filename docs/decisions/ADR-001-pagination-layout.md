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

分页条数选择器统一提供 10、20、50 三档，并默认选中 50。应用构造时的 `pageSize` 以及条数解析失败时的回退值也必须为 50，确保静态 DOM、运行状态与分页结果一致。

## 验证

- 契约验证器检查父节点、前置兄弟节点、Class 和内联间距。
- 契约验证器同时检查每页条数选项、默认选中值与运行时初始/回退值。
- Selenium 检查滚动时分页栏保持固定，并与底部 Tab 不重叠。
- Selenium 检查首次加载时选择器与应用状态均为每页 50 条。
