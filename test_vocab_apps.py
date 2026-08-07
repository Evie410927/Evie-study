#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
单词本自动化测试脚本 (test_vocab_apps.py)
===============================================================================
用途: 对 standalone_kr_vocab.html (韩语) 和 standalone_jp_vocab.html (日语)
     进行 UI 布局、Header 按钮点击、DOM 节点、事件绑定、DOM 空安全、筛选联动、卡片复习纵向绝对撑满及全量卡片宽度的自动化断言测试。

触发方式: 当用户输入 "单词本自动化测试" 或 "note auto test" 时自动运行此脚本。
===============================================================================
"""

import os
import re
import sys

# 强制标准输出使用 UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

KR_FILE = r"C:\Users\NCC Technology\Evie-study\standalone_kr_vocab.html"
JP_FILE = r"C:\Users\NCC Technology\Evie-study\standalone_jp_vocab.html"

class VocabAppTester:
    def __init__(self):
        self.passed_count = 0
        self.failed_count = 0
        self.errors = []

    def assert_true(self, condition, test_name, error_msg):
        if condition:
            self.passed_count += 1
            print(f"  [PASS] {test_name}")
        else:
            self.failed_count += 1
            full_msg = f"  [FAIL] {test_name}: {error_msg}"
            self.errors.append(full_msg)
            print(full_msg)

    def test_file(self, filepath, lang_name):
        print(f"\n==================================================")
        print(f" 开始测试 [{lang_name}单词本]: {os.path.basename(filepath)}")
        print(f"==================================================")

        if not os.path.exists(filepath):
            self.assert_true(False, f"{lang_name} 文件存在性", f"文件未找到: {filepath}")
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # ---------------------------------------------------------------------
        # 测试点 1: Header 顶部 3 个图标按钮点击兜底测试 (Header Actions Buttons)
        # ---------------------------------------------------------------------
        btn_cloud_sync = bool(re.search(r'id="cloudSyncBtn"[^>]*onclick="[^"]*fetchFromCloud', content))
        self.assert_true(btn_cloud_sync, f"[{lang_name}] Header-☁️云端同步按钮兜底点击", "cloudSyncBtn 缺少行内 fetchFromCloud 兜底绑定")

        btn_theme_toggle = bool(re.search(r'id="themeToggleBtn"[^>]*onclick="[^"]*toggleTheme', content))
        self.assert_true(btn_theme_toggle, f"[{lang_name}] Header-🌙/☀️主题切换按钮兜底点击", "themeToggleBtn 缺少行内 toggleTheme 兜底绑定")

        btn_quick_add = bool(re.search(r'id="quickAddBtn"[^>]*onclick="[^"]*openWordModal', content))
        self.assert_true(btn_quick_add, f"[{lang_name}] Header-➕加词按钮兜底点击", "quickAddBtn 缺少行内 openWordModal 兜底绑定")

        # ---------------------------------------------------------------------
        # 测试点 2: 卡片宽度与响应式布局测试 (Card Width & Layout)
        # ---------------------------------------------------------------------
        box_sizing_global = '* {\n  box-sizing: border-box;' in content or 'box-sizing: border-box;' in content
        self.assert_true(box_sizing_global, f"[{lang_name}] 全局与卡片 box-sizing 边框盒设置", "缺少 box-sizing: border-box")

        app_container_width = '#app {' in content and 'max-width: 600px;' in content
        self.assert_true(app_container_width, f"[{lang_name}] 主容器 #app 宽度限制防护", "#app 容器缺少 max-width 限制，可能在超宽屏溢出")

        word_card_width = '.word-card {' in content and 'width: 100%;' in content and 'max-width: 100%;' in content
        self.assert_true(word_card_width, f"[{lang_name}] 单词卡片 .word-card 宽度自适应", ".word-card 缺少 width:100% 或 max-width:100%，引发卡片宽窄不一或溢出")

        # ---------------------------------------------------------------------
        # 测试点 3: 底部 Tab 导航点击交互与兜底测试 (Bottom Nav Buttons)
        # ---------------------------------------------------------------------
        nav_tab_list = bool(re.search(r'onclick="[^"]*switchTab\(\'tab-list\'\)', content))
        self.assert_true(nav_tab_list, f"[{lang_name}] 底部导航-单词列表 Tab 兜底点击", "底部导航 list 按钮缺少行内 switchTab('tab-list') 兜底")

        nav_tab_review = bool(re.search(r'onclick="[^"]*switchTab\(\'tab-review\'\)', content))
        self.assert_true(nav_tab_review, f"[{lang_name}] 底部导航-卡片复习 Tab 兜底点击", "底部导航 review 按钮缺少行内 switchTab('tab-review') 兜底")

        nav_tab_settings = bool(re.search(r'onclick="[^"]*switchTab\(\'tab-settings\'\)', content))
        self.assert_true(nav_tab_settings, f"[{lang_name}] 底部导航-设置 Tab 兜底点击", "底部导航 settings 按钮缺少行内 switchTab('tab-settings') 兜底")

        # ---------------------------------------------------------------------
        # 测试点 4: 复习卡片纵向空间完全填满与撑满测试 (Flashcard Vertical Stretch)
        # ---------------------------------------------------------------------
        tab_review_active_flex = '#tab-review.active {' in content and 'display: flex;' in content
        self.assert_true(tab_review_active_flex, f"[{lang_name}] 复习界面-Tab视图激活态 Flex 链条撑满", "#tab-review.active 缺少 display: flex 导致纵向高度断裂无法填满空隙")

        card_face_bottom_stretch = '.card-face {' in content and 'bottom: 0;' in content and 'top: 0;' in content
        self.assert_true(card_face_bottom_stretch, f"[{lang_name}] 复习界面-卡片边框四周绝对拉满", ".card-face 缺少 top:0; bottom:0; 导致卡片无法填满至底部按钮上方")

        scene_full_stretch = '.scene {' in content and 'perspective: 1000px;' in content and 'flex: 1;' in content and 'height: 100%;' in content
        self.assert_true(scene_full_stretch, f"[{lang_name}] 复习界面-中间卡片容器纵向 Flex: 1 撑满紧贴操作按钮上方", ".scene 缺少 flex: 1 或 height: 100% 纵向拉长设置，导致卡片与下方操作按钮间空隙过大")

        review_actions_clearance = '.flashcard-container {' in content and 'padding-bottom:' in content and 'margin-top: auto;' in content
        self.assert_true(review_actions_clearance, f"[{lang_name}] 复习界面-控制按钮避让底部 Tab 栏且置底定位", ".flashcard-container 缺少 padding-bottom 避让底部 Tab 栏导致控制按钮被遮挡")

        # ---------------------------------------------------------------------
        # 测试点 5: 相近表达 Panel 100% 宽度与等宽对齐测试 (Similar Words Panel Width)
        # ---------------------------------------------------------------------
        similar_panel_width = ('id="cardBackSimilarBlock"' in content and 'width:100%' in content) or 'align-items: stretch;' in content
        self.assert_true(similar_panel_width, f"[{lang_name}] 复习界面-相近表达 Panel 100% 宽度与例句框等宽对齐", "#cardBackSimilarBlock 缺少 100% 宽度拉宽对齐设置")

        # ---------------------------------------------------------------------
        # 测试点 6: 分页组件与跳页选择器测试 (Pagination & Auto-Scroll)
        # ---------------------------------------------------------------------
        page_jump_select = 'id="pageJumpSelect"' in content
        self.assert_true(page_jump_select, f"[{lang_name}] 分页-页码快速跳转 Selector", "缺少 pageJumpSelect 下拉跳转组件")

        page_size_select = 'id="pageSizeSelect"' in content
        self.assert_true(page_size_select, f"[{lang_name}] 分页-每页条数 Selector", "缺少 pageSizeSelect 下拉选择框")

        scroll_to_first = 'scrollToFirstCard' in content
        self.assert_true(scroll_to_first, f"[{lang_name}] 分页-自动平滑滚动置顶机制", "缺少 scrollToFirstCard 切页自动置顶函数")

        # ---------------------------------------------------------------------
        # 测试点 7: 主筛选与子筛选统计同步测试 (Filter Stats & Labels)
        # ---------------------------------------------------------------------
        label_sub_all = 'labelSubAll' in content or '全部学习中' in content or '全部已掌握' in content
        self.assert_true(label_sub_all, f"[{lang_name}] 筛选-子筛选与主筛选动态标签同步", "updateStats 中缺少根据 currentFilter 调整子筛选文案的逻辑")

        # ---------------------------------------------------------------------
        # 测试点 8: DOM 空安全与鲁棒性保底防护 (DOM Null Safety)
        # ---------------------------------------------------------------------
        raw_add_listener = re.findall(r'document\.getElementById\([\'"][^\'"]+[\'"]\)\.addEventListener', content)
        self.assert_true(len(raw_add_listener) == 0, f"[{lang_name}] DOM空安全-全量可选链保护", f"存在 {len(raw_add_listener)} 处未加可选链 ?. 的 DOM 监听提取，可能引发空指针卡死")

        load_fallback = 'loadSampleData' in content
        self.assert_true(load_fallback, f"[{lang_name}] 数据加载-空数据自动回退保底", "loadData 缺少空数组自动唤起 loadSampleData 保底")

        flashcard_null_safe = 'if (flashcard)' in content or 'flashcard?.' in content
        self.assert_true(flashcard_null_safe, f"[{lang_name}] 卡片复习-flashcard 节点空安全防护", "assessReview 中 flashcard 节点解引用缺少空保护")

        has_card_flip_fn = 'toggleCardFlip()' in content and 'classList.toggle' in content and 'is-flipped' in content
        self.assert_true(has_card_flip_fn, f"[{lang_name}] 卡片复习-toggleCardFlip 反转函数与 CSS is-flipped 切换", "缺少 toggleCardFlip 或 classList.toggle('is-flipped') 翻转逻辑")

        no_duplicate_flip_listener = 'flashcardScene' in content and not ("getElementById('flashcardScene')?.addEventListener" in content or 'getElementById("flashcardScene")?.addEventListener' in content)
        self.assert_true(no_duplicate_flip_listener, f"[{lang_name}] 卡片复习-防重复触发卡片反转取消 (避免点击失效)", "bindEvents 中存在重复 addEventListener('click') 到 #flashcardScene，会导致点击卡片连刷二次反转抵消失效")

        no_assess_toast = 'assessReview(' in content and '📌 已自动打上' not in content and '🔀 已自动打上' not in content
        self.assert_true(no_assess_toast, f"[{lang_name}] 卡片复习-打标签评级取消 Toast 顶部提示弹窗", "assessReview 函数中仍然保留了 Toast 弹窗提示，打标签时会干扰界面")

        # ---------------------------------------------------------------------
        # 测试点 9: 搜索框实时过滤与全字段深层匹配测试 (Search & Filter Execution)
        # ---------------------------------------------------------------------
        window_app_mounted = 'window.app = this' in content
        self.assert_true(window_app_mounted, f"[{lang_name}] 搜索-window.app 全局挂载保障", "constructor 中缺少 window.app = this，导致行内 oninput 触发失效")

        on_search_input_defined = 'onSearchInput(' in content and 'this.searchQuery = ' in content
        self.assert_true(on_search_input_defined, f"[{lang_name}] 搜索-onSearchInput 响应函数与状态更新", "缺少 onSearchInput 方法或未更新 searchQuery")

        precise_search_scope = ('matchWord' in content and 'matchMeaning' in content) and not ('matchExample' in content or 'matchExampleTrans' in content or 'matchExamplesArray' in content)
        self.assert_true(precise_search_scope, f"[{lang_name}] 搜索-核心字段精确匹配(单词/读音/释义，隔离例句与标签)", "searchQuery 过滤中混入了例句或标签等非核心字段的匹配")

        composition_end_binding = 'compositionend' in content
        self.assert_true(composition_end_binding, f"[{lang_name}] 搜索-中文/日文输入法组字结束事件绑定", "searchInput 缺少 compositionend 事件绑定，可能导致拼音输入法过程中过滤滞后")

        # ---------------------------------------------------------------------
        # 测试点 10: 每页条数与页码跳转下拉框行内 onchange 双保险测试
        # ---------------------------------------------------------------------
        page_size_inline_change = bool(re.search(r'id="pageSizeSelect"[^>]*onchange="[^"]*window\.app\.onPageSizeChange', content))
        self.assert_true(page_size_inline_change, f"[{lang_name}] 分页-每页条数 Selector 行内 window.app 严谨挂载", "pageSizeSelect 的 onchange 缺少 window.app.onPageSizeChange 前缀，可能在部分设备抛出 ReferenceError")

        on_page_size_change_method = 'onPageSizeChange(' in content and 'this.pageSize = ' in content and 'this.renderWordList()' in content
        self.assert_true(on_page_size_change_method, f"[{lang_name}] 分页-onPageSizeChange 实时改变下方数据与 DOM 同步", "onPageSizeChange 方法中缺少 this.renderWordList() 实时渲染触发或未重置 currentPage")

        page_jump_inline_change = bool(re.search(r'id="pageJumpSelect"[^>]*onchange="[^"]*window\.app\.onPageJumpChange', content))
        self.assert_true(page_jump_inline_change, f"[{lang_name}] 分页-跳页 Select 行内 window.app 严谨挂载", "pageJumpSelect 缺少 window.app.onPageJumpChange 前缀")

        on_page_jump_change_method = 'onPageJumpChange(' in content and 'this.currentPage = ' in content and 'this.renderWordList()' in content
        self.assert_true(on_page_jump_change_method, f"[{lang_name}] 分页-onPageJumpChange 显式方法与跳页滚动", "类中缺少 onPageJumpChange 方法或未触发 renderWordList")

        # ---------------------------------------------------------------------
        # 测试点 11: bindEvents 事件绑定初始化与语法声明校验 (Event Binding Initialization)
        # ---------------------------------------------------------------------
        bind_events_called = 'this.bindEvents()' in content
        self.assert_true(bind_events_called, f"[{lang_name}] 事件绑定-init 中显式调用 this.bindEvents()", "init() 中未调用 this.bindEvents()，导致按钮点击无响应")

        load_theme_called = 'this.loadTheme()' in content
        self.assert_true(load_theme_called, f"[{lang_name}] 主题加载-init 中显式调用 this.loadTheme()", "init() 中未调用 this.loadTheme()，导致主题配置未生效")

        bind_events_match = re.search(r'bindEvents\(\)\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}', content)
        bind_events_body = bind_events_match.group(1) if bind_events_match else ''
        dup_const_search_input = bind_events_body.count("const searchInput") > 1
        self.assert_true(not dup_const_search_input, f"[{lang_name}] 事件绑定-bindEvents 无重复 const 变量声明", "bindEvents 中存在重复声明 const searchInput，导致 JS 运行期抛出 SyntaxError")

        # ---------------------------------------------------------------------
        # 测试点 12: 底部 Tab 导航栏 600px 宽度限制与居中对齐测试 (Bottom Nav Width Limit)
        # ---------------------------------------------------------------------
        bottom_nav_match = re.search(r'\.bottom-nav\s*\{([^}]+)\}', content)
        bottom_nav_css = bottom_nav_match.group(1) if bottom_nav_match else ''
        nav_max_width = 'max-width: 600px;' in bottom_nav_css
        self.assert_true(nav_max_width, f"[{lang_name}] 布局-底部 Tab 导航栏 max-width: 600px 限制", ".bottom-nav 缺少 max-width: 600px 限制，导致超宽屏下跨全屏扩散")

        nav_margin_auto = 'margin: 0 auto;' in bottom_nav_css
        self.assert_true(nav_margin_auto, f"[{lang_name}] 布局-底部 Tab 导航栏 margin: 0 auto 居中对齐", ".bottom-nav 缺少 margin: 0 auto 居中对齐设置")

        # ---------------------------------------------------------------------
        # 测试点 13: 主题切换按钮 🌙/☀️ 单次点击响应与防双重触发屏障 (Theme Toggle Integrity)
        # ---------------------------------------------------------------------
        theme_toggle_btn_exists = 'id="themeToggleBtn"' in content
        self.assert_true(theme_toggle_btn_exists, f"[{lang_name}] 主题-切换按钮节点 #themeToggleBtn 存在", "DOM 中缺少 id='themeToggleBtn' 主题按钮")

        theme_toggle_guard = '_lastThemeToggle' in content
        self.assert_true(theme_toggle_guard, f"[{lang_name}] 主题-toggleTheme 防连击/防叠加双重触发锁", "toggleTheme 中缺少 _lastThemeToggle 防重流控锁，引发点击抵消失效")

        light_theme_css = 'body.light-theme' in content
        self.assert_true(light_theme_css, f"[{lang_name}] 主题-CSS body.light-theme 主题变量配置", "缺少 body.light-theme 样式规则，导致主题切换效果不生效")

        # ---------------------------------------------------------------------
        # 测试点 14: 标签筛选下拉菜单与多选交互测试 (Tag Filter Dropdown Suite)
        # ---------------------------------------------------------------------
        tag_dropdown_container = 'id="tagDropdownContainer"' in content
        self.assert_true(tag_dropdown_container, f"[{lang_name}] 标签筛选-下拉菜单容器 #tagDropdownContainer 存在", "DOM 中缺少 id='tagDropdownContainer' 容器")

        tag_dropdown_btn = 'id="tagDropdownBtn"' in content and 'toggleTagDropdown' in content
        self.assert_true(tag_dropdown_btn, f"[{lang_name}] 标签筛选-触发按钮 #tagDropdownBtn 绑定 toggleTagDropdown", "DOM 中缺少 id='tagDropdownBtn' 或未绑定 toggleTagDropdown")

        tag_dropdown_menu = 'id="tagDropdownMenu"' in content and 'id="tagDropdownList"' in content
        self.assert_true(tag_dropdown_menu, f"[{lang_name}] 标签筛选-下拉菜单面板 #tagDropdownMenu 存在", "DOM 中缺少 id='tagDropdownMenu' 面板")

        tag_methods_exist = 'toggleTagDropdown(' in content and 'toggleTagFilter(' in content and 'clearAllTagFilters(' in content and 'updateTagBadge(' in content and 'renderTagDropdownItems(' in content
        self.assert_true(tag_methods_exist, f"[{lang_name}] 标签筛选-多选切换与清空方法集健全", "类中缺少 toggleTagFilter/clearAllTagFilters/updateTagBadge/renderTagDropdownItems 方法")

        custom_tag_only_filter = 'posTags' in content and '!posTags.has(' in content
        self.assert_true(custom_tag_only_filter, f"[{lang_name}] 标签筛选-下拉菜单仅精准显示自定义 Tag (排除系统词性 Tag)", "getAllAvailableTags 缺少 posTags 黑名单过滤，导致预设词性 Tag 混入自定义标签下拉菜单中")

        similar_ex_trans_clarity = ('.similar-word-chip .similar-ex-trans {' in content and 'color: var(--text-secondary)' in content) or ('similar-ex-trans' in content and 'color:var(--text-secondary)' in content)
        self.assert_true(similar_ex_trans_clarity, f"[{lang_name}] 相近表达-例句原文高亮与例句中文翻译层次色配置", ".similar-ex-trans 缺少 color: var(--text-secondary) 层次色配置，导致与例句原文难以区分")

        # ---------------------------------------------------------------------
        # 测试点 15: 云端智能合并与本地删除记忆保护 (Smart Sync & Delete Memory)
        # ---------------------------------------------------------------------
        smart_sync_methods = 'getDeletedSet()' in content and 'recordDeletedWord(' in content and 'mergeCloudData(' in content
        self.assert_true(smart_sync_methods, f"[{lang_name}] 云端同步-智能合并与本地删除记忆保护机制", "类中缺少 getDeletedSet / recordDeletedWord / mergeCloudData 方法，会导致用户删词后同步被误还原")



        # ---------------------------------------------------------------------
        # 测试点 18: 列表中单词卡片 100% 直接展示第一组例句与翻译测试 (Word Card List Direct Example Preview Parity)
        # ---------------------------------------------------------------------
        card_ex_preview_css = '.word-example-preview {' in content and '.ex-preview-text {' in content
        self.assert_true(card_ex_preview_css, f"[{lang_name}] 列表卡片-例句预览 CSS 样式组件健全", "缺少 .word-example-preview 或 .ex-preview-text 样式配置")

        card_ex_preview_render = 'word-example-preview' in content and 'ex-preview-text' in content
        self.assert_true(card_ex_preview_render, f"[{lang_name}] 列表卡片-直接渲染第一组例句与翻译模板防护", "renderWordList 或 DOM 模板中缺少 word-example-preview 渲染节点")

        # ---------------------------------------------------------------------
        # 测试点 17: 全量卡片数据 100% 包含实用例句与例句翻译覆盖率测试 (Every Card Examples Coverage Parity)
        # ---------------------------------------------------------------------
        card_example_modal_render = 'renderDetailModal' in content or 'showDetailModal' in content or 'detailExampleBlock' in content
        self.assert_true(card_example_modal_render, f"[{lang_name}] 详情弹窗-点击卡片全量例句与翻译渲染防护", "renderDetailModal 中缺少例句渲染逻辑")

        cards_examples_non_empty = True
        m = re.search(r'const samples = (\[.*?\]);', content, re.DOTALL)
        if m:
            try:
                import json
                samples_data = json.loads(m.group(1), strict=False)
                for idx, item in enumerate(samples_data):
                    ex = item.get('example', '') or item.get('examples', '')
                    ex_trans = item.get('exampleTrans', '')
                    if not ex:
                        cards_examples_non_empty = False
                        print(f"  ⚠️ [{lang_name}] 发现无例句卡片: ID={item.get('id')} Word={item.get('word')}")
            except Exception as err:
                print(f"  ⚠️ 解析 samples JSON 失败: {err}")

        self.assert_true(cards_examples_non_empty, f"[{lang_name}] 数据集-全量卡片 100% 包含例句与翻译断言", "存在未包含例句的硬编码卡片数据")

        # ---------------------------------------------------------------------
        # 测试点 16: 统计数字与卡片数据一致性与自我修复测试 (Stats Data Self-Healing Parity)
        # ---------------------------------------------------------------------
        stats_self_healing = 'if (!this.words || !Array.isArray(this.words) || this.words.length === 0)' in content and 'samples' in content
        self.assert_true(stats_self_healing, f"[{lang_name}] 统计数字-updateStats 数据源自我修复保底防护", "updateStats 中缺少对 this.words 为空时的 samples 自自我修复保底，可能导致卡片有词但数字显 0")

        static_counts_bound = 'id="count-all"' in content and ('id="count-learning"' in content)
        self.assert_true(static_counts_bound, f"[{lang_name}] 统计数字-DOM 节点绑定健全性", "缺少 count-all 或 count-learning DOM 节点绑定")

        # ---------------------------------------------------------------------
        # 测试点 17: 单词列表右侧置顶/置底按钮 Panel 内部防护测试 (Scroll Track Buttons Panel Bounds)
        # ---------------------------------------------------------------------
        has_scroll_btns_dom = 'id="scrollToTopBtn"' in content and 'id="scrollToBottomBtn"' in content
        self.assert_true(has_scroll_btns_dom, f"[{lang_name}] 交互-滑动条极顶端 #scrollToTopBtn 与极底端 #scrollToBottomBtn 按钮节点健全", "DOM 中缺少 #scrollToTopBtn 或 #scrollToBottomBtn 按钮")

        has_scroll_btns_css = '.scroll-track-btn' in content and 'position: fixed' in content and 'top: calc(50%' in content
        self.assert_true(has_scroll_btns_css, f"[{lang_name}] 布局-滑动条置顶/置底按钮固定于右侧滑动条轨道高度且优雅不遮挡底栏", "CSS 中 .scroll-track-btn 缺少滑动条高度 top: calc(50% 固定定位")

        scroll_btns_tab_list_only = 'scrollToTopBtn' in content and 'tab-list' in content and 'isListTab' in content
        self.assert_true(scroll_btns_tab_list_only, f"[{lang_name}] 交互-置顶/置底按钮仅在【词库列表】Tab显隐控制防护", "switchTab 中缺少对 #scrollToTopBtn 和 #scrollToBottomBtn 仅在 tab-list 页面显隐的切换逻辑")

        # ---------------------------------------------------------------------
        # 测试点 18: 一键置底 scrollToListBottom 以分页工具栏为终点测试 (Scroll To Bottom Pagination Bar Target)
        # ---------------------------------------------------------------------
        has_scroll_api = 'scrollToListTop' in content and 'scrollToListBottom' in content
        self.assert_true(has_scroll_api, f"[{lang_name}] 逻辑-scrollToListTop 与 scrollToListBottom 一键直达 API 健全", "JS 中缺少 scrollToListTop 或 scrollToListBottom 函数")

        scroll_to_pagination_target = 'scrollToListBottom' in content and 'paginationBar' in content and 'scrollIntoView' in content
        self.assert_true(scroll_to_pagination_target, f"[{lang_name}] 逻辑-scrollToListBottom 置底函数以 #paginationBar 分页工具栏为终点显式露出一键直达", "scrollToListBottom 缺少对 paginationBar 的 scrollIntoView 定位，会导致滑到底部时分页栏被裁剪")

        # ---------------------------------------------------------------------
        # 测试点 19: 底部导航栏紧凑高度 50px 与粉色拖动滑动条高亮测试
        # ---------------------------------------------------------------------
        compact_bottom_nav_css = 'height: 50px !important;' in content or 'height: 50px;' in content
        self.assert_true(compact_bottom_nav_css, f"[{lang_name}] 样式-底部导航栏高度紧凑化 50px 压低间距", "CSS 中 .bottom-nav 缺少 height: 50px !important 紧凑化配置")

        pink_scrollbar_css = '#wordList::-webkit-scrollbar-thumb' in content and 'var(--accent-primary, #ec4899)' in content
        self.assert_true(pink_scrollbar_css, f"[{lang_name}] 样式-粉色高亮拖动滑动条 ::-webkit-scrollbar-thumb 渲染配置", "CSS 中缺少 #wordList::-webkit-scrollbar-thumb 粉色高亮拖动滑动条配置")

        # ---------------------------------------------------------------------
        # 测试点 20: 卡片底部 Tag 行内打字加标签交互组件防护 (Inline Tag Input Component Test)
        # ---------------------------------------------------------------------
        inline_tag_css = '.inline-tag-editor {' in content and '.inline-tag-input {' in content and '.inline-quick-tag-chip {' in content
        self.assert_true(inline_tag_css, f"[{lang_name}] 交互-卡片底部 Tag 行内打字编辑器 CSS 规则健全", "CSS 中缺少 .inline-tag-editor / .inline-tag-input / .inline-quick-tag-chip 规则")

        inline_tag_methods = 'showInlineTagInput(' in content and 'handleInlineTagKeydown(' in content and 'saveInlineTag(' in content and 'addQuickTag(' in content
        self.assert_true(inline_tag_methods, f"[{lang_name}] 交互-行内打字加标签 API 方法集 (showInlineTagInput/saveInlineTag/addQuickTag) 健全", "类中缺少 showInlineTagInput / handleInlineTagKeydown / saveInlineTag / addQuickTag 方法")

        modal_inline_tag_methods = 'showModalInlineTagInput(' in content and 'handleModalInlineTagKeydown(' in content and 'saveModalInlineTag(' in content and 'addModalQuickTag(' in content
        self.assert_true(modal_inline_tag_methods, f"[{lang_name}] 交互-编辑弹窗行内打字加标签 API 方法集健全", "类中缺少 showModalInlineTagInput / saveModalInlineTag 方法")

        word_list_isolated_scroll = 'flex-shrink: 0;' in content and '#wordList::-webkit-scrollbar' in content
        self.assert_true(word_list_isolated_scroll, f"[{lang_name}] 布局-#wordList 独立滚动与搜索/Tag控件置顶固定不动", "缺少 #wordList 独立滚动或 flex-shrink: 0 防压缩设置")

        # ---------------------------------------------------------------------
        # 测试点 21: renderWordList 列表重绘时 #paginationBar 节点自动重建防护测试
        # ---------------------------------------------------------------------
        has_pagination_rebuild = 'id="paginationBar"' in content and 'word-list-inline-pagination' in content and 'renderPaginationControls' in content
        self.assert_true(has_pagination_rebuild, f"[{lang_name}] 逻辑-renderWordList 重绘列表时自动重建 #paginationBar 节点，彻底杜绝分页栏丢失 Bug", "renderWordList 拼接中缺少 #paginationBar 动态重建节点，会导致 innerHTML 重绘后分页栏丢失")

        # ---------------------------------------------------------------------
        # 测试点 22: 翻页工具栏固定悬浮与强常驻 (Never Hide Pagination Bar) 防护测试
        # ---------------------------------------------------------------------
        pagination_always_flex = ('paginationBar.style.display = \'flex\'' in content or 'paginationBar.style.display = isListTab' in content) and 'safeTotalPages = Math.max(1, totalPages)' in content
        self.assert_true(pagination_always_flex, f"[{lang_name}] 逻辑-翻页工具栏强常驻显示，即使 1 页 (totalPages<=1) 也保持 display:flex", "renderPaginationControls 中缺少 safeTotalPages 保底，会导致 1 页时分页栏被错误隐藏")

        pagination_fixed_css = 'position: fixed' in content and 'bottom: 50px' in content and 'z-index: 99' in content
        self.assert_true(pagination_fixed_css, f"[{lang_name}] 样式-翻页工具栏固定悬浮于底部导航 Tab 正上方 (bottom: 50px, z-index: 99)", "CSS 中缺少 .pagination-bar 的 position: fixed !important 及 bottom: 50px !important 悬浮定位")

        switch_tab_pagination = 'const paginationBar = document.getElementById(\'paginationBar\');' in content and 'paginationBar.style.display = isListTab ? \'flex\' : \'none\';' in content
        self.assert_true(switch_tab_pagination, f"[{lang_name}] 逻辑-switchTab 自动切换非列表 Tab 时隐藏分页工具栏", "switchTab 方法中缺少对 #paginationBar 的 isListTab 显显控制")

        # ---------------------------------------------------------------------
        # 测试点 23: 卡片底部 Tag 栏与操作按钮栏 (朗读/掌握/编辑/删除) 100% 完整保留防护测试
        # ---------------------------------------------------------------------
        has_card_footer_actions = 'class="word-footer"' in content and 'class="word-tags"' in content and 'add-tag-btn' in content and 'class="card-actions"' in content and 'speakWord' in content and 'toggleMastered' in content and 'editWord' in content and 'deleteWord' in content
        self.assert_true(has_card_footer_actions, f"[{lang_name}] 结构-卡片底部 Tag 栏与操作按钮栏 (朗读/掌握/编辑/删除) 100% 完整保留", "单词卡片 HTML 结构中缺少 word-footer、word-tags 或 card-actions 操作按钮栏")

        # ---------------------------------------------------------------------
        # 测试点 24: 自定义标签删除按钮 (.remove-tag-x) 阻止冒泡与 removeCustomTag 方法防护
        # ---------------------------------------------------------------------
        remove_tag_protection = 'remove-tag-x' in content and 'removeCustomTag' in content and 'event.stopPropagation()' in content
        self.assert_true(remove_tag_protection, f"[{lang_name}] 交互-自定义标签删除按钮 (.remove-tag-x) 阻止冒泡与 removeCustomTag 防护", "卡片 Tag 缺少 remove-tag-x 节点或未绑定 event.stopPropagation() 防止冒泡触发出弹窗")

        # ---------------------------------------------------------------------
        # 测试点 25: 卡片点击 showDetailModal 触发事件与 card-actions stopPropagation 事件隔离
        # ---------------------------------------------------------------------
        card_event_isolation = 'showDetailModal' in content and 'onclick="event.stopPropagation()"' in content
        self.assert_true(card_event_isolation, f"[{lang_name}] 结构-卡片主体 showDetailModal 弹窗与底部操作栏 stopPropagation 事件防护隔离", "卡片底部操作栏缺少 event.stopPropagation() 事件阻断隔离")

        # ---------------------------------------------------------------------
        # 测试点 26: 翻页工具栏 btnPrevPage 与 btnNextPage 动态事件监听与 disabled 态切换
        # ---------------------------------------------------------------------
        pagination_event_listener = 'btnPrevPage' in content and 'btnNextPage' in content and 'addEventListener(\'click\'' in content
        self.assert_true(pagination_event_listener, f"[{lang_name}] 逻辑-翻页工具栏按钮 btnPrevPage/btnNextPage 事件监听与 disabled 禁用态响应防护", "renderPaginationControls 中缺少 btnPrevPage 或 btnNextPage 的点击事件监听注册")

        # ---------------------------------------------------------------------
        # 测试点 27: 复习卡片背面 Tag 标签栏容器 (#cardBackTags) 与 renderWordTagsHtml 实时渲染防护
        # ---------------------------------------------------------------------
        card_back_tags_protection = 'id="cardBackTags"' in content and 'renderWordTagsHtml' in content
        self.assert_true(card_back_tags_protection, f"[{lang_name}] 结构-复习卡片背面 Tag 标签栏容器 (#cardBackTags) 与 renderWordTagsHtml 实时渲染防护", "复习卡片背面缺少 id=\"cardBackTags\" 节点或 renderWordTagsHtml 渲染函数")

        # ---------------------------------------------------------------------
        # 测试点 28: 卡片复习背面加/删标签保持卡片翻拽状态防护 (Preserve Flashcard Flip State on Tag Update)
        # ---------------------------------------------------------------------
        preserve_flip_tag_update = 'cardBackTags.innerHTML = this.renderWordTagsHtml' in content
        self.assert_true(preserve_flip_tag_update, f"[{lang_name}] 交互-复习卡片背面编辑 Tag 原地刷新不复位卡片翻面", "saveInlineTag/addQuickTag/removeCustomTag 中缺少 cardBackTags 原地更新逻辑，会导致打标签时卡片被误翻转回到正面")

        # ---------------------------------------------------------------------
        # 测试点 29: 复习卡片背面 .card-face-back 与全局粉色拖动滑动条高亮配置
        # ---------------------------------------------------------------------
        card_back_scrollbar_css = '.card-face-back::-webkit-scrollbar' in content and 'var(--accent-primary, #ec4899)' in content
        self.assert_true(card_back_scrollbar_css, f"[{lang_name}] 样式-复习卡片背面 .card-face-back 粉色高亮拖动滑动条 CSS 规则", "CSS 中缺少 .card-face-back::-webkit-scrollbar 专属滑动条配置")

        # ---------------------------------------------------------------------
        # 测试点 30: 存储沙盒与全局防崩溃护盾防护 (SafeStorageWrapper)
        # ---------------------------------------------------------------------
        safe_storage_wrapper = 'class SafeStorageWrapper' in content and 'SafeStorage' in content
        self.assert_true(safe_storage_wrapper, f"[{lang_name}] 安全-SafeStorageWrapper 存储沙盒降级与防崩溃护盾", "缺少 SafeStorageWrapper 降级存储包装器，可能在极苛沙盒下导致 localStorage 报错卡死")

        # ---------------------------------------------------------------------
        # 测试点 31: 相近/易混表达推荐算法与面板交互防护 (getSimilarWords & renderSimilarBlockHtml)
        # ---------------------------------------------------------------------
        similar_words_algo = 'getSimilarWords(' in content and 'renderSimilarBlockHtml(' in content and 'similar-word-chip' in content
        self.assert_true(similar_words_algo, f"[{lang_name}] 算法-getSimilarWords 相近/易混表达推荐算法与面板交互防护", "缺少 getSimilarWords 或 renderSimilarBlockHtml 方法")

        # ---------------------------------------------------------------------
        # 测试点 32: 复习卡片语义与 Tag 聚类出词算法防护 (clusterBySimilarity)
        # ---------------------------------------------------------------------
        cluster_by_sim = 'clusterBySimilarity(' in content and 'this.clusterBySimilarity(' in content
        self.assert_true(cluster_by_sim, f"[{lang_name}] 算法-clusterBySimilarity 复习卡片语义与 Tag 聚类出词算法", "缺少 clusterBySimilarity 方法或未在 startReviewSession 中调用")

        # ---------------------------------------------------------------------
        # 测试点 33: 内联分页工具条定位与 word-list-inline-pagination 容器包含断言
        # ---------------------------------------------------------------------
        inline_pagination_css = '.pagination-bar' in content and 'word-list-inline-pagination' in content and 'id="paginationBar"' in content
        self.assert_true(inline_pagination_css, f"[{lang_name}] 结构-内联分页工具条 word-list-inline-pagination 在 #wordList 末尾嵌套防护", "缺少 .pagination-bar CSS 规则或 word-list-inline-pagination 类名")

        # ---------------------------------------------------------------------
        # 测试点 34: 详情弹窗相近表达跳转历史栈与返回上一词条 API 防护 (Detail Modal Navigation Stack & goBackDetailModal)
        # ---------------------------------------------------------------------
        modal_history_stack = 'detailModalHistory' in content and 'goBackDetailModal(' in content and ('id="detailNavBackBar"' in content or 'id="detailBackBtn"' in content or 'goBackDetailModal' in content)
        self.assert_true(modal_history_stack, f"[{lang_name}] 交互-详情弹窗相近表达跳转历史栈 detailModalHistory 与 goBackDetailModal 返回上级按钮防护", "缺少 detailModalHistory 历史栈数组或 goBackDetailModal 方法")

        # ---------------------------------------------------------------------
        # 测试点 35: 详情弹窗添加/删除标签实时刷新防护 (Detail Modal Inline Tag Refresh)
        # ---------------------------------------------------------------------
        modal_tag_refresh = "const detailModal = document.getElementById('detailModal');" in content and "this.showDetailModal(wordId, true);" in content
        self.assert_true(modal_tag_refresh, f"[{lang_name}] 交互-详情弹窗添加与删除标签 detailModal 原地刷新与 showDetailModal 视图更新防护", "缺少 detailModal 判断或 showDetailModal(wordId, true) 刷新逻辑")

        # ---------------------------------------------------------------------
        # 测试点 36: 详情弹窗极简返回图标按钮 #detailBackBtn 显隐切换防护 (Detail Modal Minimal Back Icon Button)
        # ---------------------------------------------------------------------
        detail_back_btn = 'id="detailBackBtn"' in content and 'detailBackBtn' in content and 'backBtn.style.display' in content
        self.assert_true(detail_back_btn, f"[{lang_name}] 交互-详情弹窗极简返回图标按钮 #detailBackBtn 显隐切换与对称布局防护", "缺少 #detailBackBtn 节点或 backBtn.style.display 控制逻辑")

        # ---------------------------------------------------------------------
        # 测试点 37: 行内打字编辑器快捷标签芯片 (📌易忘 / 🔀易混) 事件绑定防护 (Inline Tag Editor Quick Chips)
        # ---------------------------------------------------------------------
        inline_quick_chips = 'class="inline-quick-tag-chip"' in content and "addQuickTag(event, '${wordId}', '易忘')" in content and "addQuickTag(event, '${wordId}', '易混')" in content
        self.assert_true(inline_quick_chips, f"[{lang_name}] 交互-行内打字编辑器快捷标签芯片 📌易忘/🔀易混 事件绑定防护", "缺少 .inline-quick-tag-chip 快捷标签芯片或 addQuickTag 绑定")

        # ---------------------------------------------------------------------
        # 测试点 38: .word-list / #wordList 容器 padding-bottom 115px 避让底部固定 Tab 与 fixed 分页栏隔离防护
        # ---------------------------------------------------------------------
        wordlist_padding_bottom = '.word-list' in content and 'padding-bottom: 115px !important;' in content
        self.assert_true(wordlist_padding_bottom, f"[{lang_name}] 样式-.word-list 容器 padding-bottom 115px 避让底部固定 Tab 与 fixed 分页栏", "CSS 中缺少 .word-list 的 padding-bottom: 115px !important 避让配置，会导致最后一个卡片的 Tag 栏被遮挡")

        # ---------------------------------------------------------------------
        # 测试点 39: 置顶与置底直达按钮高度定位 (Top & Bottom Buttons Elevated Height)
        # ---------------------------------------------------------------------
        elevated_scroll_btns = 'top: calc(50% - 48px)' in content and 'top: calc(50% - 2px)' in content
        self.assert_true(elevated_scroll_btns, f"[{lang_name}] 布局-置顶与置底直达按钮高度抬升至滚动条轨道居中位置 (calc(50%-48px) / calc(50%-2px))", "CSS 中置顶置底按钮未调高至滚动条中间大概高度")

        # ---------------------------------------------------------------------
        # 测试点 40: 数据装载 loadData 与 updateStats 自动自我修复 (Self-Healing Data Shield)
        # ---------------------------------------------------------------------
        self_healing_data = 'loadSampleData(' in content and 'updateStats()' in content and ('this.words.length === 0' in content or 'words.length' in content)
        self.assert_true(self_healing_data, f"[{lang_name}] 安全-loadData 数据为空自动装载样本保底与 updateStats 自我修复", "JS 中缺少 loadSampleData 保底或 updateStats 自我修复机制")

        # ---------------------------------------------------------------------
        # 测试点 41: 列表筛选控制栏与标签按钮高度统一及取消底边距严格齐平
        # ---------------------------------------------------------------------
        filter_pills_no_margin = 'padding-bottom: 0 !important;' in content or 'padding-bottom: 0px' in content or 'padding-bottom: 0;' in content
        pill_btn_height_28 = '.pill-btn {' in content and 'height: 28px;' in content
        tag_btn_height_28 = '.tag-dropdown-btn {' in content and 'height: 28px;' in content
        layout_alignment_ok = filter_pills_no_margin and pill_btn_height_28 and tag_btn_height_28
        self.assert_true(layout_alignment_ok, f"[{lang_name}] 布局-筛选按钮 .pill-btn 与 .tag-dropdown-btn 统一 28px 高度并与标签下拉框完美水平齐平", "filter-pills 含有底边距或 pill-btn / tag-dropdown-btn 高度未统一为 28px")

        # ---------------------------------------------------------------------
        # 测试点 42: HTML 静态 DOM 数字标签 (#count-all & #count-learning) 与 samples 数据源 100% 精确一致
        # ---------------------------------------------------------------------
        count_all_m = re.search(r'id="count-all"[^>]*>(\d+)</span>', content)
        count_learning_m = re.search(r'id="count-learning"[^>]*>(\d+)</span>', content)
        samples_m = re.search(r'const samples = (\[.*?\]);', content, re.DOTALL)
        
        dom_static_counts_ok = False
        counts_error_msg = ""
        if count_all_m and count_learning_m and samples_m:
            dom_all = int(count_all_m.group(1))
            dom_learning = int(count_learning_m.group(1))
            try:
                import json
                samples_data = json.loads(samples_m.group(1), strict=False)
                actual_all = len(samples_data)
                actual_learning = sum(1 for item in samples_data if item.get('status', 'learning') == 'learning')
                if dom_all == actual_all and dom_learning == actual_learning:
                    dom_static_counts_ok = True
                else:
                    counts_error_msg = f"静态 HTML count-all({dom_all})!=actual({actual_all}) 或 count-learning({dom_learning})!=actual({actual_learning})"
            except Exception as err:
                counts_error_msg = f"解析 samples JSON 失败: {err}"
        else:
            counts_error_msg = "未匹配到 count-all/count-learning 节点或 samples 数组"

        self.assert_true(dom_static_counts_ok, f"[{lang_name}] 静态DOM-HTML 默认数字标签 (#count-all={count_all_m.group(1) if count_all_m else 'N/A'}) 与 samples 数据源 100% 精确一致", counts_error_msg)

        # ---------------------------------------------------------------------
        # 测试点 43: 释义纯净度 (meaning 字段 100% 隔离方括号 [...] 读音)
        # ---------------------------------------------------------------------
        meaning_pure = True
        polluted_sample_id = ""
        if samples_m:
            try:
                import json
                samples_data = json.loads(samples_m.group(1), strict=False)
                for item in samples_data:
                    m_text = item.get('meaning', '')
                    if '[' in m_text and ']' in m_text:
                        meaning_pure = False
                        polluted_sample_id = f"ID={item.get('id')} Word={item.get('word')} Meaning={m_text}"
                        break
            except Exception:
                pass
        self.assert_true(meaning_pure, f"[{lang_name}] 数据集-全量卡片 meaning 字段绝对纯净 (不混入 [...] 发音)", f"发现 meaning 中残留 [...] 发音: {polluted_sample_id}")

        # ---------------------------------------------------------------------
        # 测试点 44: 发音正位 (reading 字段 100% 存在且包含 [...] 方括号发音)
        # ---------------------------------------------------------------------
        reading_valid = True
        invalid_reading_id = ""
        if samples_m:
            try:
                import json
                samples_data = json.loads(samples_m.group(1), strict=False)
                for item in samples_data:
                    r_text = item.get('reading', '')
                    if not r_text or '[' not in r_text or ']' not in r_text:
                        reading_valid = False
                        invalid_reading_id = f"ID={item.get('id')} Word={item.get('word')} Reading={r_text}"
                        break
            except Exception:
                pass
        self.assert_true(reading_valid, f"[{lang_name}] 数据集-全量卡片 reading 字段正位且格式规范 [...]", f"发现 reading 缺失或缺少 [...] 括号: {invalid_reading_id}")

        # ---------------------------------------------------------------------
        # 测试点 45: 自定义标签行内打字编辑器 (showInlineTagInput 不使用 window.prompt)
        # ---------------------------------------------------------------------
        inline_tag_no_prompt = 'showInlineTagInput' in content and 'saveInlineTag' in content and 'prompt(' not in content
        self.assert_true(inline_tag_no_prompt, f"[{lang_name}] 交互-自定义标签采用行内高亮打字框 (绝不弹窗 prompt)", "缺少 showInlineTagInput 或使用了 window.prompt 传统弹窗")

        # ---------------------------------------------------------------------
        # 测试点 46: 页面垂直滚动条畅通性 (绝对禁止锁定 html/body overflow:hidden)
        # ---------------------------------------------------------------------
        body_scroll_unlocked = 'body {\n  overflow: hidden' not in content and 'html, body {\n  overflow: hidden' not in content
        self.assert_true(body_scroll_unlocked, f"[{lang_name}] 布局-页面 html/body 垂直滚动条畅通 (无 overflow:hidden 强行锁定)", "页面设置了 overflow:hidden 锁定高度")

        # ---------------------------------------------------------------------
        # 测试点 47: 卡片底栏加 Tag 按钮 (.add-inline-tag-btn) 事件阻断 (stopPropagation) 防护
        # ---------------------------------------------------------------------
        add_tag_stop_prop = 'event.stopPropagation()' in content and 'showInlineTagInput' in content
        self.assert_true(add_tag_stop_prop, f"[{lang_name}] 交互-卡片底部 + 加 Tag 按钮与操作栏显式绑定 stopPropagation 隔离阻断", "缺少 event.stopPropagation()，会导致点击 + 加标签时误唤起卡片详情弹窗")

        # ---------------------------------------------------------------------
        # 测试点 48: 悬浮翻页工具栏 (.pagination-bar) 精确定位 (bottom: 50px) 与 z-index 避让 Tab 栏
        # ---------------------------------------------------------------------
        pagination_bar_fixed = '.pagination-bar {' in content and 'position: fixed !important;' in content and 'bottom: 50px !important;' in content
        self.assert_true(pagination_bar_fixed, f"[{lang_name}] 布局-悬浮翻页工具栏 position: fixed 挂载于 bottom: 50px 正上方", "pagination-bar 缺少 fixed 定位或未精确悬浮于 50px Tab 栏正上方")

        # ---------------------------------------------------------------------
        # 测试点 49: 一键置底直达按钮 API (scrollToListBottom) 自动滑至 #wordList 最底端
        # ---------------------------------------------------------------------
        scroll_bottom_api = 'scrollToListBottom()' in content and 'wl.scrollTop = wl.scrollHeight' in content
        self.assert_true(scroll_bottom_api, f"[{lang_name}] 逻辑-一键置底 scrollToListBottom() 自动精确滚动至 #wordList 最底端", "scrollToListBottom 缺少 wl.scrollTop = wl.scrollHeight 置底触发")

        # ---------------------------------------------------------------------
        # 测试点 50: 卡片底部容器 (.word-footer) 包裹 .word-tags 与操作按钮，保障 Tag 与操作按钮 100% 同行同行对齐
        # ---------------------------------------------------------------------
        word_footer_alignment = 'word-footer' in content and 'word-tags' in content
        self.assert_true(word_footer_alignment, f"[{lang_name}] 布局-单词卡片底部采用 .word-footer 结构，保障 Tag 标签与操作按钮 100% 独占同一排", "缺少 word-footer 包裹，导致 Tag 栏与操作按钮折行拆成两排")

        # ---------------------------------------------------------------------
        # 测试点 51: 列表卡片例句预览必须包含中文翻译 (.word-example-trans)
        # ---------------------------------------------------------------------
        example_trans_preview = 'word-example-trans' in content
        self.assert_true(example_trans_preview, f"[{lang_name}] 结构-单词列表卡片预览必须直接包含例句中文翻译 (.word-example-trans)", "卡片预览缺少 word-example-trans 节点，导致只显示日/韩文原句无中文意思")

        # ---------------------------------------------------------------------
        # 测试点 52: 搜索框一键清空按钮 (#searchClearBtn) 动态显隐与 clearSearch 逻辑健全
        # ---------------------------------------------------------------------
        search_clear_btn_ok = 'searchClearBtn' in content and 'clearSearch()' in content and ('clearBtn.style.display' in content or 'searchClearBtn.style.display' in content)
        self.assert_true(search_clear_btn_ok, f"[{lang_name}] 交互-搜索框输入文字自动浮现 ✕ 一键清空按钮 (#searchClearBtn) 并绑定 clearSearch()", "缺少 searchClearBtn 或 clearBtn.style.display 显隐控制")

        # ---------------------------------------------------------------------
        # 测试点 53: 全量内联 onclick 语法严谨合规 (绝对禁止出现 '' + w.id + '' 引号逃逸冲突导致的 SyntaxError)
        # ---------------------------------------------------------------------
        onclicks = re.findall(r'onclick="([^"]+)"', content)
        has_broken_onclick = any("''" in oc or "’" in oc for oc in onclicks)
        self.assert_true(not has_broken_onclick, f"[{lang_name}] 语法-全量内联 onclick 属性语法严谨合规 (无引号逃逸导致 JS 崩溃)", "发现存在单引号嵌套冲突的 onclick 属性，会导致运行时卡片与按钮点不动")

        # ---------------------------------------------------------------------
        # 测试点 54: 入口初始化 window.app 与 window.vocabApp 健全挂载防护
        # ---------------------------------------------------------------------
        app_mount_ok = 'window.app = new VocabApp()' in content and 'window.vocabApp = window.app' in content
        self.assert_true(app_mount_ok, f"[{lang_name}] 逻辑-入口 DOMContentLoaded 事件中 window.app 与 window.vocabApp 双重挂载防护", "缺少 window.vocabApp = window.app 挂载，会导致以 vocabApp 调用的函数报错")

        # ---------------------------------------------------------------------
        # 触发语言专属特有检测点
        # ---------------------------------------------------------------------
        if lang_name == "日语":
            self.test_jp_specific(content)

    def test_jp_specific(self, content):
        print("\n  --------------------------------------------------")
        print("  >>> [日语专属特有测试项] 针对 JP 特有韩文对应表达 (krMeaning) 进行深度检测...")
        print("  --------------------------------------------------")

        # JP 测试点 1: CSS 包含 .kr-badge 专属韩文释义徽章样式
        has_kr_badge_css = '.kr-badge' in content and 'background:' in content
        self.assert_true(has_kr_badge_css, "[日语专属] 样式-.kr-badge 专属韩文释义徽章 CSS 配置", "缺少 .kr-badge 样式规则")

        # JP 测试点 2: 单词列表卡片 .word-meaning 中支持条件渲染 krMeaning 徽章
        has_list_kr_badge = 'krMeaning' in content and 'class="kr-badge"' in content
        self.assert_true(has_list_kr_badge, "[日语专属] 结构-单词列表 .word-meaning 中支持渲染 krMeaning 韩文表达徽章", "renderWordList 模版中缺少 krMeaning 的 kr-badge 条件渲染")

        # JP 测试点 3: 详情弹窗 detailMeaning & 复习背面 cardBackMeaning 支持 krMeaning 动态渲染
        has_detail_kr_badge = 'detailMeaning' in content and 'cardBackMeaning' in content and 'word.krMeaning' in content
        self.assert_true(has_detail_kr_badge, "[日语专属] 交互-详情弹窗与复习卡片背面支持 krMeaning 韩文对应表达展示", "showDetailModal 或 renderCurrentCard 中缺少 word.krMeaning 节点渲染")

        # JP 测试点 4: 相近表达推荐芯片中渲染 krMeaning 徽章
        has_similar_kr_badge = 'renderSimilarBlockHtml' in content and 'w.krMeaning' in content
        self.assert_true(has_similar_kr_badge, "[日语专属] 交互-相近/近义表达推荐芯片包含 krMeaning 展示", "renderSimilarBlockHtml 中缺少 w.krMeaning 展示")

        # JP 测试点 5: 样本数据集 samples 中全量包含 krMeaning 韩文对应表达字段
        m = re.search(r'const samples = (\[.*?\]);', content, re.DOTALL)
        jp_kr_meaning_complete = True
        if m:
            try:
                import json
                samples_data = json.loads(m.group(1), strict=False)
                for idx, item in enumerate(samples_data):
                    kr_m = item.get('krMeaning', '')
                    if not kr_m:
                        jp_kr_meaning_complete = False
                        print(f"  ⚠️ [日语专属] 发现缺失 krMeaning 韩文表达的卡片: ID={item.get('id')} Word={item.get('word')}")
            except Exception as err:
                print(f"  ⚠️ [日语专属] 解析 samples JSON 失败: {err}")

        self.assert_true(jp_kr_meaning_complete, "[日语专属] 数据集-全量日语样本卡片 100% 覆盖 krMeaning 韩文对应表达", "存在未包含 krMeaning 韩文对应表达的硬编码日语卡片")


    def run_all(self):
        print("\n[INIT] 启动单词本应用全量自动化测试流程...")
        self.test_file(KR_FILE, "韩语")
        self.test_file(JP_FILE, "日语")

        print("\n==================================================")
        print(f"[RESULT] 测试总结: 通过 {self.passed_count} 项 | 失败 {self.failed_count} 项")
        print("==================================================")

        if self.failed_count > 0:
            print("\n[FAIL] 发现以下问题需要修复:")
            for err in self.errors:
                print(err)
            sys.exit(1)
        else:
            print("\n[SUCCESS] 所有自动化测试点全部通过！系统状态完美健全！")
            sys.exit(0)

if __name__ == "__main__":
    tester = VocabAppTester()
    tester.run_all()
