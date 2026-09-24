#!/usr/bin/env python3
"""Validate architecture decisions that must stay synchronized across the app."""

from __future__ import annotations

import json
import sys
from html.parser import HTMLParser
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = PROJECT_ROOT / "config" / "quality-contract.json"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


class AppContractParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[dict[str, object]] = []
        self.pagination: dict[str, object] | None = None
        self.review_options: list[dict[str, object]] = []
        self._inside_review_select = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value or "" for key, value in attrs}
        parent = self.stack[-1] if self.stack else None
        parent_children = parent["children"] if parent else []
        previous_sibling_id = parent_children[-1] if parent_children else None
        element_id = attr_map.get("id") or None
        if parent is not None:
            parent_children.append(element_id)

        if element_id == "paginationBar":
            self.pagination = {
                "parent_id": parent.get("id") if parent else None,
                "previous_sibling_id": previous_sibling_id,
                "class": attr_map.get("class", ""),
                "style": attr_map.get("style", ""),
            }

        if tag == "select" and element_id == "reviewRatingSortSelect":
            self._inside_review_select = True
        elif tag == "option" and self._inside_review_select:
            self.review_options.append(
                {
                    "value": attr_map.get("value", ""),
                    "selected": "selected" in attr_map,
                }
            )

        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append({"tag": tag, "id": element_id, "children": []})

    def handle_endtag(self, tag: str) -> None:
        while self.stack:
            element = self.stack.pop()
            if element["tag"] == tag:
                if tag == "select" and element.get("id") == "reviewRatingSortSelect":
                    self._inside_review_select = False
                break


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def require_file(errors: list[str], relative_path: str) -> Path:
    path = PROJECT_ROOT / relative_path
    if not path.is_file():
        fail(errors, f"缺少契约要求的文件: {relative_path}")
    return path


def validate_app(errors: list[str], relative_path: str, contract: dict[str, object]) -> None:
    path = require_file(errors, relative_path)
    if not path.is_file():
        return
    content = path.read_text(encoding="utf-8")
    parser = AppContractParser()
    parser.feed(content)

    pagination_contract = contract["uiContracts"]["pagination"]
    pagination = parser.pagination
    if pagination is None:
        fail(errors, f"{relative_path}: 缺少 #paginationBar")
    else:
        expected_class = pagination_contract["class"]
        classes = str(pagination["class"]).split()
        checks = {
            "parentId": pagination["parent_id"],
            "previousSiblingId": pagination["previous_sibling_id"],
            "inlineStyle": pagination["style"],
        }
        for key, actual in checks.items():
            expected = pagination_contract[key]
            if actual != expected:
                fail(errors, f"{relative_path}: pagination {key} 应为 {expected!r}，实际为 {actual!r}")
        if expected_class not in classes:
            fail(errors, f"{relative_path}: #paginationBar 缺少类 {expected_class}")

    review_contract = contract["uiContracts"]["reviewOrder"]
    actual_values = [option["value"] for option in parser.review_options]
    if actual_values != review_contract["allowed"]:
        fail(errors, f"{relative_path}: 复习排序选项应为 {review_contract['allowed']}，实际为 {actual_values}")
    selected_values = [option["value"] for option in parser.review_options if option["selected"]]
    if selected_values != [review_contract["default"]]:
        fail(errors, f"{relative_path}: 复习默认排序应为 {review_contract['default']}，实际为 {selected_values}")
    if "this.reviewRatingSort = 'createdDesc'" not in content:
        fail(errors, f"{relative_path}: reviewRatingSort 运行时默认值不是 createdDesc")
    if "this.sortReviewWordsBySimilarity(this.reviewList)" in content:
        fail(errors, f"{relative_path}: 仍存在已废止的自动相似表达聚类调用")

    similar_contract = contract["dataContracts"]["similarWords"]
    if similar_contract["mode"] == "manual-only":
        required_manual_tokens = (
            "newWord.autoSimilarWordIds = [];",
            "w.autoSimilarWordIds = [];",
            "manualSimilarWordIds",
            "暂无相近表达，可点击右上角＋添加",
        )
        for token in required_manual_tokens:
            if token not in content:
                fail(errors, f"{relative_path}: 人工相近表达契约缺少实现标记 {token}")
        forbidden_automatic_tokens = (
            "calculateAutomaticSimilarWords(",
            "automaticWords.concat(",
            "targetWord.autoSimilarWordIds = this.",
        )
        for token in forbidden_automatic_tokens:
            if token in content:
                fail(errors, f"{relative_path}: 仍包含自动相近表达实现 {token}")


def main() -> None:
    errors: list[str] = []
    if not CONTRACT_PATH.is_file():
        print("[CONTRACT][FAIL] 缺少 config/quality-contract.json")
        raise SystemExit(1)
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    authority = contract["authority"]
    for key in ("architecture", "dataContract"):
        require_file(errors, authority[key])
    for decision in authority["decisions"]:
        decision_path = require_file(errors, decision)
        if decision_path.is_file() and "状态：Accepted" not in decision_path.read_text(encoding="utf-8"):
            fail(errors, f"{decision}: ADR 尚未标记为 Accepted")

    for app in contract["mirroredApps"]:
        validate_app(errors, app, contract)

    agents_path = require_file(errors, "AGENTS.md")
    if agents_path.is_file():
        agents = agents_path.read_text(encoding="utf-8")
        required_markers = (
            "config/quality-contract.json",
            "python scripts/run_quality_gate.py",
            "ADR-001",
            "ADR-002",
        )
        for marker in required_markers:
            if marker not in agents:
                fail(errors, f"AGENTS.md 缺少质量契约标记: {marker}")
        forbidden_markers = (
            "放置在 `#wordList` 容器内部的最末尾",
            "必须根据单词/表达的中文释义与标签进行语义相似度聚类",
            "已有存量词条保留既有自动快照不动",
            "加入 note 时双向持久关联",
            "包含 `🔊` 发音朗读、`✅ 掌握 / 🔄 学习中` 状态切换",
        )
        for marker in forbidden_markers:
            if marker in agents:
                fail(errors, f"AGENTS.md 仍包含已被 ADR 替代的规则: {marker}")

    test_path = require_file(errors, "test_vocab_apps.py")
    if test_path.is_file():
        test_source = test_path.read_text(encoding="utf-8")
        if "PROJECT_ROOT = Path(__file__).resolve().parent" not in test_source:
            fail(errors, "test_vocab_apps.py 未使用跨平台项目根路径")
        if "C:\\Users\\" in test_source:
            fail(errors, "test_vocab_apps.py 仍包含用户机器绝对路径")

    workflow_path = require_file(errors, ".github/workflows/quality.yml")
    if workflow_path.is_file() and "python scripts/run_quality_gate.py" not in workflow_path.read_text(encoding="utf-8"):
        fail(errors, "GitHub Actions 未运行完整质量门禁")

    if errors:
        print("[CONTRACT][FAIL] 项目质量契约不一致：")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(1)

    print("[CONTRACT][PASS] 架构决策、双端 DOM 和质量门禁配置一致。")


if __name__ == "__main__":
    main()
