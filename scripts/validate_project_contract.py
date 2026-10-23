#!/usr/bin/env python3
"""Validate architecture decisions that must stay synchronized across the app."""

from __future__ import annotations

import json
import re
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
        self.elements_by_id: dict[str, dict[str, object]] = {}
        self.review_options: list[dict[str, object]] = []
        self.page_size_options: list[dict[str, object]] = []
        self._inside_review_select = False
        self._inside_page_size_select = False

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

        if element_id:
            self.elements_by_id[element_id] = {
                "tag": tag,
                "parent_id": parent.get("id") if parent else None,
                "previous_sibling_id": previous_sibling_id,
                "attrs": attr_map,
            }

        if tag == "select" and element_id == "reviewRatingSortSelect":
            self._inside_review_select = True
        elif tag == "select" and element_id == "pageSizeSelect":
            self._inside_page_size_select = True
        elif tag == "option" and self._inside_review_select:
            self.review_options.append(
                {
                    "value": attr_map.get("value", ""),
                    "selected": "selected" in attr_map,
                }
            )
        elif tag == "option" and self._inside_page_size_select:
            self.page_size_options.append(
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
                elif tag == "select" and element.get("id") == "pageSizeSelect":
                    self._inside_page_size_select = False
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

    page_size_select = parser.elements_by_id.get(pagination_contract["pageSizeSelectId"])
    if page_size_select is None:
        fail(errors, f"{relative_path}: 缺少分页条数选择器 #{pagination_contract['pageSizeSelectId']}")
    actual_page_sizes = [int(option["value"]) for option in parser.page_size_options if str(option["value"]).isdigit()]
    if actual_page_sizes != pagination_contract["allowedPageSizes"]:
        fail(errors, f"{relative_path}: 每页条数选项应为 {pagination_contract['allowedPageSizes']}，实际为 {actual_page_sizes}")
    selected_page_sizes = [int(option["value"]) for option in parser.page_size_options if option["selected"] and str(option["value"]).isdigit()]
    if selected_page_sizes != [pagination_contract["defaultPageSize"]]:
        fail(errors, f"{relative_path}: 每页条数默认值应为 {pagination_contract['defaultPageSize']}，实际为 {selected_page_sizes}")
    default_page_size = pagination_contract["defaultPageSize"]
    required_page_size_tokens = (
        f"this.pageSize = {default_page_size};",
        f"this.pageSize = parseInt(e.target.value) || {default_page_size};",
        f"this.pageSize = parseInt(val) || {default_page_size};",
    )
    for token in required_page_size_tokens:
        if token not in content:
            fail(errors, f"{relative_path}: 分页条数默认/回退实现缺少 {token}")

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

    reset_contract = contract["uiContracts"]["partOfSpeechFilterReset"]
    reset_button = parser.elements_by_id.get(reset_contract["buttonId"])
    if reset_button is None:
        fail(errors, f"{relative_path}: 缺少词性筛选重置按钮 #{reset_contract['buttonId']}")
    else:
        if reset_button["parent_id"] != reset_contract["menuId"]:
            fail(errors, f"{relative_path}: 词性筛选重置按钮必须直属 #{reset_contract['menuId']}")
        if reset_button["previous_sibling_id"] != reset_contract["previousSiblingId"]:
            fail(errors, f"{relative_path}: 词性筛选重置按钮必须紧随 #{reset_contract['previousSiblingId']}")
        onclick = str(reset_button["attrs"].get("onclick", ""))
        if reset_contract["action"] not in onclick:
            fail(errors, f"{relative_path}: 词性筛选重置按钮未绑定 {reset_contract['action']}")

    quick_reset_button = parser.elements_by_id.get(reset_contract["quickButtonId"])
    if quick_reset_button is None:
        fail(errors, f"{relative_path}: 缺少收起状态词性快捷重置按钮 #{reset_contract['quickButtonId']}")
    else:
        if quick_reset_button["parent_id"] != reset_contract["quickParentId"]:
            fail(errors, f"{relative_path}: 词性快捷重置按钮必须直属 #{reset_contract['quickParentId']}")
        if quick_reset_button["previous_sibling_id"] != reset_contract["quickPreviousSiblingId"]:
            fail(errors, f"{relative_path}: 词性快捷重置按钮必须紧随 #{reset_contract['quickPreviousSiblingId']}")
        onclick = str(quick_reset_button["attrs"].get("onclick", ""))
        if reset_contract["action"] not in onclick:
            fail(errors, f"{relative_path}: 词性快捷重置按钮未绑定 {reset_contract['action']}")
        if "display:none" not in str(quick_reset_button["attrs"].get("style", "")).replace(" ", ""):
            fail(errors, f"{relative_path}: 词性快捷重置按钮初始状态必须隐藏")
    quick_visibility_token = "quickResetButton.style.display = count > 0 ? 'inline-flex' : 'none';"
    if quick_visibility_token not in content:
        fail(errors, f"{relative_path}: 词性快捷重置按钮未按已选数量显隐")

    tag_reset_contract = contract["uiContracts"]["tagFilterReset"]
    tag_reset_button = parser.elements_by_id.get(tag_reset_contract["buttonId"])
    if tag_reset_button is None:
        fail(errors, f"{relative_path}: 缺少 Tag 筛选重置按钮 #{tag_reset_contract['buttonId']}")
    else:
        if tag_reset_button["parent_id"] != tag_reset_contract["menuId"]:
            fail(errors, f"{relative_path}: Tag 筛选重置按钮必须直属 #{tag_reset_contract['menuId']}")
        if tag_reset_button["previous_sibling_id"] != tag_reset_contract["previousSiblingId"]:
            fail(errors, f"{relative_path}: Tag 筛选重置按钮必须紧随 #{tag_reset_contract['previousSiblingId']}")
        onclick = str(tag_reset_button["attrs"].get("onclick", ""))
        if tag_reset_contract["action"] not in onclick:
            fail(errors, f"{relative_path}: Tag 筛选重置按钮未绑定 {tag_reset_contract['action']}")

    tag_quick_reset_button = parser.elements_by_id.get(tag_reset_contract["quickButtonId"])
    if tag_quick_reset_button is None:
        fail(errors, f"{relative_path}: 缺少收起状态 Tag 快捷重置按钮 #{tag_reset_contract['quickButtonId']}")
    else:
        if tag_quick_reset_button["parent_id"] != tag_reset_contract["quickParentId"]:
            fail(errors, f"{relative_path}: Tag 快捷重置按钮必须直属 #{tag_reset_contract['quickParentId']}")
        if tag_quick_reset_button["previous_sibling_id"] != tag_reset_contract["quickPreviousSiblingId"]:
            fail(errors, f"{relative_path}: Tag 快捷重置按钮必须紧随 #{tag_reset_contract['quickPreviousSiblingId']}")
        onclick = str(tag_quick_reset_button["attrs"].get("onclick", ""))
        if tag_reset_contract["action"] not in onclick:
            fail(errors, f"{relative_path}: Tag 快捷重置按钮未绑定 {tag_reset_contract['action']}")
        if "display:none" not in str(tag_quick_reset_button["attrs"].get("style", "")).replace(" ", ""):
            fail(errors, f"{relative_path}: Tag 快捷重置按钮初始状态必须隐藏")
    tag_quick_visibility_token = "tagQuickResetButton.style.display = count > 0 ? 'inline-flex' : 'none';"
    if tag_quick_visibility_token not in content:
        fail(errors, f"{relative_path}: Tag 快捷重置按钮未按已选数量显隐")

    active_tags_bar = parser.elements_by_id.get("activeTagsBar")
    if active_tags_bar is None:
        fail(errors, f"{relative_path}: 缺少兼容节点 #activeTagsBar")
    else:
        active_bar_style = str(active_tags_bar["attrs"].get("style", "")).replace(" ", "")
        if "display:none" not in active_bar_style or active_tags_bar["attrs"].get("aria-hidden") != "true":
            fail(errors, f"{relative_path}: #activeTagsBar 必须静态隐藏且对辅助技术隐藏")
    required_hidden_summary_tokens = (
        "bar.innerHTML = '';",
        "bar.style.display = 'none';",
        "bar.setAttribute('aria-hidden', 'true');",
    )
    for token in required_hidden_summary_tokens:
        if token not in content:
            fail(errors, f"{relative_path}: Tag 旧摘要栏缺少持续隐藏实现 {token}")
    for forbidden_markup in ('<span class="active-tag-chip">', '<button class="clear-all-tags-chip-btn"'):
        if forbidden_markup in content:
            fail(errors, f"{relative_path}: 搜索框下方仍会渲染旧 Tag 摘要 {forbidden_markup}")

    word_editor_save_contract = contract["uiContracts"]["wordEditorSave"]
    save_button = parser.elements_by_id.get(word_editor_save_contract["buttonId"])
    if save_button is None:
        fail(errors, f"{relative_path}: 缺少词条编辑保存按钮 #{word_editor_save_contract['buttonId']}")
    required_direct_save_tokens = (
        "document.getElementById('saveWordBtn')?.addEventListener('pointerdown', (e) => {",
        "this._wordModalPointerSaveHandled = true;",
        "this._wordModalPointerSaveHandled = false;",
        "if (this._wordModalPointerSaveHandled) return;",
        "this.commitWordModalDraftAndSave();",
        "async commitWordModalDraftAndSave() {",
        "const activeElement = document.activeElement;",
        "form.contains(activeElement)",
        "activeElement.blur();",
        "return await this.saveWordFromForm();",
        "if (this._wordModalSaveInFlight) return false;",
        "saveButton.disabled = true;",
        "saveButton.setAttribute('aria-busy', 'true');",
        "saveData(options = {})",
        "this._lastSaveDataDurablePromise = this.queueDurableSnapshot();",
        "async confirmLastSaveDataDurableFallback()",
        "async saveWordFromForm()",
        "this.saveData({ reportFailure: false });",
        "await this.confirmLastSaveDataDurableFallback();",
        "this.words = JSON.parse(wordsBeforeSave);",
        "this.savePendingCloudChanges(pendingBeforeSave);",
        "pendingIds: Object.keys(pending)",
        "if (durablePendingOnly > 0 && localPendingOnly === 0) return true;",
        "localStorage 与 IndexedDB 均未能持久保存",
    )
    for token in required_direct_save_tokens:
        if token not in content:
            fail(errors, f"{relative_path}: 词条编辑首次交互直接保存契约缺少 {token}")

    resource_contract = contract["uiContracts"]["resourceLibrary"]
    excel_contract = contract["uiContracts"]["vocabularyExcelExport"]
    excel_import_contract = contract["uiContracts"]["vocabularyExcelImport"]
    cloud_sync_undo_contract = contract["uiContracts"]["cloudSyncUndo"]
    history_limit = cloud_sync_undo_contract.get("maximumSnapshots")
    if history_limit != 2:
        fail(errors, "质量契约：云同步撤销历史必须只保留最近 2 份")
    required_history_limit_tokens = (
        f"this.CLOUD_SYNC_UNDO_HISTORY_LIMIT = {history_limit};",
        ".slice(0, this.CLOUD_SYNC_UNDO_HISTORY_LIMIT)",
        "if (stored.length !== history.length)",
        f"最多保留最近 {history_limit} 份同步或 Excel 导入前快照",
    )
    for token in required_history_limit_tokens:
        if token not in content:
            fail(errors, f"{relative_path}: 云同步历史缺少最近 {history_limit} 份上限或旧历史裁剪实现 {token}")
    if excel_contract.get("allowedRatings") != [0, 1, 2, 3, 4, 5]:
        fail(errors, "质量契约：Excel 导出星级范围必须固定为 0～5 星")
    if excel_contract.get("customSaveLocationControl") != "automatic-no-visible-toggle":
        fail(errors, "质量契约：Excel 导出保存位置必须自动判断且不显示开关")
    if excel_contract.get("columns") != {
        "word": "单词",
        "partOfSpeech": "词性",
        "meaning": "释义",
        "example": "例句",
        "reading": "发音",
        "pronunciationNote": "发音备注",
        "userNote": "说明",
        "similarWords": "相近词汇",
    }:
        fail(errors, "质量契约：Excel 导出列必须固定为八个指定字段")
    if excel_contract.get("defaultSelectedColumns") != ["word", "partOfSpeech", "meaning", "example"] or excel_contract.get("minimumSelectedColumns") != 1:
        fail(errors, "质量契约：Excel 导出必须默认勾选前四列且至少保留一列")
    if (
        excel_import_contract.get("acceptedExtension") != "xlsx"
        or excel_import_contract.get("legacyWithoutStableIdRequiresFirstColumn") != "word"
        or excel_import_contract.get("newExportMayOmitWordColumn") is not True
    ):
        fail(errors, "质量契约：Excel 回导必须只接受 xlsx；新版按稳定 ID 导入，旧版无 ID 时第一列固定为单词")
    if excel_import_contract.get("preImportSnapshot") != "required-local-version-history-snapshot":
        fail(errors, "质量契约：Excel 回导必须在改写词库前保存本地版本快照")
    if cloud_sync_undo_contract.get("snapshotSources") != ["cloud-sync", "excel-import"]:
        fail(errors, "质量契约：版本历史必须同时覆盖云同步与 Excel 导入")
    resource_button = parser.elements_by_id.get(resource_contract["buttonId"])
    import_button = parser.elements_by_id.get(excel_import_contract["buttonId"])
    export_button = parser.elements_by_id.get(excel_contract["buttonId"])
    quick_add_button = parser.elements_by_id.get("quickAddBtn")
    if resource_button is None or import_button is None or export_button is None or quick_add_button is None:
        fail(errors, f"{relative_path}: Header 缺少资料库、Excel 导入、Excel 导出或新增词条按钮")
    else:
        if import_button["previous_sibling_id"] != resource_contract["buttonId"]:
            fail(errors, f"{relative_path}: Excel 导入按钮必须紧随资料库按钮")
        if export_button["previous_sibling_id"] != excel_import_contract["buttonId"]:
            fail(errors, f"{relative_path}: Excel 导出按钮必须紧随 Excel 导入按钮")
        if quick_add_button["previous_sibling_id"] != excel_contract["buttonId"]:
            fail(errors, f"{relative_path}: 新增词条按钮必须紧随 Excel 导出按钮")
    required_excel_tokens = (
        'id="excelExportModal"',
        "this.excelExportScope = 'all'",
        "this.excelExportTags = new Set()",
        "this.excelExportRatings = new Set()",
        'value="ratings"',
        'id="excelExportRatingPanel"',
        'id="excelExportColumnsPanel"',
        'name="excelExportColumn"',
        "this.excelExportSelectedColumns = new Set(['word', 'partOfSpeech', 'meaning', 'example'])",
        "new Set(['word', 'partOfSpeech', 'meaning', 'example', 'reading', 'pronunciationNote', 'userNote', 'similarWords'])",
        "this.excelExportSelectedColumns.size === 0",
        "请至少选择一个导出列",
        "some(tag => selected.has(",
        "this.excelExportRatings.has(this.normalizeExcelExportRating(word?.rating))",
        "const firstExample = this.getParsedExamples(word)[0]",
        "isJapanese ? '中韩意思' : '中文意思'",
        "window.showSaveFilePicker",
        "await fileHandle.createWritable()",
        "浏览器默认下载位置",
        "title: '相近词汇'",
        "this.getSimilarWords(word, Number.POSITIVE_INFINITY).map(similarWord =>",
        ".join('：')",
        "const lastColumnName = columnNames[columnNames.length - 1]",
        "name: 'xl/worksheets/sheet1.xml'",
        "name: 'xl/styles.xml'",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xlsx`",
    )
    for token in required_excel_tokens:
        if token not in content:
            fail(errors, f"{relative_path}: Excel 导出缺少实现标记 {token}")
    if 'excelExportChooseLocation' in content or 'excel-export-save-location' in content:
        fail(errors, f"{relative_path}: Excel 导出不得显示保存位置开关")
    required_excel_import_tokens = (
        'id="importExcelBtn"',
        'id="importExcelFileInput"',
        'accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"',
        "importVocabularyExcelFile(event)",
        "getVocabularyExcelImportDefinitions()",
        "readVocabularyXlsxEntries(file)",
        "parseVocabularyWorksheetRows(sheetXml, sharedStringsXml = '')",
        "parseVocabularyXlsxFile(file)",
        "prepareVocabularyExcelImport(rows)",
        "'__EVIE_WORD_ID__'",
        "旧版文件没有词条标识时，第一列表头必须保持为“单词”",
        "第一行字段名称被修改、重复或顺序不正确",
        "第 ${item.excelRow} 行的词条标识不存在",
        "this.saveLocalVersionUndoSnapshot('Excel 导入')",
        "this.markPendingCloudChanges(plan.changedIds, plan.changedAt, 'user', plan.changedFieldsById)",
        "this.saveData({ reportFailure: false })",
        "await this.confirmLastSaveDataDurableFallback()",
        "await this.discardCloudSyncUndoSnapshot(snapshotId)",
        "cloud: { rows: [], revision: this.getCloudBaselineRevision(), available: false }",
        "此版本只记录了本浏览器状态，不能恢复云端",
    )
    for token in required_excel_import_tokens:
        if token not in content:
            fail(errors, f"{relative_path}: Excel 严格回导缺少实现标记 {token}")
    if resource_contract.get("localIsolation") == "filter-by-current-language":
        language_code = "kr" if relative_path == "standalone_kr_vocab.html" else "jp"
        required_resource_language_tokens = (
            "this.RESOURCE_DB_VERSION = 3",
            f"this.RESOURCE_LANGUAGE = '{language_code}'",
            "this.RESOURCE_LEGACY_LANGUAGE = 'jp'",
            "store.createIndex('language', 'language', { unique: false })",
            "deletionStore.createIndex('language', 'language', { unique: false })",
            "normalizedRecords.filter(record => record.language === this.RESOURCE_LANGUAGE)",
            "language=eq.${encodeURIComponent(this.RESOURCE_LANGUAGE)}",
            "on_conflict=user_id,language,resource_id",
            "${userId}/${this.RESOURCE_LANGUAGE}/${record.id}/${record.id}.${extension}",
        )
        for token in required_resource_language_tokens:
            if token not in content:
                fail(errors, f"{relative_path}: 学习资料语言隔离缺少实现标记 {token}")
    if resource_contract.get("manualOrderField") == "sortOrder":
        required_resource_order_tokens = (
            ".resource-file-drag-handle {",
            "touch-action: none;",
            "dragHandle.addEventListener('pointerdown'",
            "dragHandle.addEventListener('keydown'",
            "async persistResourceFileOrder(orderedIds, focusResourceId = '')",
            "await this.putResourceRecords(reordered);",
            "sortOrder: index,",
            "orderUpdatedAt,",
            "orderDirty: true",
            "isResourceOrderSchemaError(data, status = 0)",
            "async upsertResourceOrderRows(accessToken, userId, records)",
            "missing=default",
            "sort_order",
            "order_updated_at",
            "orderSynced === false",
        )
        for token in required_resource_order_tokens:
            if token not in content:
                fail(errors, f"{relative_path}: 学习资料手动排序缺少实现标记 {token}")
        if resource_contract.get("manualOrderCloudFallback") == "local-order-remains-pending-when-columns-unavailable":
            fallback_tokens = (
                "this._resourceOrderCloudSupported = false;",
                "return fetchPages(false);",
                "await writeRows(false);",
                "Boolean(pendingRecord.orderDirty)",
            )
            for token in fallback_tokens:
                if token not in content:
                    fail(errors, f"{relative_path}: 旧资料云表排序字段降级缺少实现标记 {token}")
    if resource_contract.get("renameButtonPlacement") == "immediately-before-download-button":
        required_resource_rename_tokens = (
            f'id="{resource_contract["renameModalId"]}"',
            f'id="{resource_contract["renameInputId"]}"',
            "renameButton.className = 'resource-file-action rename'",
            "actions.append(dragHandle, renameButton, downloadButton, deleteButton)",
            "openResourceRenameModal(resourceId, trigger = null)",
            "async renameResourceFile()",
            "metadataDirty: true",
            "if (record.metadataDirty &&",
            "metadataDirty: false",
            "当前资料库中已存在同名文件",
            "文件名不能包含",
        )
        for token in required_resource_rename_tokens:
            if token not in content:
                fail(errors, f"{relative_path}: 学习资料重命名缺少实现标记 {token}")
        needs_upload_match = re.search(r"const needsUpload = record\?\.blob instanceof Blob && \((.*?)\);", content, re.DOTALL)
        if not needs_upload_match or "updatedAt" in needs_upload_match.group(1):
            fail(errors, f"{relative_path}: 资料改名不得通过 updatedAt 触发 Blob 重复上传")

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

    pronunciation_contract = contract["uiContracts"]["inlinePronunciationNote"]
    if "similar-word-card-title" in pronunciation_contract["contexts"]:
        required_similar_note_tokens = (
            "const cleanPronunciationNote = typeof w.pronunciationNote === 'string' ? w.pronunciationNote.trim() : '';",
            '<span class="similar-word-pronunciation-note"',
            'title="${this.escapeHtml(cleanPronunciationNote)}"',
            '>${this.escapeHtml(cleanPronunciationNote)}</span>',
            ".similar-word-pronunciation-note {",
            "color: #f6a96b;",
            "text-overflow: ellipsis;",
        )
        for token in required_similar_note_tokens:
            if token not in content:
                fail(errors, f"{relative_path}: 相近表达发音备注展示缺少实现标记 {token}")
        if pronunciation_contract.get("similarWordVerticalAlignment") == "typographic-baseline":
            baseline_title_css = ".similar-word-title {\n  display: flex;\n  align-items: baseline;"
            if baseline_title_css not in content:
                fail(errors, f"{relative_path}: 相近表达标题中的词条、读音与发音备注必须按文字基线对齐")
        if pronunciation_contract.get("similarWordSharedLineHeight") == 1.25:
            for selector in (".similar-word-text", ".similar-word-reading", ".similar-word-pronunciation-note"):
                css_block = re.search(rf"{re.escape(selector)}\s*\{{([^}}]*)\}}", content, re.DOTALL)
                if not css_block or "line-height: 1.25;" not in css_block.group(1):
                    fail(errors, f"{relative_path}: {selector} 必须使用契约规定的 1.25 统一行高")
        reading_markup = '${cleanReading ? `<span class="similar-word-reading"'
        note_markup = '${cleanPronunciationNote ? `<span class="similar-word-pronunciation-note"'
        if reading_markup not in content or note_markup not in content or content.index(reading_markup) > content.index(note_markup):
            fail(errors, f"{relative_path}: 相近表达发音备注必须紧随读音标注之后")


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
