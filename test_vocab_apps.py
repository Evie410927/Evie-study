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

        scene_min_height_stretch = '.scene {' in content and 'min-height: 480px;' in content
        self.assert_true(scene_min_height_stretch, f"[{lang_name}] 复习界面-中间卡片容器最小高度 480px 延伸", ".scene 缺少 min-height: 480px 保证卡片足够纵向拉长")

        review_actions_bottom = '.review-actions {' in content and 'margin-top: auto;' in content
        self.assert_true(review_actions_bottom, f"[{lang_name}] 复习界面-控制按钮最置底定位", ".review-actions 缺少 margin-top: auto，未能贴紧底部菜单 Tab 上方")

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

        similar_ex_trans_clarity = ('.similar-word-chip .similar-ex-trans {' in content and 'color: var(--text-secondary)' in content) or ('similar-ex-trans' in content and 'color:var(--text-secondary)' in content)
        self.assert_true(similar_ex_trans_clarity, f"[{lang_name}] 相近表达-例句原文高亮与例句中文翻译层次色配置", ".similar-ex-trans 缺少 color: var(--text-secondary) 层次色配置，导致与例句原文难以区分")

        # ---------------------------------------------------------------------
        # 测试点 15: 云端智能合并与本地删除记忆保护 (Smart Sync & Delete Memory)
        # ---------------------------------------------------------------------
        smart_sync_methods = 'getDeletedSet()' in content and 'recordDeletedWord(' in content and 'mergeCloudData(' in content
        self.assert_true(smart_sync_methods, f"[{lang_name}] 云端同步-智能合并与本地删除记忆保护机制", "类中缺少 getDeletedSet / recordDeletedWord / mergeCloudData 方法，会导致用户删词后同步被误还原")

        # ---------------------------------------------------------------------
        # 测试点 16: 统计数字与卡片数据一致性与自我修复测试 (Stats Data Self-Healing Parity)
        # ---------------------------------------------------------------------
        stats_self_healing = 'if (!this.words || !Array.isArray(this.words) || this.words.length === 0)' in content and 'samples' in content
        self.assert_true(stats_self_healing, f"[{lang_name}] 统计数字-updateStats 数据源自我修复保底防护", "updateStats 中缺少对 this.words 为空时的 samples 自自我修复保底，可能导致卡片有词但数字显 0")

        static_counts_bound = 'id="count-all"' in content and ('id="count-learning"' in content)
        self.assert_true(static_counts_bound, f"[{lang_name}] 统计数字-DOM 节点绑定健全性", "缺少 count-all 或 count-learning DOM 节点绑定")


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
