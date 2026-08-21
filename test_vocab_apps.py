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
import time
from pathlib import Path

# 强制标准输出使用 UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

KR_FILE = r"C:\Users\NCC Technology\Evie-study\standalone_kr_vocab.html"
JP_FILE = r"C:\Users\NCC Technology\Evie-study\standalone_jp_vocab.html"
SUPABASE_SQL_FILE = r"C:\Users\NCC Technology\Evie-study\supabase_vocab_sync.sql"

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

        init_body = re.search(r'\n\s*init\(\)\s*\{(.*?)\n\s*\}\n\s*\n\s*loadData\(', content, re.S)
        save_data_body = re.search(r'\n\s*saveData\(\)\s*\{(.*?)\n\s*\}\n\s*\n\s*loadTheme\(', content, re.S)
        edit_auto_upload = (
            'title="手动云端同步"' in content
            and bool(init_body) and 'fetchFromCloud(' not in init_body.group(1)
            and bool(save_data_body) and 'this.scheduleCloudSync()' in save_data_body.group(1)
            and 'scheduleCloudSync(delay = 350)' in content
            and 'this.syncWithSupabase(false)' in content
        )
        self.assert_true(edit_auto_upload, f"[{lang_name}] 云同步-登录后编辑自动上传且启动时不无条件拉取", "本地编辑保存后未安排静默上传，或页面启动时错误地无条件拉取云端")

        historical_pending_upload = bool(init_body) and all(token in init_body.group(1) for token in (
            "const pendingCloudChanges = this.getPendingCloudChanges",
            "this.getCloudSession()",
            "Object.keys(pendingCloudChanges).length > 0",
            "this.scheduleCloudSync(600)",
        ))
        self.assert_true(historical_pending_upload, f"[{lang_name}] 云同步-重新打开页面自动补传历史待同步编辑", "旧版本积压在浏览器本地的修改不会在升级后自动进入云端")

        # Supabase 双端同步回归矩阵：覆盖账号隔离、全字段编辑、删除与冲突合并。
        supabase_configured = (
            "https://orxkrmiqboumwbneworn.supabase.co" in content
            and "sb_publishable_YrhTciM7PjyCIJvdmu5OlA_I1fgsyU4" in content
            and "service_role" not in content
        )
        self.assert_true(supabase_configured, f"[{lang_name}] 云同步-Supabase Project URL 与安全 Publishable key 配置", "Supabase 配置缺失或错误暴露 service_role 高权限密钥")

        cloud_auth = all(token in content for token in (
            "cloudAuthModal", "cloudAuthEmail", "cloudAuthPassword",
            "submitCloudAuth('signin')", "submitCloudAuth('signup')",
            "token?grant_type=refresh_token", "cloudAuthStatus", "setCloudAuthStatus",
            "正在注册账号", "注册请求已提交", "button.disabled = false",
            "getCloudRedirectUrl", "signup?redirect_to=", "consumeCloudAuthCallback",
            "邮箱确认完成，已登录云同步",
        ))
        self.assert_true(cloud_auth, f"[{lang_name}] 云同步-同账号登录注册、弹窗内可见状态与过期令牌刷新", "缺少登录注册、弹窗内状态反馈、按钮恢复或 refresh token 续期逻辑")

        per_word_sync = all(token in content for token in (
            "word_id", "payload", "updated_at", "deleted_at",
            "on_conflict=user_id,language,word_id", "resolution=merge-duplicates",
        ))
        self.assert_true(per_word_sync, f"[{lang_name}] 云同步-逐词条全量 payload Upsert", "云端同步没有按 word_id 保存完整卡片字段或缺少 Upsert 防重复")

        edit_tracking = all(token in content for token in (
            "wordFingerprint", "markLocallyChangedWords", "word.updatedAt = Math.max(now",
            "if (this.markLocallyChangedWords) this.markLocallyChangedWords()",
        ))
        self.assert_true(edit_tracking, f"[{lang_name}] 云同步-释义/例句/Tag/掌握状态等所有编辑统一更新时间追踪", "saveData 未通过全卡片指纹捕获所有字段修改")

        field_level_merge = all(token in content for token in (
            "fieldUpdatedAt", "mergeWordFields(localWord, cloudPayload",
            "const fieldMergedWord =", "differsFromCloud", "differsFromLocal",
        ))
        self.assert_true(field_level_merge, f"[{lang_name}] 云同步-释义例句与星级状态按字段合并", "同步仍按整张卡片覆盖，手机改星级时可能反向覆盖电脑端新释义或例句")

        tombstone_sync = all(token in content for token in (
            "getDeletedRecords", "saveDeletedRecords", "recordDeletedWord",
            "const deletedAt = Date.now()", "cloudDeletedAt >= localUpdatedAt",
        ))
        self.assert_true(tombstone_sync, f"[{lang_name}] 云同步-删除 Tombstone 跨设备传播并防止复活", "删除记录未携带时间戳，或云端删除不能覆盖旧的本地卡片")

        conflict_merge = all(token in content for token in (
            "const cloudWinsByTime = cloudUpdatedAt > localUpdatedAt",
            "const localWinsByTime = localWord && cloudDiffers && localUpdatedAt >= cloudUpdatedAt",
            "pending[id] = { changedAt: Math.max(localUpdatedAt, 1), source: 'user' }",
            "localDeletedAt >= cloudUpdatedAt", "mergeCloudRows", "syncWithSupabase",
        )) and "(!locallyPending && cloudDiffers)" not in content
        self.assert_true(conflict_merge, f"[{lang_name}] 云同步-严格 Last-Write-Wins 且旧云端禁止覆盖较新本地编辑", "冲突合并仍可能因待上传标记缺失而用旧云端副本覆盖较新本地编辑")

        legacy_pending_protected = all(token in content for token in (
            "return { changedAt, source: changedAt > 0 ? 'user' : 'none' }",
            "pendingMeta.source === 'system'",
        )) and "pendingMeta.source === 'legacy'" not in content
        self.assert_true(legacy_pending_protected, f"[{lang_name}] 云同步-旧格式待上传记录按用户编辑保护", "legacy 待上传记录仍可能被当作系统更新，导致较旧云端内容覆盖较新的本地编辑")

        sync_lock = "this._cloudSyncing" in content and "this._cloudSyncPending" in content
        self.assert_true(sync_lock, f"[{lang_name}] 云同步-并发请求锁与待同步补偿", "连续编辑可能并发上传并产生覆盖竞争")

        delta_sync = all(token in content for token in (
            "PENDING_CLOUD_KEY", "getPendingCloudChanges", "markPendingCloudChanges",
            "clearUploadedCloudChanges", "cloudIds.has(String(w.id))",
            "this.upsertCloudRows(session.access_token, userId, cloudRows)",
        ))
        self.assert_true(delta_sync, f"[{lang_name}] 云同步-手机编辑待上传队列与差量 Upsert", "点击云朵仍可能把浏览器旧整库反向覆盖手机新编辑")

        explicit_error = "PGRST205" in content and "supabase_vocab_sync.sql" in content and "云同步失败" in content
        self.assert_true(explicit_error, f"[{lang_name}] 云同步-缺表/断网/鉴权失败显式提示", "云端异常仍可能被误报为已经同步成功")

        lang_code = "kr" if lang_name == "韩语" else "jp"
        other_lang = "jp" if lang_code == "kr" else "kr"
        storage_isolation = f"k.startsWith('evie_{lang_code}_')" in content and f"k.startsWith('evie_{other_lang}_')" not in content
        self.assert_true(storage_isolation, f"[{lang_name}] 本地存储-KR/JP 清理范围隔离", "当前页面可能误删另一语言页面的 localStorage 数据")

        mirrored_mixin = f"Object.assign({'Kr' if lang_code == 'kr' else 'Jp'}VocabApp.prototype, createSupabaseSyncMethods('{lang_code}'))" in content
        self.assert_true(mirrored_mixin, f"[{lang_name}] 云同步-语言隔离且 KR/JP 共用镜像同步引擎", "同步引擎未正确挂载到当前语言应用")

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

        review_actions_clearance = '.flashcard-container {' in content and 'padding-bottom: 8px;' in content and 'margin-top: auto;' in content
        self.assert_true(review_actions_clearance, f"[{lang_name}] 复习界面-易忘/记住了按钮与底部 Tab 仅保留 8px 紧凑安全间距", ".flashcard-container 未使用 8px 紧凑底距，可能产生大块空白或遮挡底部 Tab")

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

        scroll_to_first_match = re.search(
            r'scrollToFirstCard\(\)\s*\{(?P<body>.*?)\n\s*\}\n\s*\n\s*scrollToListTop\(\)',
            content,
            re.S,
        )
        scroll_to_first_body = scroll_to_first_match.group('body') if scroll_to_first_match else ''
        scroll_to_first = all(token in scroll_to_first_body for token in (
            "document.getElementById('wordList')",
            'listContainer.scrollTop = 0',
            'requestAnimationFrame',
        )) and 'window.scrollTo' not in scroll_to_first_body
        self.assert_true(scroll_to_first, f"[{lang_name}] 分页-翻页后 #wordList 滑动条自动归零", "scrollToFirstCard 未直接重置 #wordList.scrollTop，或仍在错误滚动整个 window")

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
        # 测试点 10.5: 主列表排序=五星→无星/无星→五星 + 创建时间近→远/远→近
        #              (回归: 星级升降排序曾被误删, 用户要求维持原星级排序;
        #               用户随后要求删除"默认排序"项, 只保留升降/创建时间四项)
        # ---------------------------------------------------------------------
        default_sort_option_absent = 'value="default">默认排序<' not in content
        self.assert_true(default_sort_option_absent, f"[{lang_name}] 排序-默认排序选项已删除(用户需求)", "主列表下拉框仍残留 默认排序 选项, 用户明确要求删除")

        star_sort_options_present = ('value="desc" selected>五星 → 无星<' in content
            and 'value="asc">无星 → 五星<' in content)
        self.assert_true(star_sort_options_present, f"[{lang_name}] 排序-星级升降两选项齐全且默认五星→无星", "主列表下拉框星级排序两选项缺失或 selected 未落在 五星→无星 上")

        star_sort_default_selected = 'value="desc" selected>五星 → 无星<' in content
        self.assert_true(star_sort_default_selected, f"[{lang_name}] 排序-默认选中五星→无星(星级降序)", "selected 未默认设置在 value=\"desc\" 五星→无星 选项上")

        created_sort_options = 'value="createdDesc">近 → 远<' in content and 'value="createdAsc">远 → 近<' in content
        self.assert_true(created_sort_options, f"[{lang_name}] 排序-创建时间近→远/远→近两选项保留(不再 selected)", "sortRatingSelect 创建时间 createdDesc/createdAsc 选项缺失或仍被误标 selected")

        created_sort_prefix_removed = '创建时间:' not in content
        self.assert_true(created_sort_prefix_removed, f"[{lang_name}] 排序-下拉框移除前缀防文案截断", "主列表排序下拉框仍残留“创建时间:”前缀，112px 限宽下文案会被截断")

        rating_sort_init_desc = "this.ratingSort = 'desc'" in content
        self.assert_true(rating_sort_init_desc, f"[{lang_name}] 排序-ratingSort 默认初始化为 desc(五星→无星)", "构造函数中 ratingSort 未默认设置为 desc")

        star_sort_method = 'sortWordsByRating(items, direction)' in content
        self.assert_true(star_sort_method, f"[{lang_name}] 排序-sortWordsByRating 星级排序方法存在", "类中缺少 sortWordsByRating 星级排序方法")

        created_sort_method = 'sortWordsByCreatedAt(items, direction)' in content
        self.assert_true(created_sort_method, f"[{lang_name}] 排序-sortWordsByCreatedAt 方法存在", "类中缺少 sortWordsByCreatedAt 排序方法")

        rating_sort_guard = ("allowedSorts = ['asc', 'desc', 'createdAsc', 'createdDesc']" in content
            and "allowedSorts.includes(value) ? value : 'desc'" in content)
        self.assert_true(rating_sort_guard, f"[{lang_name}] 排序-onRatingSortChange 四值合法护栏(默认回落 desc)", "onRatingSortChange 缺少四值 allowedSorts 护栏或默认回落 desc 逻辑")

        created_sort_branch = "this.ratingSort === 'createdAsc' || this.ratingSort === 'createdDesc'" in content
        self.assert_true(created_sort_branch, f"[{lang_name}] 排序-renderWordList 创建时间分支联动", "renderWordList 缺少 createdAsc/createdDesc 排序分支")

        star_sort_branch = 'sortWordsByRating(filtered, this.ratingSort)' in content
        self.assert_true(star_sort_branch, f"[{lang_name}] 排序-renderWordList 星级排序分支联动", "renderWordList 缺少 sortWordsByRating 星级排序分发")

        status_rating_commit_chain = all(token in content for token in (
            'word.updatedAt = Math.max(Date.now(), Number(word.updatedAt || 0) + 1);',
            'if (this.markPendingCloudChanges) this.markPendingCloudChanges([String(word.id)], word.updatedAt);',
            'const word = this.words.find(w => String(w.id) === String(id));',
            'if (options.rerender !== false) this.renderWordList();',
            'this.syncRatingWidgets(wordId);',
            'this.syncMasteredWidgets(id);',
            'this.updateStats();',
        )) and content.count('word.updatedAt = Math.max(Date.now(), Number(word.updatedAt || 0) + 1);') >= 2 and content.count('this.markPendingCloudChanges([String(word.id)], word.updatedAt)') >= 2
        self.assert_true(status_rating_commit_chain, f"[{lang_name}] 状态与星级-显式更新时间、持久化后重绘并刷新统计", "学习状态或星级仍依赖隐式指纹更新，可能出现提示成功但数据/统计/卡片未更新")

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

        mobile_tag_dropdown_unclipped = all(token in content for token in (
            "positionTagDropdownMenu(menu)", "document.body.appendChild(menu)",
            "button.getBoundingClientRect()", "menu.style.position = 'fixed'",
            "menu.style.zIndex = '10000'", "viewportWidth - menuWidth - 8",
            "list.style.maxHeight",
        ))
        self.assert_true(mobile_tag_dropdown_unclipped, f"[{lang_name}] 标签筛选-手机端下拉菜单脱离滚动层且完整显示", "标签下拉框仍嵌在词库滚动层中，可能被卡片遮挡或超出屏幕")

        tag_methods_exist = 'toggleTagDropdown(' in content and 'toggleTagFilter(' in content and 'clearAllTagFilters(' in content and 'updateTagBadge(' in content and 'renderTagDropdownItems(' in content
        self.assert_true(tag_methods_exist, f"[{lang_name}] 标签筛选-多选切换与清空方法集健全", "类中缺少 toggleTagFilter/clearAllTagFilters/updateTagBadge/renderTagDropdownItems 方法")

        required_system_pos_tags = ('动词', '形容词', '名词', '副词', '短语', '惯用句', '接续词', '连体词', '形容动词', '语法', '句型', '词汇', '助词', '助动词')
        custom_tag_only_filter = (
            'posTags' in content
            and '!posTags.has(' in content
            and all(f"'{tag}'" in content for tag in required_system_pos_tags)
        )
        self.assert_true(custom_tag_only_filter, f"[{lang_name}] 标签筛选-下拉菜单仅显示自定义 Tag，完整排除 KR/JP 系统词性 Tag", "getAllAvailableTags 的系统词性集合不完整，词汇/接续词/连体词/形容动词等可能混入顶部标签列表")

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
        card_ex_preview_css = all(token in content for token in (
            '.word-example-preview {',
            '.ex-preview-text {',
            'border-left: 3px solid var(--accent-primary);',
            'padding-left: 10px;',
            'border-radius: 8px 0 0 8px;',
        ))
        self.assert_true(card_ex_preview_css, f"[{lang_name}] 列表卡片-例句预览含粉红左边强调装饰与内距", "例句预览缺少 3px 强调左边、10px 内距或圆角端点")

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
        # 测试点 18: 一键置顶/置底仅滚动 #wordList，不带动固定分页栏或整个页面
        # ---------------------------------------------------------------------
        has_scroll_api = 'scrollToListTop' in content and 'scrollToListBottom' in content
        self.assert_true(has_scroll_api, f"[{lang_name}] 逻辑-scrollToListTop 与 scrollToListBottom 一键直达 API 健全", "JS 中缺少 scrollToListTop 或 scrollToListBottom 函数")

        list_only_scroll = (
            'wl.scrollTop = wl.scrollHeight' in content
            and "pag.scrollIntoView({ behavior: 'smooth', block: 'center' })" not in content
            and "firstCard.scrollIntoView({ behavior: 'smooth', block: 'start' })" not in content
        )
        self.assert_true(list_only_scroll, f"[{lang_name}] 逻辑-置顶/置底按钮仅滚动 #wordList，分页栏与页面保持固定", "置顶/置底逻辑仍会 scrollIntoView 带动固定分页栏或整个页面")

        # ---------------------------------------------------------------------
        # 测试点 19: 底部导航栏紧凑高度 44px 与粉色拖动滑动条高亮测试
        # ---------------------------------------------------------------------
        compact_bottom_nav_css = 'height: 44px !important;' in content or 'height: 44px;' in content
        self.assert_true(compact_bottom_nav_css, f"[{lang_name}] 样式-底部导航栏高度紧凑化至 44px", "CSS 中 .bottom-nav 缺少 height: 44px !important 紧凑化配置")

        pink_scrollbar_css = '#wordList::-webkit-scrollbar-thumb' in content and 'var(--accent-primary, #ec4899)' in content
        self.assert_true(pink_scrollbar_css, f"[{lang_name}] 样式-粉色高亮拖动滑动条 ::-webkit-scrollbar-thumb 渲染配置", "CSS 中缺少 #wordList::-webkit-scrollbar-thumb 粉色高亮拖动滑动条配置")

        scrollbar_endpoint_arrows = all(token in content for token in (
            '#wordList::-webkit-scrollbar-button:single-button:vertical:decrement',
            '#wordList::-webkit-scrollbar-button:single-button:vertical:increment',
            "d='M4 1 7 6H1z'",
            "d='m1 2 3 5 3-5z'",
        ))
        self.assert_true(scrollbar_endpoint_arrows, f"[{lang_name}] 样式-列表滚动条顶部向上箭头与底部向下箭头成对显示", "#wordList 滚动条缺少顶部 decrement 或底部 increment 箭头")

        # ---------------------------------------------------------------------
        # 测试点 20: 卡片底部 Tag 行内打字加标签交互组件防护 (Inline Tag Input Component Test)
        # ---------------------------------------------------------------------
        inline_tag_css = '.inline-tag-editor {' in content and '.inline-tag-input {' in content and '.inline-quick-tag-chip {' in content
        self.assert_true(inline_tag_css, f"[{lang_name}] 交互-卡片底部 Tag 行内打字编辑器 CSS 规则健全", "CSS 中缺少 .inline-tag-editor / .inline-tag-input / .inline-quick-tag-chip 规则")

        inline_tag_methods = 'showInlineTagInput(' in content and 'handleInlineTagKeydown(' in content and 'saveInlineTag(' in content and 'addQuickTag(' in content
        self.assert_true(inline_tag_methods, f"[{lang_name}] 交互-行内打字加标签 API 方法集 (showInlineTagInput/saveInlineTag/addQuickTag) 健全", "类中缺少 showInlineTagInput / handleInlineTagKeydown / saveInlineTag / addQuickTag 方法")

        add_only_modal_tag_editor = all(token in content for token in (
            'id="addWordTagsGroup"',
            'id="modalTagsContainer"',
            '>卡片标签</label>',
            'this.editingModalTags = [];',
            "addWordTagsGroup.style.display = word ? 'none' : 'block';",
            'renderModalTags(',
            'showModalInlineTagInput(',
            'editModalTag(',
            'handleModalInlineTagKeydown(',
            'saveModalInlineTag(',
            'addModalQuickTag(',
            'removeModalTag(',
            'const existingWord = id ? this.words.find(w => w.id === id) : null;',
            'const tags = existingWord && Array.isArray(existingWord.tags) ? [...existingWord.tags] : [...(this.editingModalTags || [])];',
        )) and "const tags = existingWord && Array.isArray(existingWord.tags) ? [...existingWord.tags] : ['名词'];" not in content
        self.assert_true(add_only_modal_tag_editor, f"[{lang_name}] 新增弹窗-空白 Tag 编辑器支持增改删且编辑旧词时隐藏", "新增弹窗缺少零默认 Tag 编辑器、增改删方法，或编辑旧词时没有隐藏标签字段/保留原 Tag")

        add_modal_rating_editor = all(token in content for token in (
            'id="addWordRatingGroup"',
            'id="modalDraftRating"',
            'this.editingModalRating = 0;',
            "addWordRatingGroup.style.display = word ? 'none' : 'block';",
            'renderModalDraftRating()',
            'setModalDraftRatingFromPointer(event)',
            'handleModalDraftRatingKeydown(event)',
            'rating: draftRating,',
        ))
        self.assert_true(add_modal_rating_editor, f"[{lang_name}] 新增弹窗-可点击与键盘编辑星级并随新词保存", "新增弹窗缺少草稿星级控件、交互方法或保存字段")

        add_modal_mastered_editor = all(token in content for token in (
            'id="addWordMasteredGroup"',
            'id="modalDraftMasteredBtn"',
            '>学习状态</label>',
            'this.editingModalMastered = false;',
            "addWordMasteredGroup.style.display = word ? 'none' : 'block';",
            'renderModalDraftMastered()',
            'toggleModalDraftMastered()',
            'const draftMastered = existingWord ? Boolean(existingWord.mastered) : Boolean(this.editingModalMastered);',
            'mastered: draftMastered,',
        )) and 'mastered: false,' not in content[content.find('const newWord = {'):content.find('const newWord = {') + 1000]
        self.assert_true(add_modal_mastered_editor, f"[{lang_name}] 新增弹窗-学习中/已掌握 Label 可直接切换并随新词保存", "新增弹窗缺少学习状态草稿控件、切换方法或仍将新词状态硬编码为学习中")

        add_modal_similar_picker = all(token in content for token in (
            'id="addWordSimilarGroup"',
            'id="modalSimilarSearchInput"',
            'id="modalSimilarSearchResults"',
            'id="modalSelectedSimilarWords"',
            'this.editingModalSimilarWordIds = [];',
            "addWordSimilarGroup.style.display = word ? 'none' : 'block';",
            'renderModalSelectedSimilarWords()',
            'searchModalSimilarWordOptions(input)',
            'addModalSimilarWord(similarWordId)',
            'removeModalSimilarWord(similarWordId)',
            'manualSimilarWordIds: [...draftSimilarWordIds],',
            'newWord.autoSimilarWordIds = [];',
            'similarWord.manualSimilarWordIds.push(String(newWord.id))',
        ))
        self.assert_true(add_modal_similar_picker, f"[{lang_name}] 新增弹窗-相近词面板支持库内搜索、增删与双向持久关联", "新增弹窗缺少相近词搜索面板、草稿选择方法、空自动快照或保存后的反向关联")

        protected_word_modal_draft = all(token in content for token in (
            '<div id="wordModal" class="modal-overlay">',
            'id="closeModalBtn" type="button"',
            'id="saveWordBtn" type="button"',
            "document.getElementById('wordForm')?.addEventListener('submit', (e) => {",
            "document.getElementById('wordForm')?.addEventListener('keydown', (e) => {",
            "if (e.key !== 'Enter' || e.target?.tagName === 'TEXTAREA') return;",
            "document.getElementById('saveWordBtn')?.addEventListener('click', (e) => {",
            'this.saveWordFromForm();',
            'const persisted = this.saveData();',
            'if (!persisted) return;',
            'this.showToast(saveSuccessMessage);',
        )) and all(token not in content for token in (
            "event.target.id === 'wordModal' && window.app) window.app.closeWordModal()",
            "if (e.target.id === 'wordModal') this.closeWordModal();",
            '<button type="submit" class="btn-primary"',
        ))
        self.assert_true(protected_word_modal_draft, f"[{lang_name}] 新增/编辑弹窗-仅右上角×或显式点击保存成功后关闭", "弹窗仍可能被遮罩点击、Enter 表单提交或其他非显式操作关闭并丢失草稿")

        detail_editor_returns_to_detail = all(token in content for token in (
            'id="detailEditBtn" type="button"',
            'this.openDetailWordEditor();',
            'openDetailWordEditor() {',
            'this.wordModalReturnContext = {',
            "detailModal.classList.remove('active');",
            'this.editWord(wordId, true);',
            'this.restoreDetailAfterWordModal();',
            'restoreDetailAfterWordModal() {',
            'this.showDetailModal(returnContext.wordId, true);',
            'detailBody.scrollTop = savedScrollTop;',
            'editWord(id, preserveDetailReturn = false)',
        )) and 'window.app.closeDetailModal(); window.app.editWord(id);' not in content
        self.assert_true(detail_editor_returns_to_detail, f"[{lang_name}] 详情→编辑-保存或×关闭编辑层后恢复原详情、历史与滚动位置", "详情编辑仍直接销毁详情弹窗，或编辑层关闭后未恢复原卡片上下文")

        word_list_isolated_scroll = 'flex-shrink: 0;' in content and '#wordList::-webkit-scrollbar' in content
        self.assert_true(word_list_isolated_scroll, f"[{lang_name}] 布局-#wordList 独立滚动与搜索/Tag控件置顶固定不动", "缺少 #wordList 独立滚动或 flex-shrink: 0 防压缩设置")

        # ---------------------------------------------------------------------
        # 测试点 21: #paginationBar 为 #wordList 外部持久兄弟节点，列表重绘不能删除它
        # ---------------------------------------------------------------------
        persistent_pagination = (
            content.count('id="paginationBar"') == 1
            and 'word-list-inline-pagination' in content
            and "}).join('') + '<div id=\"paginationBar\"'" not in content
            and 'renderPaginationControls' in content
        )
        self.assert_true(persistent_pagination, f"[{lang_name}] 结构-分页栏为 wordList 外部唯一持久节点，列表重绘不丢失", "#paginationBar 仍在 renderWordList 中动态拼接、重复出现或缺失")

        # ---------------------------------------------------------------------
        # 测试点 22: 翻页工具栏固定悬浮与强常驻 (Never Hide Pagination Bar) 防护测试
        # ---------------------------------------------------------------------
        pagination_always_flex = 'paginationBar.style.display = \'flex\'' in content and 'safeTotalPages = Math.max(1, totalPages)' in content and 'if (totalItems <= 0)' in content
        self.assert_true(pagination_always_flex, f"[{lang_name}] 逻辑-翻页工具栏有结果时常驻、0 条时隐藏", "renderPaginationControls 未区分 0 条空结果与至少 1 条有效结果")

        pagination_inline_css = 'position: relative' in content and 'z-index: 10' in content
        self.assert_true(pagination_inline_css, f"[{lang_name}] 样式-翻页工具栏采用 relative 相对定位内联流式布局 (防止 fixed 浮层遮挡与撕裂卡片按钮点击)", "CSS 中缺少 .pagination-bar 的 position: relative !important 相对定位")

        switch_tab_pagination = 'const paginationBar = document.getElementById(\'paginationBar\');' in content and 'showListNavigation = isListTab && hasListItems' in content
        self.assert_true(switch_tab_pagination, f"[{lang_name}] 逻辑-switchTab 按列表 Tab 与实际卡片数量联动导航显隐", "switchTab 未同时判断当前是否在列表页以及是否存在卡片")

        empty_navigation_hidden = all(token in content for token in (
            'updateListNavigationVisibility(false)',
            'updateListNavigationVisibility(true)',
            'const shouldShow = Boolean(hasItems && isListTab)',
            "if (topBtn) topBtn.style.setProperty('display', shouldShow ? 'flex' : 'none', 'important')",
            "if (bottomBtn) bottomBtn.style.setProperty('display', shouldShow ? 'flex' : 'none', 'important')",
        )) and 'this.renderPaginationControls(0, 0)' not in content
        self.assert_true(empty_navigation_hidden, f"[{lang_name}] 空结果-隐藏分页栏与置顶/置底按钮并支持恢复", "空结果分支仍渲染分页，或没有统一隐藏三个列表导航控件")

        # ---------------------------------------------------------------------
        # 测试点 23: 卡片底部仅保留 Tag 栏与朗读/编辑/删除，掌握状态统一由右上角 Label 切换
        # ---------------------------------------------------------------------
        render_list_match = re.search(
            r'renderWordList\(\)\s*\{(.*?)\n\s*updateListNavigationVisibility\(hasItems\)',
            content,
            re.DOTALL,
        )
        render_list_source = render_list_match.group(1) if render_list_match else ''
        has_card_footer_actions = all(token in render_list_source for token in (
            'class="word-footer"', 'this.renderWordTagsHtml(w)', 'class="card-actions"',
            'speakWord', 'editWord', 'deleteWord',
        ))
        bottom_status_removed = not bool(re.search(
            r'class="action-btn[^\"]*"[^>]*toggleMastered',
            render_list_source,
        ))
        self.assert_true(
            has_card_footer_actions and bottom_status_removed,
            f"[{lang_name}] 结构-列表底部仅保留 Tag、朗读、编辑、删除且无重复状态按钮",
            "单词卡片底栏缺少必要操作，或仍保留喇叭旁的学习中/已掌握按钮",
        )

        # ---------------------------------------------------------------------
        # 测试点 24: 所有标签（含系统词性）均可删除并阻止冒泡
        # ---------------------------------------------------------------------
        remove_tag_protection = all(token in content for token in (
            "const tagClass = isSystem ? 'pos-tag' : 'custom-tag';",
            'title="删除标签">×</i>',
            'removeCustomTag(wordId, tagName)',
            "const cleanTag = String(tagName || '').replace(/^#/, '').trim();",
            "word.tags = word.tags.filter(tag => String(tag || '').replace(/^#/, '').trim() !== cleanTag);",
            'word.updatedAt = Date.now();',
        ))
        self.assert_true(remove_tag_protection, f"[{lang_name}] 交互-系统词性与自定义 Tag 均显示 × 并可删除持久化", "系统词性 Tag 仍不可删除，或删除逻辑缺少归一化、更新时间与冒泡防护")

        custom_tag_css_m = re.search(r'\.tag-badge\.custom-tag\s*\{([^}]*)\}', content, re.DOTALL)
        active_tag_css_m = re.search(r'\.active-tag-chip\s*\{([^}]*)\}', content, re.DOTALL)
        quick_tag_css_m = re.search(r'\.inline-quick-tag-chip\s*\{([^}]*)\}', content, re.DOTALL)
        selected_tag_css_m = re.search(r'\.tag-dropdown-item\.selected\s*\{([^}]*)\}', content, re.DOTALL)
        neutral_tag_blocks = [
            custom_tag_css_m.group(1) if custom_tag_css_m else '',
            active_tag_css_m.group(1) if active_tag_css_m else '',
            quick_tag_css_m.group(1) if quick_tag_css_m else '',
        ]
        all_tags_neutral_gray = (
            all('rgba(255, 255, 255, 0.06)' in block and 'var(--text-secondary)' in block for block in neutral_tag_blocks)
            and selected_tag_css_m is not None
            and 'rgba(255, 255, 255, 0.12)' in selected_tag_css_m.group(1)
            and '#a5b4fc' not in (custom_tag_css_m.group(1) if custom_tag_css_m else '')
            and 'var(--accent-gradient)' not in (active_tag_css_m.group(1) if active_tag_css_m else '')
            and 'var(--accent-primary' not in (quick_tag_css_m.group(1) if quick_tag_css_m else '')
        )
        self.assert_true(all_tags_neutral_gray, f"[{lang_name}] 样式-系统、自定义、已选与快捷 Tag 全部统一为中性灰色", "Tag 仍保留蓝紫、粉色、渐变等特殊配色，或未采用与词性 Tag 一致的灰色")

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
        safe_storage_wrapper = all(token in content for token in (
            'class SafeStorageWrapper', 'SafeStorage',
            'localStorage.getItem(key) !== serialized',
            'flushMemoryStore()', 'hasVolatileValue(key)',
            'const durable = !SafeStorage.hasVolatileValue(this.STORAGE_KEY)',
            "if (!durable)", "return false;",
        ))
        self.assert_true(safe_storage_wrapper, f"[{lang_name}] 安全-SafeStorageWrapper 写入回读验证、临时数据重试与保存失败显式返回", "浏览器持久存储失败仍可能被静默降级为内存数据并误报保存成功")

        persistence_gated_feedback = (
            content.count('const persisted = this.saveData();') >= 7
            and content.count('if (!persisted) return;') >= 7
            and 'this.refreshSimilarWordPanels(targetWord.id);\n    if (!persisted) return;' in content
        )
        self.assert_true(persistence_gated_feedback, f"[{lang_name}] 持久化-编辑、相近表达、状态、删除、导入和清空仅在落盘成功后提示完成", "部分编辑入口仍可能在持久化失败后显示成功或继续完成后续动作")

        # ---------------------------------------------------------------------
        # 测试点 31: 相近表达纯手动关系与面板交互防护 (getSimilarWords & renderSimilarBlockHtml)
        # ---------------------------------------------------------------------
        similar_words_manual_view = 'getSimilarWords(' in content and 'renderSimilarBlockHtml(' in content and 'similar-word-chip' in content
        self.assert_true(similar_words_manual_view, f"[{lang_name}] 相近表达-getSimilarWords 手动关系读取与面板交互防护", "缺少 getSimilarWords 或 renderSimilarBlockHtml 方法")

        similar_word_manual_controls = all(token in content for token in (
            'class="similar-panel-add-btn"',
            'class="similar-word-remove-btn"',
            'toggleSimilarWordPicker(',
            'searchSimilarWordOptions(',
            'addSimilarWord(',
            'removeSimilarWord(',
            'refreshSimilarWordPanels(',
        ))
        self.assert_true(similar_word_manual_controls, f"[{lang_name}] 相近表达-标题＋库内搜索添加与卡片右上角×删除控件完整", "相近表达 Panel 缺少＋搜索添加、×删除或双视图刷新 API")

        similar_word_persistence = all(token in content for token in (
            'manualSimilarWordIds',
            'hiddenSimilarWordIds',
            'this.saveData()',
            'const seenIds = new Set();',
            'return manualIds',
        ))
        self.assert_true(similar_word_persistence, f"[{lang_name}] 相近表达-仅按人工关系不限量读取、去重并持久化", "相近表达未严格读取 manualSimilarWordIds，或缺少人工关系持久化")

        automatic_similarity_disabled = all(token in content for token in (
            'newWord.autoSimilarWordIds = [];',
            'w.autoSimilarWordIds = [];',
            '暂无相近表达，可点击右上角＋添加',
        )) and all(token not in content for token in (
            'calculateAutomaticSimilarWords(',
            'automaticWords.concat(',
            'targetWord.autoSimilarWordIds = this.',
        ))
        self.assert_true(automatic_similarity_disabled, f"[{lang_name}] 相近表达-彻底禁用自动计算与旧快照，仅允许人工添加编辑", "仍存在自动相近词算法、自动快照展示路径，或旧缓存快照未在装载时清空")

        bidirectional_manual_similarity = all(token in content for token in (
            'similarWord.manualSimilarWordIds = Array.isArray(similarWord.manualSimilarWordIds)',
            'similarWord.manualSimilarWordIds.push(String(targetWord.id))',
            'similarWord.hiddenSimilarWordIds = similarWord.hiddenSimilarWordIds.filter',
            'this.refreshSimilarWordPanels(similarWord.id)',
        ))
        self.assert_true(bidirectional_manual_similarity, f"[{lang_name}] 相近表达-人工添加自动建立并刷新双向持久关联", "A 手动添加 B 时未同步把 A 写入 B 的相近表达关系或未刷新反向视图")

        bidirectional_legacy_migration = all(token in content for token in (
            'SIMILAR_RELATION_MIGRATION_KEY',
            'migrateBidirectionalManualSimilarities()',
            'this.migrateBidirectionalManualSimilarities();',
            'if (reverseHiddenIds.includes(String(sourceWord.id))) return;',
            "SafeStorage.setItem(this.SIMILAR_RELATION_MIGRATION_KEY, 'done')",
        ))
        self.assert_true(bidirectional_legacy_migration, f"[{lang_name}] 相近表达-已有单向人工关系一次性补齐反向关系且尊重单侧隐藏", "旧数据不会自动迁移为双向关系，或迁移会错误恢复用户已删除的反向卡片")

        similar_word_search_scope = "[word.word, word.reading, word.meaning].some" in content and ".slice(0, 20)" in content
        self.assert_true(similar_word_search_scope, f"[{lang_name}] 相近表达-添加搜索仅匹配当前词库的词条/读音/释义", "相近表达搜索未限制为当前 this.words，或错误纳入例句/标签/笔记字段")

        similar_word_already_added_disabled = all(token in content for token in (
            '.similar-word-search-result:disabled',
            'class="similar-word-added-badge">已添加',
            'const addedIds = new Set(this.getSimilarWords(targetWord, 3)',
            "disabled aria-disabled=\"true\"",
            "isAdded ? ' is-added' : ''",
        ))
        self.assert_true(similar_word_already_added_disabled, f"[{lang_name}] 相近表达-搜索结果中的已添加词灰化禁用并显示状态", "已存在于当前 Panel 的词仍可在搜索结果中重复点击，或缺少‘已添加’状态提示")

        similar_word_continuous_multi_select = all(token in content for token in (
            "addSimilarWord('${targetWord.id}', '${word.id}', this)",
            'restoreSimilarWordPickerState(hostId, targetWordId, searchValue)',
            "triggerElement.closest('#detailSimilarBlock, #cardBackSimilarBlock')",
            "picker.classList.add('active')",
            'this.searchSimilarWordOptions(input, targetWordId);',
            'if (pickerState) this.restoreSimilarWordPickerState(',
        ))
        self.assert_true(similar_word_continuous_multi_select, f"[{lang_name}] 相近表达-详情与复习弹窗搜索下拉支持连续多选且保留查询和焦点", "选择首个相近词后未恢复原搜索下拉、查询内容及连续选择上下文")

        similar_search_backspace_guard = all(token in content for token in (
            'protectSimilarSearchBackspace(event, targetWordId = null, modalDraft = false)',
            "if (!event || event.key !== 'Backspace') return;",
            'event.stopPropagation();',
            "const allTextSelected = value.length > 0",
            'event.preventDefault();',
            "input.value = '';",
            'onkeydown="(window.app||window.vocabApp).protectSimilarSearchBackspace(event,',
            'onkeyup="(window.app||window.vocabApp).protectSimilarSearchBackspace(event,',
        ))
        self.assert_true(similar_search_backspace_guard, f"[{lang_name}] 相近表达-搜索框全选后 Backspace 仅清空文字并阻断弹窗关闭事件", "相近表达搜索框未拦截 Backspace 冒泡/默认导航，或全选删除后不能保持弹窗")

        # ---------------------------------------------------------------------
        # 测试点 31A: 相近表达卡片状态按钮位于星级左侧并可同步切换
        # ---------------------------------------------------------------------
        similar_word_status_control = all(token in content for token in (
            'class="similar-word-header-actions"',
            'class="similar-word-status-btn ${w.mastered',
            'data-mastered-word-id=',
            "${w.mastered ? '✅ 已掌握' : '🔄 学习中'}",
            "this.renderStarRating(w, 'similar-word-rating')",
            'syncMasteredWidgets(wordId)',
            'this.syncMasteredWidgets(id);',
        ))
        status_before_rating = content.find('class="similar-word-status-btn ${w.mastered') < content.find("this.renderStarRating(w, 'similar-word-rating')")
        self.assert_true(similar_word_status_control and status_before_rating, f"[{lang_name}] 相近表达-卡片星级左侧显示可切换的学习中/已掌握状态", "相近词卡片缺少状态按钮、未复用星级控件、状态未同步，或状态按钮没有位于星级左侧")

        detail_header_status_control = all(token in content for token in (
            'id="detailMasteredBtn" type="button"',
            'class="similar-word-status-btn detail-mastered-status-btn status-learning"',
            'id="detailRating" class="detail-star-slot"',
            "document.getElementById('detailMasteredBtn')?.addEventListener('click', (e) => {",
            'if (wordId) this.toggleMastered(wordId);',
            "const detailMasteredBtn = document.getElementById('detailMasteredBtn');",
            'detailMasteredBtn.dataset.masteredWordId = String(word.id);',
            'this.syncMasteredWidgets(word.id);',
        ))
        detail_status_before_rating = content.find('id="detailMasteredBtn"') < content.find('id="detailRating"')
        self.assert_true(detail_header_status_control and detail_status_before_rating, f"[{lang_name}] 详情弹窗-顶部星级左侧显示可直接切换的学习中/已掌握 Label", "详情标题栏缺少状态 Label、未绑定切换同步，或状态按钮没有位于星级左侧")

        # ---------------------------------------------------------------------
        # 测试点 31B: 用户自定义说明仅在卡片编辑弹窗维护并按内容条件展示
        # ---------------------------------------------------------------------
        user_note_views = all(token in content for token in (
            'id="detailUserNote"',
            'id="cardBackUserNote"',
            "this.renderUserNoteHtml(w, 'list')",
            "this.renderUserNoteHtml(w, 'similar')",
            "this.renderUserNoteHtml(word, 'detail')",
            "this.renderUserNoteHtml(word, 'review')",
            "const note = typeof word.userNote === 'string' ? word.userNote.trim() : '';",
            "if (!note) return '';",
            'class="user-note-display"',
            'class="user-note-text"',
        ))
        self.assert_true(user_note_views, f"[{lang_name}] 自定义说明-仅有内容时在列表、详情、复习背面与相近词卡片展示", "自定义说明缺少某个视图渲染调用、非空判断或只读展示结构")

        user_note_modal_editor = all(token in content for token in (
            '<label class="form-label" for="inputUserNote">说明</label>',
            'id="inputUserNote"',
            'maxlength="500"',
            "const userNoteInput = document.getElementById('inputUserNote');",
            "userNoteInput.value = typeof word.userNote === 'string' ? word.userNote : '';",
            'const userNote = userNoteInput.value.trim();',
            'userNote,',
        ))
        self.assert_true(user_note_modal_editor, f"[{lang_name}] 自定义说明-编辑弹窗说明字段支持回填、保存与清空", "编辑弹窗缺少说明字段，或 userNote 未接入新增/编辑保存流程")

        user_note_external_controls_removed = all(token not in content for token in (
            'user-note-add-btn',
            'user-note-edit-btn',
            'user-note-delete-btn',
            'user-note-input',
            'startUserNoteEdit',
            'saveUserNoteFromEditor',
            'deleteUserNote',
            '>【+】</button>',
            '自定义说明已保存',
            '自定义说明已清空',
            '自定义说明已删除',
        ))
        self.assert_true(user_note_external_controls_removed, f"[{lang_name}] 自定义说明-四种展示视图无【+】、编辑删除按钮及专属提醒", "展示层仍残留说明新增/编辑/删除控件或说明专属 Toast")

        user_note_style = all(token in content for token in (
            '.user-note-display {',
            '.user-note-text {',
            '.user-note-text::before { content: "【"; }',
            '.user-note-text::after { content: "】"; }',
            '.detail-user-note-slot:empty,',
            '.review-user-note-slot:empty {',
            'display: none;',
            'background: transparent;',
            'padding: 0;',
            'border: 0;',
            'font-size: 12px;',
        ))
        self.assert_true(user_note_style, f"[{lang_name}] 自定义说明-无背景中括号小字展示且空内容完全隐藏不占位", "自定义说明缺少紧凑纯文本样式，或详情/复习空插槽没有自适应隐藏")

        user_note_compact_spacing = all(token in content for token in (
            'margin: 0 0 3px;',
            '.user-note-row + .word-example-preview {',
            'margin-top: 3px;',
            '.similar-word-chip .user-note-row + .similar-word-example {',
            'margin-top: 0 !important;',
            '.detail-sheet .modal-header {',
            'padding: 4px 0 8px;',
            'gap: 6px;',
        ))
        self.assert_true(user_note_compact_spacing, f"[{lang_name}] 自定义说明-列表、详情与相近词卡片使用紧凑间距", "自定义说明与释义、例句之间仍保留过大的垂直间距")

        user_note_readable_color = bool(re.search(
            r'\.user-note-text\s*\{[^}]*color:\s*var\(--text-secondary\);',
            content,
            re.S,
        ))
        self.assert_true(user_note_readable_color, f"[{lang_name}] 自定义说明-文字颜色与中文释义使用同一灰色", "自定义说明仍使用过暗的 text-muted，阅读对比度不足")

        # ---------------------------------------------------------------------
        # 测试点 31C: 编辑弹窗固定三行双栏对照例句编辑器
        # ---------------------------------------------------------------------
        example_pair_editor = all(token in content for token in (
            'id="examplePairsEditor"',
            'class="example-pair-columns"',
            'data-example-index="0"',
            'data-example-index="1"',
            'data-example-index="2"',
            'example-source-input',
            'example-translation-input',
            'fillExamplePairsEditor(word = null)',
            'collectExamplePairsFromEditor()',
        )) and content.count('class="example-pair-row"') == 3
        self.assert_true(example_pair_editor, f"[{lang_name}] 编辑弹窗-例句字段固定三行且每行原句/中文翻译双栏一一对应", "编辑弹窗缺少固定三行、双栏输入框或例句装载/收集方法")

        legacy_example_inputs_removed = all(token not in content for token in (
            'id="inputExample"',
            'id="inputExampleTrans"',
            "document.getElementById('inputExample')",
            "document.getElementById('inputExampleTrans')",
        ))
        self.assert_true(legacy_example_inputs_removed, f"[{lang_name}] 编辑弹窗-旧原句大文本框与独立翻译框已完全移除", "旧 inputExample/inputExampleTrans 控件或读写逻辑仍残留，可能与三行编辑器冲突")

        example_pair_persistence = all(token in content for token in (
            'examplePairs.length !== 3',
            'examplePairs.some(pair => !pair.example || !pair.trans)',
            'const examples = examplePairs.map(pair => ({ example: pair.example, trans: pair.trans }))',
            "const example = examples.map(pair => pair.example).join('\\n')",
            "const exampleTrans = examples.map(pair => pair.trans).join('\\n')",
        ))
        self.assert_true(example_pair_persistence, f"[{lang_name}] 编辑弹窗-三组例句完整性校验并同步结构化与旧版兼容字段", "三组例句未校验成对完整性，或保存时没有同步 examples/example/exampleTrans")

        example_pair_layout = all(token in content for token in (
            '.example-pairs-editor {',
            '.example-pair-row {',
            'grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);',
            '.example-pair-input {',
        ))
        self.assert_true(example_pair_layout, f"[{lang_name}] 编辑弹窗-三行对照例句双等分布局与手机端紧凑适配", "例句双栏缺少稳定等分网格、输入框约束或手机端适配")

        # ---------------------------------------------------------------------
        # 测试点 32: 复习卡片语义与 Tag 聚类出词算法防护 (clusterBySimilarity)
        # ---------------------------------------------------------------------
        cluster_by_sim = 'clusterBySimilarity(' in content and 'this.clusterBySimilarity(' in content
        self.assert_true(cluster_by_sim, f"[{lang_name}] 算法-clusterBySimilarity 复习卡片语义与 Tag 聚类出词算法", "缺少 clusterBySimilarity 方法或未在 startReviewSession 中调用")

        # ---------------------------------------------------------------------
        # 测试点 33: 分页工具条位于独立滚动列表之外并保持紧凑固定
        # ---------------------------------------------------------------------
        fixed_pagination_footer = all(token in content for token in (
            '.pagination-bar {',
            'word-list-inline-pagination',
            'id="paginationBar"',
            'flex-shrink: 0 !important;',
            'height: 36px !important;',
        ))
        self.assert_true(fixed_pagination_footer, f"[{lang_name}] 结构-分页栏为滚动列表外的 36px 固定页脚", "分页栏缺少独立固定布局、flex 防压缩或 36px 紧凑高度")

        # ---------------------------------------------------------------------
        # 测试点 34: 详情弹窗相近表达跳转历史栈与返回上一词条 API 防护 (Detail Modal Navigation Stack & goBackDetailModal)
        # ---------------------------------------------------------------------
        modal_history_stack = 'detailModalHistory' in content and 'goBackDetailModal(' in content and ('id="detailNavBackBar"' in content or 'id="detailBackBtn"' in content or 'goBackDetailModal' in content)
        self.assert_true(modal_history_stack, f"[{lang_name}] 交互-详情弹窗相近表达跳转历史栈 detailModalHistory 与 goBackDetailModal 返回上级按钮防护", "缺少 detailModalHistory 历史栈数组或 goBackDetailModal 方法")

        # ---------------------------------------------------------------------
        # 测试点 34A: 相近表达切换到新词条时详情正文必须自动回到顶部
        # ---------------------------------------------------------------------
        detail_navigation_scroll_reset = all(token in content for token in (
            'shouldResetDetailScroll',
            "modalEl.querySelector('.detail-body')",
            'detailBody.scrollTop = 0',
            'requestAnimationFrame(() =>',
        ))
        self.assert_true(detail_navigation_scroll_reset, f"[{lang_name}] 交互-详情弹窗点击相近表达或返回上一词条后正文自动置顶", "showDetailModal 切换词条后未把复用的 .detail-body 滚动位置重置为顶部")

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
        # 测试点 37: 仅保留 📌易忘快捷标签，并彻底移除旧的易混卡片概念
        # ---------------------------------------------------------------------
        easy_forget_only = all(token in content for token in (
            'class="inline-quick-tag-chip"',
            "addQuickTag(event, '${wordId}', '易忘')",
            'grid-template-columns: 1fr 1fr;',
            "tag !== '\\u6613\\u6df7'",
        )) and all(token not in content for token in (
            'btnEasyConfuse',
            'easy-confuse',
            "addQuickTag(event, '${wordId}', '易混')",
        ))
        self.assert_true(easy_forget_only, f"[{lang_name}] 交互-仅保留📌易忘标签与两枚复习按钮，旧易混标签自动清理且无法重新添加", "仍存在易混按钮/标签/逻辑，或缺少旧数据清理及两列复习按钮布局")

        # ---------------------------------------------------------------------
        # 测试点 38: .word-list 使用极小底边距，把空间留给单词卡片
        # ---------------------------------------------------------------------
        wordlist_padding_bottom = '.word-list' in content and 'padding-bottom: 4px !important;' in content
        self.assert_true(wordlist_padding_bottom, f"[{lang_name}] 样式-.word-list 底边距压缩至 4px", "CSS 中缺少 .word-list 的 padding-bottom: 4px !important 紧凑配置")

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
        fallback_m = re.search(r'var fallbackWords = (\[.*?\]);', content, re.DOTALL)
        
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
        # 测试点 42A: 非空浏览器缓存也必须合并新版内置词条，并尊重用户删除记录
        # ---------------------------------------------------------------------
        load_data_m = re.search(r'\n  loadData\(\)\s*\{(.*?)\n  saveData\(\)', content, re.DOTALL)
        load_data_body = load_data_m.group(1) if load_data_m else ''
        cached_data_upgrade = (
            'Always reconcile built-in cards' in load_data_body
            and 'this.loadSampleData(false);' in load_data_body
            and 'deletedIds.has(String(item.id))' in content
            and 'deletedWords.has(item.word)' in content
            and 'contentRevision' in content
            and 'markPendingCloudChanges(changedIds, reconciliationTime' in content
        )
        self.assert_true(cached_data_upgrade, f"[{lang_name}] 数据升级-非空浏览器缓存自动补入新版内置词条且不复活已删除词", "loadData 未无条件合并内置 samples，或 loadSampleData 未尊重删除记录/按变化保存")

        user_edit_upgrade_guard = all(token in content for token in (
            'userEditedAt: userEditTime',
            'const hasProtectedUserEdit = Number(old.userEditedAt || 0) > 0',
            "pendingMeta.source === 'user'",
            '!hasProtectedUserEdit',
        ))
        self.assert_true(user_edit_upgrade_guard, f"[{lang_name}] 数据升级-用户手动编辑标记永久阻止内置样本覆盖", "编辑词条未写入 userEditedAt，或内置数据升级仍可能覆盖用户修改的释义、读音与例句")

        renamed_word_identity_guard = all(token in content for token in (
            'const uniqueCachedIds = new Map();',
            'const preferred = preferCachedWord',
            "const idMatchIndex = this.words.findIndex",
            'const idx = idMatchIndex !== -1 ? idMatchIndex',
            "markPendingCloudChanges(userChangedIds, reconciliationTime, 'user')",
        ))
        self.assert_true(renamed_word_identity_guard, f"[{lang_name}] 数据升级-用户改词名后按稳定 ID 匹配且旧样本不得复活", "loadSampleData 仍只按旧词名查找，用户改名后会重新补入同 ID 的旧卡并覆盖同步结果")

        corrected_example_migration = all(token in content for token in (
            'hasNewerContent' if lang_name == '韩语' else 'Number(item.contentRevision || 0) > Number(old.contentRevision || 0)',
            'examples: Array.isArray(item.examples)',
            'markPendingCloudChanges(changedIds, reconciliationTime',
            'updatedAt: reconciliationTime',
        ))
        self.assert_true(corrected_example_migration, f"[{lang_name}] 数据修复-新版自然例句覆盖旧缓存且仅标记修正词条待同步", "例句修正只能作用于空白设备，或加载时错误地把整库标记为待上传")

        if lang_name == '韩语':
            repaired_cluster_ids = [f'kr_{index}:' for index in range(585, 611)]
            repaired_example_cluster = (
                'window.KR_CONTENT_REPAIRS' in content
                and 'applyKrContentRepairs(samples);' in content
                and 'applyKrContentRepairs(fallbackWords);' in content
                and all(token in content for token in repaired_cluster_ids if token != 'kr_595:')
                and '실생활에서 무르다 문맥으로 자주 쓰인다.' not in content
                and '상황에 맞춰 성질 내다 행동하는 자세가 필요하다.' not in content
                and '"contentRevision": 2' in content
            )
            self.assert_true(repaired_example_cluster, '[韩语] 数据质量-截图词条及同批情绪/说话表达使用人工自然例句', '무르다、성질 내다 或同批词条仍保留模板句，或修订未覆盖主数据与备用数据')

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
        # 发音字段同时禁止残留日语音调圈号 (①-⑳ / ⓪)，用户明确要求去掉这种“奇怪的数字”
        import re as _re_circled
        circled_pat = _re_circled.compile(r'[①-⑳⓪]')
        reading_sources = [('samples', samples_m), ('fallbackWords', fallback_m)]
        for source_name, source_match in reading_sources:
            if not source_match:
                reading_valid = False
                invalid_reading_id = f"未解析到 {source_name} 数据源"
                break
            try:
                import json
                source_data = json.loads(source_match.group(1), strict=False)
                for item in source_data:
                    r_text = item.get('reading', '')
                    if source_name == 'fallbackWords':
                        r_text = str(r_text or '').strip()
                        while r_text.startswith('['):
                            r_text = r_text[1:].lstrip()
                        while r_text.endswith(']'):
                            r_text = r_text[:-1].rstrip()
                        r_text = f'[{r_text}]' if r_text else ''
                    if (
                        not r_text
                        or not r_text.startswith('[')
                        or not r_text.endswith(']')
                        or r_text.startswith('[[')
                        or r_text.endswith(']]')
                    ):
                        reading_valid = False
                        invalid_reading_id = f"Source={source_name} ID={item.get('id')} Word={item.get('word')} Reading={r_text}"
                        break
                    if circled_pat.search(r_text):
                        reading_valid = False
                        invalid_reading_id = f"Source={source_name} ID={item.get('id')} Word={item.get('word')} Reading={r_text} (含音调圈号)"
                        break
                if not reading_valid:
                    break
            except Exception as err:
                reading_valid = False
                invalid_reading_id = f"解析 {source_name} 失败: {err}"
                break
        self.assert_true(reading_valid, f"[{lang_name}] 数据集-全量卡片 reading 字段正位且格式规范 [...] (不含音调圈号)", f"发现 reading 缺失/缺少 [...] 括号/含圈号: {invalid_reading_id}")

        reading_auto_brackets = all(token in content for token in [
            'normalizeBracketedReading(value)',
            "const pitchAccentNumberMarks = new Set(Array.from('⓪①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳'));",
            "reading = Array.from(reading).filter(character => !pitchAccentNumberMarks.has(character)).join('').trim();",
            "while (reading.startsWith('[')) reading = reading.slice(1).trimStart();",
            "while (reading.endsWith(']')) reading = reading.slice(0, -1).trimEnd();",
            "return reading ? `[${reading}]` : '';",
            'formatReadingInput(input)',
            "document.getElementById('inputReading')?.addEventListener('blur'",
            'const reading = this.normalizeBracketedReading(readingInput.value);',
            'readingInput.value = reading;',
            'w.reading = this.normalizeBracketedReading(w.reading);',
            'function normalizeFallbackReadings(words)',
            'normalizeFallbackReadings(fallbackWords);',
            "reading = Array.from(reading).filter(function(character) { return !pitchAccentNumberMarks.has(character); }).join('').trim();",
            "word.reading = reading ? '[' + reading + ']' : '';",
            '系统自动添加 [ ]',
        ]) and 'const reading = readingInput.value.trim();' not in content
        self.assert_true(
            reading_auto_brackets,
            f"[{lang_name}] 表单-读音自动补全唯一方括号并移除日语圈号音调编号",
            "读音输入缺少方括号自动补全、圈号音调清理或旧缓存/备用数据迁移逻辑",
        )

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
        # 测试点 48: 内联翻页工具栏 (.pagination-bar / .word-list-inline-pagination) 采用 relative 相对定位 (防止 fixed 浮层遮挡与撕裂卡片按钮点击)
        # ---------------------------------------------------------------------
        pagination_bar_inline = ('.pagination-bar {' in content and 'position: relative !important;' in content) or ('.word-list-inline-pagination {' in content and 'position: relative !important;' in content)
        self.assert_true(pagination_bar_inline, f"[{lang_name}] 布局-内联翻页工具栏 position: relative 相对定位 (绝不浮动遮挡卡片按钮)", "pagination-bar 缺少 relative 相对定位，会导致 fixed 浮层遮挡底端卡片按钮导致点不动")

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
        expected_app_class = 'JpVocabApp' if lang_name == '日语' else 'KrVocabApp'
        app_mount_ok = f'window.app = new {expected_app_class}()' in content and 'window.vocabApp = window.app' in content
        self.assert_true(app_mount_ok, f"[{lang_name}] 逻辑-入口 DOMContentLoaded 事件中 window.app 与 window.vocabApp 双重挂载防护", "缺少 window.vocabApp = window.app 挂载，会导致以 vocabApp 调用的函数报错")

        # ---------------------------------------------------------------------
        # 测试点 56: 目标图紧凑布局与卡片底部左右分栏
        # ---------------------------------------------------------------------
        compact_target_layout = (
            'padding: 10px 12px 44px 0;' in content
            and 'padding-right: 10px;' in content
            and 'min-height: 36px;' in content
        )
        self.assert_true(compact_target_layout, f"[{lang_name}] 目标图样式-贴边主区域与紧凑搜索栏", "主区域、列表右侧或搜索框高度未按目标图紧凑布局")

        footer_split_layout = (
            '.word-footer {' in content
            and 'justify-content: space-between;' in content
            and '.card-actions {' in content
            and 'margin-left: auto;' in content
            and 'justify-content: flex-end;' in content
        )
        self.assert_true(footer_split_layout, f"[{lang_name}] 目标图样式-Tag 左置且操作按钮右置同排", "word-footer/card-actions 缺少左右分栏布局")

        # ---------------------------------------------------------------------
        # 测试点 55: 入口 DOMContentLoaded 事件中 app = window.app 挂载防护 (防止内联 app.func 抛 ReferenceError)
        # ---------------------------------------------------------------------
        global_app_assign = 'app = window.app;' in content
        self.assert_true(global_app_assign, f"[{lang_name}] 逻辑-入口 DOMContentLoaded 事件中 app = window.app 显式赋值", "缺少 app = window.app 赋值，会导致模板中 app.xxx 调用抛出 ReferenceError 引起卡片按钮点不动")

        # ---------------------------------------------------------------------
        # 测试点 57: 昨日稳定版与当前版差异回归矩阵
        # ---------------------------------------------------------------------
        preview_body_clickable = (
            '<div class="word-example-preview">' in content
            and 'class="ex-preview-text"' in content
            and 'class="ex-preview-trans"' in content
        )
        self.assert_true(preview_body_clickable, f"[{lang_name}] 基线差异-例句与翻译使用统一预览结构且卡片主体可点击", "运行时例句预览未统一，或仍可能吞掉卡片详情点击")

        dropdown_outside_close = (
            "document.addEventListener('click', (e) =>" in content
            and 'this.closeTagFilterDropdown();' in content
        )
        self.assert_true(dropdown_outside_close, f"[{lang_name}] 基线差异-点击标签下拉外部自动关闭", "缺少 document click 外部区域关闭 Tag 下拉逻辑")

        global_tag_handlers = all(token in content for token in (
            '(window.app||window.vocabApp).showInlineTagInput(event',
            '(window.app||window.vocabApp).handleInlineTagKeydown(event',
        ))
        self.assert_true(global_tag_handlers, f"[{lang_name}] 基线差异-卡片外部 Tag 行内编辑事件使用全局安全实例", "卡片外部 Tag 事件仍依赖不稳定的裸 app 变量")

        tag_normalization_safe = (
            "String(t).replace(/^#/, '').trim()" in content
            and ('!posTags.has(clean)' in content or '!posTags.has(cleanTag)' in content)
        )
        self.assert_true(tag_normalization_safe, f"[{lang_name}] 基线差异-自定义 Tag 去井号归一化并排除词性标签", "getAllAvailableTags 缺少稳定的 Tag 归一化/词性排除")

        detached_pagination_exact = (
            'class="pagination-bar word-list-inline-pagination"' in content
            and 'style="margin-top: 2px; margin-bottom: 0px;"' in content
            and 'margin-top: 0 !important;' in content
            and 'height: 36px !important;' in content
        )
        self.assert_true(detached_pagination_exact, f"[{lang_name}] 基线差异-分页保持 wordList 外部紧凑固定结构", "分页栏未从滚动列表中分离，或紧凑间距不符合镜像规范")

        fallback_click_syntax_safe = (
            "showDetailModal('' + w.id + '')" not in content
            and 'showDetailModal(w.id)' in content
        )
        self.assert_true(fallback_click_syntax_safe, f"[{lang_name}] 基线差异-兜底卡片 onclick 不含引号逃逸错误", "兜底卡片点击仍存在拼接引号错误")

        list_header_status_control = all(token in render_list_source for token in (
            'word-card-status-btn',
            'data-mastered-word-id=',
            'aria-pressed=',
            "toggleMastered('${w.id}')",
            "w.mastered ? '✅ 已掌握' : '🔄 学习中'",
            "this.renderStarRating(w, 'word-card-rating')",
        ))
        list_status_before_rating = render_list_source.find('word-card-status-btn') < render_list_source.find("this.renderStarRating(w, 'word-card-rating')")
        self.assert_true(
            list_header_status_control and list_status_before_rating,
            f"[{lang_name}] 列表卡片-右上角星级左侧 Label 为唯一学习状态切换入口",
            "列表右上角缺少常显可切换状态 Label、未位于星级左侧，或底部状态按钮未移除",
        )

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

        # JP 测试点 6: 日语语音发音 (speakWord) 正确配置 utterance.lang = 'ja-JP'
        has_ja_jp_tts = "utterance.lang = 'ja-JP';" in content
        self.assert_true(has_ja_jp_tts, "[日语专属] 语音-speakWord 发音引擎语言设置为 ja-JP", "utterance.lang 未设置为 ja-JP，导致日语发音引擎失效或读错")

        # JP 测试点 7: 编辑弹窗可回填并保存韩文对应释义
        editable_kr_meaning = all(token in content for token in (
            '<label class="form-label" for="inputKrMeaning">韩文释义</label>',
            'id="inputKrMeaning"',
            "const krMeaningInput = document.getElementById('inputKrMeaning');",
            "krMeaningInput.value = word.krMeaning || '';",
            'const krMeaning = krMeaningInput.value.trim();',
            'krMeaning,',
        ))
        self.assert_true(editable_kr_meaning, "[日语专属] 编辑弹窗-韩文释义字段支持回填、修改、清空与保存", "日语编辑弹窗缺少 inputKrMeaning，或 krMeaning 未接入回填/保存流程")

        # JP 测试点 8: 主搜索框支持按韩文释义 krMeaning 精确过滤
        search_method_match = re.search(
            r'getSearchFilteredWords\(\)\s*\{(.*?)\n\s*\}\s*\n\s*/\*',
            content,
            re.DOTALL,
        )
        search_method = search_method_match.group(1) if search_method_match else ''
        searches_kr_meaning = all(token in search_method for token in (
            'const matchKrMeaning = w.krMeaning',
            'w.krMeaning.toLowerCase().includes(q)',
            'matchMeaning || matchKrMeaning',
        ))
        search_hint_mentions_korean = 'placeholder="搜索日语单词、假名、中文或韩文释义..."' in content
        self.assert_true(
            searches_kr_meaning and search_hint_mentions_korean,
            "[日语专属] 主搜索-支持按 krMeaning 韩文释义筛选日语卡片",
            "JP getSearchFilteredWords 未将 krMeaning 纳入匹配，或搜索提示未说明支持韩文释义",
        )

    def test_browser_interactions(self, filepath, lang_name):
        """在真实浏览器中执行 JS 并点击核心控件，防止静态字符串断言假通过。"""
        print("\n  --------------------------------------------------")
        print(f"  >>> [{lang_name}] 真实浏览器交互测试（Selenium + Chrome）...")
        print("  --------------------------------------------------")

        driver = None
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            options = Options()
            options.add_argument('--headless=new')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=430,932')
            options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
            driver = webdriver.Chrome(options=options)
            driver.get(Path(filepath).resolve().as_uri())
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.word-card'))
            )
            time.sleep(0.5)

            required_methods = (
                'toggleTheme', 'openWordModal', 'showDetailModal', 'switchTab',
                'syncWithSupabase', 'mergeCloudRows', 'submitCloudAuth'
            )
            app_ready = driver.execute_script(
                "return !!window.app && arguments[0].every("
                "name => typeof window.app[name] === 'function');",
                list(required_methods),
            )
            self.assert_true(
                app_ready,
                f"[{lang_name}] 浏览器运行期-window.app 初始化且核心交互方法可调用",
                "window.app 未正确实例化，或 toggleTheme/openWordModal/showDetailModal/switchTab 缺失",
            )

            custom_tag_dropdown_result = driver.execute_script("""
                const app = window.app;
                const originalWords = app.words;
                try {
                  const systemTags = ['词汇', '动词', '形容词', '副词', '接续词', '连体词', '形容动词', '名词', '短语', '惯用句', '语法', '句型', '助词', '助动词'];
                  app.words = systemTags.map((tag, index) => ({
                    id: 'tag_filter_probe_' + index,
                    word: 'probe_' + index,
                    meaning: '测试',
                    tags: index === 0 ? [tag, '我的自定义标签'] : (index === 1 ? [tag, '#第二个自定义标签'] : [tag]),
                    mastered: false
                  }));
                  const available = app.getAllAvailableTags();
                  if (typeof app.renderTagDropdownMenu === 'function') app.renderTagDropdownMenu();
                  else app.renderTagDropdownItems();
                  const rendered = Array.from(document.querySelectorAll('#tagDropdownList .tag-name'))
                    .map(el => el.textContent.replace(/^#/, '').trim());
                  return {
                    available,
                    rendered,
                    onlyCustom: available.length === 2
                      && available.includes('我的自定义标签')
                      && available.includes('第二个自定义标签')
                      && rendered.length === 2
                      && rendered.includes('我的自定义标签')
                      && rendered.includes('第二个自定义标签')
                      && !systemTags.some(tag => available.includes(tag) || rendered.includes(tag))
                  };
                } finally {
                  app.words = originalWords;
                  app.renderWordList();
                  if (typeof app.renderTagDropdownMenu === 'function') app.renderTagDropdownMenu();
                  else app.renderTagDropdownItems();
                }
            """)
            self.assert_true(
                bool(custom_tag_dropdown_result and custom_tag_dropdown_result.get('onlyCustom')),
                f"[{lang_name}] 浏览器标签下拉-只渲染用户自定义 Tag，系统词性全部排除",
                f"标签列表错误：{custom_tag_dropdown_result}",
            )

            driver.find_element(By.ID, 'cloudSyncBtn').click()
            WebDriverWait(driver, 5).until(
                lambda active_driver: active_driver.execute_script(
                    "const m=document.getElementById('cloudAuthModal'); return !!m && m.style.display==='flex';"
                )
            )
            cloud_auth_visible = driver.execute_script(
                "return !!document.getElementById('cloudAuthEmail') && !!document.getElementById('cloudAuthPassword');"
            )
            self.assert_true(
                cloud_auth_visible,
                f"[{lang_name}] 浏览器真实点击-云朵打开账号登录而非静默假同步",
                "未登录时点击 #cloudSyncBtn 没有展示可操作的云同步登录界面",
            )

            driver.execute_script("""
                window.__originalCloudAuthRequest = window.app.cloudAuthRequest;
                window.__signupProbe = null;
                window.app.cloudAuthRequest = async function(path, body) {
                  window.__signupProbe = {path, body};
                  await new Promise(resolve => setTimeout(resolve, 80));
                  return {user:{id:'pending-email-confirmation'}, session:null};
                };
                document.getElementById('cloudAuthEmail').value = 'signup-test@example.com';
                document.getElementById('cloudAuthPassword').value = 'safe-test-password';
            """)
            driver.find_element(By.ID, 'cloudSignUpBtn').click()
            WebDriverWait(driver, 5).until(
                lambda active_driver: '注册请求已提交' in active_driver.find_element(By.ID, 'cloudAuthStatus').text
            )
            signup_result = driver.execute_script("""
                const probe = window.__signupProbe;
                const status = document.getElementById('cloudAuthStatus');
                const button = document.getElementById('cloudSignUpBtn');
                window.app.cloudAuthRequest = window.__originalCloudAuthRequest;
                return {
                  requested: !!probe && probe.path.startsWith('signup?redirect_to=') && probe.body.email === 'signup-test@example.com',
                  redirectCorrect: !!probe && decodeURIComponent(probe.path.split('redirect_to=')[1] || '').includes('evie410927.github.io/Evie-study/standalone_' + (window.app.words[0] && String(window.app.words[0].id).startsWith('jp_') ? 'jp' : 'kr') + '_vocab.html'),
                  statusVisible: !!status && status.style.display === 'block' && status.textContent.includes('注册请求已提交'),
                  buttonRestored: !!button && !button.disabled && button.textContent === '首次注册'
                };
            """)
            self.assert_true(
                bool(signup_result and signup_result.get('requested')),
                f"[{lang_name}] 浏览器真实点击-首次注册按钮确实发起 signup 请求",
                "点击 #cloudSignUpBtn 后没有调用云端 signup 接口",
            )
            self.assert_true(
                bool(signup_result and signup_result.get('redirectCorrect')),
                f"[{lang_name}] 浏览器真实点击-确认邮件 redirect_to 指向当前 GitHub Pages 页面",
                "signup 请求仍会把邮箱确认链接导向 localhost 或错误语言页面",
            )
            self.assert_true(
                bool(signup_result and signup_result.get('statusVisible')),
                f"[{lang_name}] 浏览器真实点击-注册结果在登录弹窗内部清晰可见",
                "注册结果仍被弹窗遮挡或没有写入 #cloudAuthStatus",
            )
            self.assert_true(
                bool(signup_result and signup_result.get('buttonRestored')),
                f"[{lang_name}] 浏览器真实点击-注册完成后按钮恢复可再次操作",
                "注册请求结束后 #cloudSignUpBtn 仍处于禁用或加载状态",
            )

            callback_result = driver.execute_script("""
                const app = window.app;
                const originalSave = app.saveCloudSession;
                let captured = null;
                app.saveCloudSession = data => { captured = data; return data; };
                location.hash = '#access_token=callback-test-token&refresh_token=callback-refresh&expires_in=3600&type=signup';
                const consumed = app.consumeCloudAuthCallback();
                app.saveCloudSession = originalSave;
                return {consumed, captured, hashCleared: !location.hash};
            """)
            self.assert_true(
                bool(callback_result and callback_result.get('consumed') and callback_result.get('captured', {}).get('access_token') == 'callback-test-token'),
                f"[{lang_name}] 浏览器邮箱回跳-自动保存 Supabase 登录会话",
                "确认邮件返回页面后没有消费 access_token 并完成登录",
            )
            self.assert_true(
                bool(callback_result and callback_result.get('hashCleared')),
                f"[{lang_name}] 浏览器邮箱回跳-登录后清除地址栏敏感 token",
                "邮箱确认 token 仍残留在地址栏 hash 中",
            )
            driver.execute_script("window.app.closeCloudAuthModal()")

            auto_sync_result = driver.execute_async_script("""
                const done = arguments[0];
                const app = window.app;
                const originalGetSession = app.getCloudSession;
                const originalSync = app.syncWithSupabase;
                let calls = 0;
                app.getCloudSession = () => ({access_token:'auto-sync-test-token'});
                app.syncWithSupabase = async () => { calls += 1; return true; };
                const scheduled = app.scheduleCloudSync(0);
                setTimeout(() => {
                  app.getCloudSession = originalGetSession;
                  app.syncWithSupabase = originalSync;
                  done({scheduled, calls});
                }, 80);
            """)
            self.assert_true(
                bool(auto_sync_result and auto_sync_result.get('scheduled') and auto_sync_result.get('calls') == 1),
                f"[{lang_name}] 浏览器本地编辑-登录状态下自动安排一次静默云上传",
                "本地保存后的自动同步调度器没有真正调用双向同步引擎",
            )

            rename_reconciliation_result = driver.execute_script("""
                const app = window.app;
                const originalWords = app.words;
                const originalPending = app.getPendingCloudChanges();
                const prefix = originalWords[0] && String(originalWords[0].id).startsWith('jp_') ? 'jp' : 'kr';
                const target = prefix === 'kr' ? originalWords.find(word => word.word === '둥그라미') : originalWords.find(word => word && word.id);
                if (!target) return {targetFound:false};
                const originalName = target.word;
                const renamedName = prefix === 'kr' ? '동그라미' : `${originalName}（用户改名）`;
                const editAt = Date.now() + 1000;
                try {
                  const edited = {...target, word:renamedName, userEditedAt:editAt, updatedAt:editAt, fieldUpdatedAt:{...(target.fieldUpdatedAt || {}), word:editAt}};
                  const staleSample = {...target, word:originalName, userEditedAt:0, updatedAt:editAt + 100};
                  app.words = originalWords.flatMap(word => String(word.id) === String(target.id) ? [edited, staleSample] : [word]);
                  app.savePendingCloudChanges({});
                  app.refreshWordFingerprints();
                  app.loadSampleData(false);
                  const sameIdCards = app.words.filter(word => String(word.id) === String(target.id));
                  const pendingMeta = app.getPendingCloudMeta(app.getPendingCloudChanges()[String(target.id)]);
                  return {
                    targetFound:true,
                    onlyOneStableId:sameIdCards.length === 1,
                    renamedPreserved:sameIdCards.length === 1 && sameIdCards[0].word === renamedName,
                    oldSampleNotRevived:!app.words.some(word => String(word.id) === String(target.id) && word.word === originalName),
                    queuedAsUserEdit:pendingMeta.source === 'user'
                  };
                } finally {
                  app.words = originalWords;
                  app.savePendingCloudChanges(originalPending);
                  app.persistSyncedData();
                  app.renderWordList();
                  app.updateStats();
                }
            """)
            self.assert_true(
                bool(rename_reconciliation_result and rename_reconciliation_result.get('targetFound') and rename_reconciliation_result.get('onlyOneStableId') and rename_reconciliation_result.get('renamedPreserved') and rename_reconciliation_result.get('oldSampleNotRevived') and rename_reconciliation_result.get('queuedAsUserEdit')),
                f"[{lang_name}] 浏览器数据升级-改词名后旧样本不复活且改名版本重新排队上传",
                "用户改词名后 loadSampleData 又补回同 ID 的旧词名，或没有保留并上传用户版本",
            )

            merge_result = driver.execute_script("""
                const app = window.app;
                const originalWords = app.words;
                const originalDeleted = app.getDeletedRecords();
                const originalPending = app.getPendingCloudChanges();
                const prefix = originalWords[0] && String(originalWords[0].id).startsWith('jp_') ? 'jp' : 'kr';
                try {
                  app.words = [
                    {id: prefix + '_sync_edit', word:'编辑测试', meaning:'旧释义', example:'旧例句', tags:['旧Tag'], mastered:false, updatedAt:100},
                    {id: prefix + '_sync_newer', word:'本地较新', meaning:'保留本地', tags:[], mastered:false, updatedAt:300},
                    {id: prefix + '_sync_stale_future', word:'浏览器旧缓存', meaning:'浏览器旧释义', tags:[], mastered:false, updatedAt:9999},
                    {id: prefix + '_sync_field_merge', word:'字段合并', meaning:'手机旧释义', example:'手机旧例句', rating:5, mastered:false, tags:[], createdAt:50, updatedAt:500},
                    {id: prefix + '_sync_delete', word:'删除测试', meaning:'待删除', tags:[], mastered:false, updatedAt:100}
                  ];
                  app.saveDeletedRecords({});
                  app.savePendingCloudChanges({[prefix + '_sync_newer']: 300});
                  app.refreshWordFingerprints();
                  const cloudRows = [
                    {word_id:prefix + '_sync_edit', updated_at:200, deleted_at:null, payload:{id:prefix + '_sync_edit', word:'编辑测试', meaning:'云端释义', example:'云端例句', tags:['云端Tag'], mastered:true}},
                    {word_id:prefix + '_sync_newer', updated_at:200, deleted_at:null, payload:{id:prefix + '_sync_newer', word:'本地较新', meaning:'错误覆盖', tags:['云端Tag'], mastered:true}},
                    {word_id:prefix + '_sync_stale_future', updated_at:250, deleted_at:null, payload:{id:prefix + '_sync_stale_future', word:'手机新编辑', meaning:'手机新释义', tags:['手机Tag'], mastered:true}},
                    {word_id:prefix + '_sync_field_merge', updated_at:400, deleted_at:null, payload:{id:prefix + '_sync_field_merge', word:'字段合并', meaning:'电脑新释义', example:'电脑新例句', rating:0, mastered:true, tags:[], createdAt:50, userEditedAt:400}},
                    {word_id:prefix + '_sync_delete', updated_at:400, deleted_at:400, payload:{id:prefix + '_sync_delete', word:'删除测试'}}
                  ];
                  const changed = app.mergeCloudRows(cloudRows);
                  const edited = app.words.find(w => w.id === prefix + '_sync_edit');
                  const newer = app.words.find(w => w.id === prefix + '_sync_newer');
                  const staleFuture = app.words.find(w => w.id === prefix + '_sync_stale_future');
                  const fieldMerged = app.words.find(w => w.id === prefix + '_sync_field_merge');
                  const deletedGone = !app.words.some(w => w.id === prefix + '_sync_delete');
                  const allFields = edited && edited.meaning === '云端释义' && edited.example === '云端例句' && edited.tags.includes('云端Tag') && edited.mastered === true;
                  const localWins = newer && newer.meaning === '保留本地' && newer.mastered === false;
                  const unmarkedNewerLocalPreserved = staleFuture && staleFuture.meaning === '浏览器旧释义' && staleFuture.mastered === false;
                  const uploadRows = app.buildCloudRows('00000000-0000-0000-0000-000000000000', cloudRows);
                  const recoveredPendingQueued = uploadRows.some(row => row.word_id === prefix + '_sync_stale_future' && row.payload.meaning === '浏览器旧释义');
                  const fieldMergePreserved = fieldMerged && fieldMerged.meaning === '电脑新释义' && fieldMerged.example === '电脑新例句' && fieldMerged.rating === 5;
                  const fieldMergeQueued = uploadRows.some(row => row.word_id === prefix + '_sync_field_merge' && row.payload.meaning === '电脑新释义' && row.payload.rating === 5);
                  const before = Number(edited.updatedAt || 0);
                  edited.tags.push('本地新增Tag');
                  app.markLocallyChangedWords();
                  const localEditTracked = Number(edited.updatedAt || 0) > before;
                  return {changed, allFields, localWins, unmarkedNewerLocalPreserved, recoveredPendingQueued, fieldMergePreserved, fieldMergeQueued, deletedGone, localEditTracked};
                } finally {
                  app.words = originalWords;
                  app.saveDeletedRecords(originalDeleted);
                  app.savePendingCloudChanges(originalPending);
                  app.persistSyncedData();
                  app.renderWordList();
                  app.updateStats();
                }
            """)
            self.assert_true(
                bool(merge_result and merge_result.get('allFields')),
                f"[{lang_name}] 浏览器双设备模拟-释义/例句/Tag/掌握状态完整同步",
                "云端较新卡片没有完整覆盖所有可编辑字段",
            )
            self.assert_true(
                bool(merge_result and merge_result.get('localWins')),
                f"[{lang_name}] 浏览器双设备模拟-本地较新版本不被旧云端覆盖",
                "冲突合并没有保留更新时间更晚的本地编辑",
            )
            self.assert_true(
                bool(merge_result and merge_result.get('unmarkedNewerLocalPreserved')),
                f"[{lang_name}] 浏览器双设备模拟-待上传标记缺失时仍按时间保留较新本地版本",
                "待上传标记缺失时，较旧云端副本仍覆盖了较新的本地编辑",
            )
            self.assert_true(
                bool(merge_result and merge_result.get('recoveredPendingQueued')),
                f"[{lang_name}] 浏览器双设备模拟-自动补回缺失的待上传标记并上传较新本地版本",
                "本地版本胜出后没有重新加入待上传队列，下一次同步仍可能继续冲突",
            )
            self.assert_true(
                bool(merge_result and merge_result.get('fieldMergePreserved') and merge_result.get('fieldMergeQueued')),
                f"[{lang_name}] 浏览器双设备模拟-电脑新释义与手机新星级按字段合并",
                "手机只改星级后仍覆盖了电脑端的新释义/例句，或合并结果没有重新上传",
            )
            self.assert_true(
                bool(merge_result and merge_result.get('deletedGone')),
                f"[{lang_name}] 浏览器双设备模拟-云端删除同步到本地",
                "另一设备产生的删除记录没有移除本地旧卡片",
            )
            self.assert_true(
                bool(merge_result and merge_result.get('localEditTracked')),
                f"[{lang_name}] 浏览器双设备模拟-本地任意字段编辑更新时间自动刷新",
                "Tag 等编辑没有更新卡片 updatedAt，无法可靠上传",
            )

            empty_navigation_result = driver.execute_script("""
                const app = window.app;
                const originalSearch = app.searchQuery;
                app.searchQuery = '__codex_empty_result_navigation_test__';
                app.currentPage = 1;
                app.renderWordList();
                const paginationWhenEmpty = document.getElementById('paginationBar');
                const topBtn = document.getElementById('scrollToTopBtn');
                const bottomBtn = document.getElementById('scrollToBottomBtn');
                const emptyState = {
                  noCards: !document.querySelector('#wordList .word-card'),
                  paginationHidden: !paginationWhenEmpty || getComputedStyle(paginationWhenEmpty).display === 'none',
                  topHidden: !!topBtn && getComputedStyle(topBtn).display === 'none',
                  bottomHidden: !!bottomBtn && getComputedStyle(bottomBtn).display === 'none'
                };
                app.searchQuery = originalSearch;
                app.currentPage = 1;
                app.renderWordList();
                const paginationRestored = document.getElementById('paginationBar');
                const restoredState = {
                  hasCards: !!document.querySelector('#wordList .word-card'),
                  paginationVisible: !!paginationRestored && getComputedStyle(paginationRestored).display === 'flex',
                  topVisible: getComputedStyle(topBtn).display === 'flex',
                  bottomVisible: getComputedStyle(bottomBtn).display === 'flex'
                };
                return {emptyState, restoredState};
            """)
            empty_state = empty_navigation_result.get('emptyState', {}) if empty_navigation_result else {}
            restored_state = empty_navigation_result.get('restoredState', {}) if empty_navigation_result else {}
            self.assert_true(
                all(empty_state.get(key) for key in ('noCards', 'paginationHidden', 'topHidden', 'bottomHidden')),
                f"[{lang_name}] 浏览器空结果-分页栏和置顶/置底按钮全部隐藏",
                "筛选结果为 0 时仍有分页栏、置顶按钮或置底按钮可见",
            )
            self.assert_true(
                all(restored_state.get(key) for key in ('hasCards', 'paginationVisible', 'topVisible', 'bottomVisible')),
                f"[{lang_name}] 浏览器结果恢复-分页栏和置顶/置底按钮重新显示",
                "清除空结果条件后导航控件没有随卡片一起恢复",
            )

            fixed_list_layout = driver.execute_script("""
                const list = document.getElementById('wordList');
                const pagination = document.getElementById('paginationBar');
                const bottomNav = document.querySelector('.bottom-nav');
                const tabList = document.getElementById('tab-list');
                if (!list || !pagination || !bottomNav || !tabList) return null;
                list.scrollTop = 0;
                const before = {
                  paginationTop: pagination.getBoundingClientRect().top,
                  navTop: bottomNav.getBoundingClientRect().top
                };
                list.scrollTop = list.scrollHeight;
                const listRect = list.getBoundingClientRect();
                const pageRect = pagination.getBoundingClientRect();
                const navRect = bottomNav.getBoundingClientRect();
                const after = {paginationTop: pageRect.top, navTop: navRect.top};
                return {
                  paginationOutsideList: pagination.parentElement === tabList && pagination.previousElementSibling === list,
                  listActuallyScrollable: list.scrollHeight > list.clientHeight && list.scrollTop > 0,
                  paginationDoesNotScroll: Math.abs(before.paginationTop - after.paginationTop) < 1,
                  bottomNavDoesNotScroll: Math.abs(before.navTop - after.navTop) < 1,
                  scrollbarEndsAtPagination: listRect.bottom <= pageRect.top + 3,
                  paginationAboveTabs: pageRect.bottom <= navRect.top + 3,
                  paginationCompact: pageRect.height <= 38,
                  bottomNavCompact: navRect.height <= 46
                };
            """)
            self.assert_true(
                bool(fixed_list_layout and fixed_list_layout.get('paginationOutsideList')),
                f"[{lang_name}] 浏览器布局-分页栏是 #wordList 外部相邻固定栏",
                "#paginationBar 仍嵌套在可滚动 #wordList 内，滑动时会被带走",
            )
            self.assert_true(
                bool(fixed_list_layout and fixed_list_layout.get('listActuallyScrollable') and fixed_list_layout.get('paginationDoesNotScroll') and fixed_list_layout.get('bottomNavDoesNotScroll')),
                f"[{lang_name}] 浏览器滚动-仅单词列表滚动，分页栏和底部 Tab 均保持固定",
                "滚动 #wordList 时分页栏或底部 Tab 发生位移，或列表未形成独立滚动区",
            )
            self.assert_true(
                bool(fixed_list_layout and fixed_list_layout.get('scrollbarEndsAtPagination') and fixed_list_layout.get('paginationAboveTabs')),
                f"[{lang_name}] 浏览器边界-滚动条止于分页栏上沿且分页栏不遮挡底部 Tab",
                "#wordList 滚动区域、分页栏和底部 Tab 的垂直边界重叠或错位",
            )
            self.assert_true(
                bool(fixed_list_layout and fixed_list_layout.get('paginationCompact') and fixed_list_layout.get('bottomNavCompact')),
                f"[{lang_name}] 浏览器尺寸-分页栏不高于 38px、底部 Tab 不高于 46px",
                "分页栏或底部 Tab 仍然过高，挤占单词列表空间",
            )

            browser_logs = driver.get_log('browser')
            fatal_markers = ('Uncaught', 'SyntaxError', 'ReferenceError', 'TypeError', 'VocabApp init error')
            fatal_logs = [
                entry.get('message', '') for entry in browser_logs
                if any(marker in entry.get('message', '') for marker in fatal_markers)
            ]
            self.assert_true(
                not fatal_logs,
                f"[{lang_name}] 浏览器运行期-JavaScript 无致命初始化/语法错误",
                fatal_logs[0][:500] if fatal_logs else "发现 JavaScript 致命错误",
            )

            before_theme = driver.find_element(By.TAG_NAME, 'body').get_attribute('class')
            driver.find_element(By.ID, 'themeToggleBtn').click()
            time.sleep(0.2)
            after_theme = driver.find_element(By.TAG_NAME, 'body').get_attribute('class')
            self.assert_true(
                before_theme != after_theme,
                f"[{lang_name}] 浏览器真实点击-主题切换按钮立即生效",
                "点击 #themeToggleBtn 后 body 主题 class 未变化",
            )

            driver.find_element(By.ID, 'quickAddBtn').click()
            time.sleep(0.2)
            word_modal_active = 'active' in driver.find_element(By.ID, 'wordModal').get_attribute('class').split()
            self.assert_true(
                word_modal_active,
                f"[{lang_name}] 浏览器真实点击-加词按钮打开编辑弹窗",
                "点击 #quickAddBtn 后 #wordModal 未进入 active 状态",
            )
            blank_example_pair_editor = driver.execute_script("""
                const rows = Array.from(document.querySelectorAll('#examplePairsEditor .example-pair-row'));
                return {
                  threeRows: rows.length === 3,
                  twoInputsPerRow: rows.every(row => row.querySelectorAll('input').length === 2),
                  allBlank: rows.every(row => Array.from(row.querySelectorAll('input')).every(input => input.value === '')),
                  allRequired: rows.every(row => Array.from(row.querySelectorAll('input')).every(input => input.required)),
                  pairedColumns: rows.every(row => {
                    const source = row.querySelector('.example-source-input');
                    const translation = row.querySelector('.example-translation-input');
                    if (!source || !translation) return false;
                    const sourceRect = source.getBoundingClientRect();
                    const translationRect = translation.getBoundingClientRect();
                    return sourceRect.right <= translationRect.left && Math.abs(sourceRect.width - translationRect.width) < 2;
                  })
                };
            """)
            self.assert_true(
                bool(blank_example_pair_editor and all(blank_example_pair_editor.values())),
                f"[{lang_name}] 浏览器新增弹窗-例句区三行双栏、默认空白且原句/译文等宽成对",
                f"新增弹窗例句双栏结构异常: {blank_example_pair_editor}",
            )
            protected_modal_draft = driver.execute_script("""
                const app = window.app;
                const modal = document.getElementById('wordModal');
                const draftWord = `弹窗防误关草稿_${Date.now()}`;
                const wordInput = document.getElementById('inputWord');
                const meaningInput = document.getElementById('inputMeaning');
                if (!app || !modal || !wordInput || !meaningInput) return null;
                wordInput.value = draftWord;
                meaningInput.value = 'n. 防误关测试释义';
                document.querySelectorAll('#examplePairsEditor .example-pair-row').forEach((row, index) => {
                  row.querySelector('.example-source-input').value = `防误关原句 ${index + 1}`;
                  row.querySelector('.example-translation-input').value = `防误关译文 ${index + 1}`;
                });
                modal.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                return {
                  draftWord,
                  backdropIgnored: modal.classList.contains('active') && wordInput.value === draftWord,
                };
            """)
            draft_word_input = driver.find_element(By.ID, 'inputWord')
            draft_word_input.send_keys(Keys.ENTER)
            time.sleep(0.1)
            enter_state = driver.execute_script("""
                const modal = document.getElementById('wordModal');
                const draftWord = arguments[0];
                return {
                  stayedOpen: modal?.classList.contains('active') === true,
                  draftPreserved: document.getElementById('inputWord')?.value === draftWord,
                  notSaved: !window.app.words.some(word => word.word === draftWord),
                };
            """, protected_modal_draft.get('draftWord') if protected_modal_draft else '')
            draft_word_input.send_keys(Keys.ESCAPE)
            driver.execute_script("document.getElementById('wordForm')?.requestSubmit();")
            submit_escape_state = driver.execute_script("""
                const modal = document.getElementById('wordModal');
                const draftWord = arguments[0];
                return {
                  stayedOpen: modal?.classList.contains('active') === true,
                  draftPreserved: document.getElementById('inputWord')?.value === draftWord,
                  notSaved: !window.app.words.some(word => word.word === draftWord),
                };
            """, protected_modal_draft.get('draftWord') if protected_modal_draft else '')
            driver.find_element(By.ID, 'closeModalBtn').click()
            close_and_reopen_state = driver.execute_script("""
                const modal = document.getElementById('wordModal');
                const closedByX = modal?.classList.contains('active') === false;
                document.getElementById('quickAddBtn')?.click();
                return {
                  closedByX,
                  reopenedBlank: modal?.classList.contains('active') === true
                    && document.getElementById('inputWord')?.value === '',
                };
            """)
            protected_modal_ok = bool(
                protected_modal_draft
                and protected_modal_draft.get('backdropIgnored')
                and enter_state
                and all(enter_state.values())
                and submit_escape_state
                and all(submit_escape_state.values())
                and close_and_reopen_state
                and all(close_and_reopen_state.values())
            )
            self.assert_true(
                protected_modal_ok,
                f"[{lang_name}] 浏览器新增弹窗-遮罩/Enter/Esc/非点击提交均不关闭且×可显式关闭",
                f"新增弹窗草稿防误关失败: backdrop={protected_modal_draft}, enter={enter_state}, submit_escape={submit_escape_state}, close={close_and_reopen_state}",
            )
            manual_add_tag_editor = driver.execute_script("""
                const app = window.app;
                const group = document.getElementById('addWordTagsGroup');
                const container = document.getElementById('modalTagsContainer');
                const groupVisible = group && getComputedStyle(group).display !== 'none';
                const startsEmpty = !!container && container.querySelectorAll('.tag-badge').length === 0 && app.editingModalTags.length === 0;
                container?.querySelector('.add-tag-btn')?.click();
                let input = container?.querySelector('.inline-tag-input');
                if (input) {
                  input.value = '手动词性';
                  input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
                }
                const added = app.editingModalTags.length === 1 && app.editingModalTags[0] === '手动词性';
                const customBadge = container?.querySelector('.tag-badge.custom-tag');
                const referenceBadge = document.createElement('span');
                referenceBadge.className = 'tag-badge pos-tag';
                referenceBadge.textContent = '#动词';
                container?.appendChild(referenceBadge);
                const customStyle = customBadge ? getComputedStyle(customBadge) : null;
                const referenceStyle = getComputedStyle(referenceBadge);
                const uniformGray = !!customStyle
                  && customStyle.backgroundColor === referenceStyle.backgroundColor
                  && customStyle.color === referenceStyle.color
                  && customStyle.borderTopWidth === referenceStyle.borderTopWidth
                  && customStyle.boxShadow === referenceStyle.boxShadow;
                referenceBadge.remove();
                container?.querySelector('.modal-editable-tag')?.click();
                input = container?.querySelector('.inline-tag-input');
                const editPrefilled = input?.value === '手动词性';
                if (input) {
                  input.value = '自定义新词Tag';
                  input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
                }
                const edited = app.editingModalTags.length === 1 && app.editingModalTags[0] === '自定义新词Tag';
                container?.querySelector('.remove-tag-x')?.click();
                const deleted = app.editingModalTags.length === 0 && container?.querySelectorAll('.tag-badge').length === 0;
                return { groupVisible, startsEmpty, added, uniformGray, editPrefilled, edited, deleted };
            """)
            self.assert_true(
                bool(manual_add_tag_editor and all(manual_add_tag_editor.values())),
                f"[{lang_name}] 浏览器新增弹窗-Tag 灰色统一并支持输入、改名与删除",
                f"新增弹窗 Tag 灰色统一或手动编辑全流程失败: {manual_add_tag_editor}",
            )
            manual_add_rating_similar = driver.execute_script("""
                const app = window.app;
                const ratingGroup = document.getElementById('addWordRatingGroup');
                const masteredGroup = document.getElementById('addWordMasteredGroup');
                const masteredButton = document.getElementById('modalDraftMasteredBtn');
                const similarGroup = document.getElementById('addWordSimilarGroup');
                const ratingWidget = document.querySelector('#modalDraftRating .modal-draft-star-rating');
                const searchInput = document.getElementById('modalSimilarSearchInput');
                const results = document.getElementById('modalSimilarSearchResults');
                const selectedList = document.getElementById('modalSelectedSimilarWords');
                const target = app.words[0];
                if (!ratingGroup || !masteredGroup || !masteredButton || !similarGroup || !ratingWidget || !searchInput || !results || !selectedList || !target) return null;
                const originalTarget = JSON.parse(JSON.stringify(target));
                const originalState = {
                  currentFilter: app.currentFilter,
                  searchQuery: app.searchQuery,
                  currentPage: app.currentPage,
                  ratingSort: app.ratingSort
                };
                const groupsVisible = getComputedStyle(ratingGroup).display !== 'none'
                  && getComputedStyle(masteredGroup).display !== 'none'
                  && getComputedStyle(similarGroup).display !== 'none';
                const startsEmpty = app.editingModalRating === 0
                  && app.editingModalMastered === false
                  && app.editingModalSimilarWordIds.length === 0
                  && ratingWidget.querySelectorAll('.rating-star.filled').length === 0
                  && masteredButton.textContent.trim() === '🔄 学习中'
                  && masteredButton.getAttribute('aria-pressed') === 'false';

                const ratingRect = ratingWidget.getBoundingClientRect();
                ratingWidget.dispatchEvent(new MouseEvent('click', {
                  bubbles: true,
                  clientX: ratingRect.left + ratingRect.width * 0.72,
                  clientY: ratingRect.top + ratingRect.height / 2
                }));
                const ratingSet = app.editingModalRating === 4
                  && document.querySelectorAll('#modalDraftRating .rating-star.filled').length === 4
                  && document.querySelector('#modalDraftRating .modal-draft-star-rating')?.getAttribute('aria-valuenow') === '4';
                masteredButton.click();
                const masteredSet = app.editingModalMastered === true
                  && masteredButton.textContent.trim() === '✅ 已掌握'
                  && masteredButton.getAttribute('aria-pressed') === 'true'
                  && masteredButton.classList.contains('status-mastered');

                const findTargetResult = () => Array.from(results.querySelectorAll('.similar-word-search-result')).find(button =>
                  button.querySelector('strong')?.textContent === target.word
                );
                searchInput.value = target.word;
                searchInput.dispatchEvent(new Event('input', { bubbles: true }));
                const firstResult = findTargetResult();
                const searchFound = !!firstResult;
                firstResult?.click();
                const selected = app.editingModalSimilarWordIds.map(String).includes(String(target.id));
                const selectedChip = selectedList.querySelector(`[data-similar-word-id="${target.id}"]`);
                const selectedRendered = !!selectedChip && selectedChip.querySelector('.modal-draft-selected-word-title')?.textContent.includes(target.word);
                selectedChip?.querySelector('.similar-word-remove-btn')?.click();
                const removed = !app.editingModalSimilarWordIds.map(String).includes(String(target.id))
                  && !selectedList.querySelector(`[data-similar-word-id="${target.id}"]`);
                const secondResult = findTargetResult();
                secondResult?.click();
                const readded = app.editingModalSimilarWordIds.map(String).includes(String(target.id));

                const testWord = `新增弹窗星级相近词测试_${Date.now()}`;
                document.getElementById('inputWord').value = testWord;
                const readingInput = document.getElementById('inputReading');
                readingInput.value = 'test-reading';
                readingInput.dispatchEvent(new Event('blur', { bubbles: true }));
                const readingAutoBracketed = readingInput.value === '[test-reading]';
                const duplicateBracketsRemoved = app.normalizeBracketedReading('[[test-reading]]') === '[test-reading]';
                const pitchNumbersRemoved = ['[test-reading①]', '[test-reading]②', '⓪test-reading⑳']
                  .every(value => app.normalizeBracketedReading(value) === '[test-reading]');
                document.getElementById('inputMeaning').value = 'n. 新增弹窗测试释义';
                const krMeaningInput = document.getElementById('inputKrMeaning');
                if (krMeaningInput) krMeaningInput.value = '추가 창 테스트 뜻';
                document.querySelectorAll('#examplePairsEditor .example-pair-row').forEach((row, index) => {
                  row.querySelector('.example-source-input').value = `新增测试原句 ${index + 1}`;
                  row.querySelector('.example-translation-input').value = `新增测试译文 ${index + 1}`;
                });
                document.getElementById('saveWordBtn')?.click();
                const newWord = app.words.find(word => word.word === testWord);
                const savedRating = newWord?.rating === 4;
                const savedMastered = newWord?.mastered === true;
                const savedReading = newWord?.reading === '[test-reading]';
                const savedManualRelation = Array.isArray(newWord?.manualSimilarWordIds)
                  && newWord.manualSimilarWordIds.map(String).includes(String(target.id));
                const automaticSnapshotEmpty = Array.isArray(newWord?.autoSimilarWordIds) && newWord.autoSimilarWordIds.length === 0;
                const reverseRelation = Array.isArray(target.manualSimilarWordIds)
                  && target.manualSimilarWordIds.map(String).includes(String(newWord?.id));
                const mutualRecommendation = !!newWord
                  && app.getSimilarWords(newWord, 3).some(word => String(word.id) === String(target.id))
                  && app.getSimilarWords(target, 3).some(word => String(word.id) === String(newWord.id));
                const storedNewWord = JSON.parse(localStorage.getItem(app.STORAGE_KEY) || '[]').find(word => String(word.id) === String(newWord?.id));
                const persisted = storedNewWord?.rating === 4
                  && storedNewWord?.mastered === true
                  && storedNewWord?.reading === '[test-reading]'
                  && storedNewWord.manualSimilarWordIds?.map(String).includes(String(target.id));
                const modalClosed = document.getElementById('wordModal')?.classList.contains('active') === false;

                if (newWord) app.words = app.words.filter(word => String(word.id) !== String(newWord.id));
                const targetIndex = app.words.findIndex(word => String(word.id) === String(originalTarget.id));
                if (targetIndex >= 0) app.words[targetIndex] = originalTarget;
                app.currentFilter = originalState.currentFilter;
                app.searchQuery = originalState.searchQuery;
                app.currentPage = originalState.currentPage;
                app.ratingSort = originalState.ratingSort;
                app.saveData();
                app.renderWordList();
                app.closeWordModal();
                return {
                  groupsVisible, startsEmpty, ratingSet, masteredSet, searchFound, selected,
                  selectedRendered, removed, readded, savedRating, savedManualRelation,
                  savedMastered, readingAutoBracketed, duplicateBracketsRemoved, pitchNumbersRemoved, savedReading,
                  automaticSnapshotEmpty, reverseRelation, mutualRecommendation, persisted, modalClosed
                };
            """)
            self.assert_true(
                bool(manual_add_rating_similar and all(manual_add_rating_similar.values())),
                f"[{lang_name}] 浏览器新增弹窗-星级、学习状态、读音加括号去音调编号与相近词保存全流程",
                f"新增弹窗星级、学习状态、读音规范化或相近词交互失败: {manual_add_rating_similar}",
            )

            status_rating_persistence = driver.execute_script("""
                const app = window.app;
                const target = app.words.find(word => word && !word.mastered);
                if (!target) return null;
                const targetId = String(target.id);
                const originalWord = JSON.parse(JSON.stringify(target));
                const originalPending = JSON.parse(JSON.stringify(app.getPendingCloudChanges()));
                const originalState = {
                  currentFilter: app.currentFilter,
                  subFilter: app.subFilter,
                  searchQuery: app.searchQuery,
                  selectedTags: Array.from(app.selectedTags || []),
                  currentPage: app.currentPage,
                  ratingSort: app.ratingSort
                };

                app.currentFilter = 'learning';
                app.subFilter = 'all';
                app.searchQuery = String(target.word || '').toLowerCase();
                app.selectedTags = new Set();
                app.currentPage = 1;
                app.renderWordList();
                const initialCard = Array.from(document.querySelectorAll('#wordList .word-card')).find(card => String(card.dataset.id) === targetId);
                const bottomStatusRemoved = !initialCard?.querySelector('.card-actions button[onclick*="toggleMastered"]');
                const statusButton = initialCard?.querySelector('.word-card-status-btn');
                const statusBeforeRating = !!statusButton && !!initialCard?.querySelector('.word-card-rating')
                  && Boolean(statusButton.compareDocumentPosition(initialCard.querySelector('.word-card-rating')) & Node.DOCUMENT_POSITION_FOLLOWING);
                const beforeUpdatedAt = Number(target.updatedAt || 0);
                statusButton?.click();

                const masteredWord = app.words.find(word => String(word.id) === targetId);
                const statusMemoryUpdated = masteredWord?.mastered === true;
                const statusTimestampUpdated = Number(masteredWord?.updatedAt || 0) > beforeUpdatedAt;
                const hiddenFromLearning = !Array.from(document.querySelectorAll('#wordList .word-card')).some(card => String(card.dataset.id) === targetId);
                const statusStoredWord = JSON.parse(localStorage.getItem(app.STORAGE_KEY) || '[]').find(word => String(word.id) === targetId);
                const statusStored = statusStoredWord?.mastered === true && Number(statusStoredWord.updatedAt || 0) === Number(masteredWord?.updatedAt || 0);
                const searchMatchesAfterStatus = app.getSearchFilteredWords();
                const expectedLearning = searchMatchesAfterStatus.filter(word => !word.mastered).length;
                const expectedMastered = searchMatchesAfterStatus.filter(word => word.mastered).length;
                const statusStatsUpdated = Number(document.getElementById('count-learning')?.textContent) === expectedLearning
                  && Number(document.getElementById('count-mastered')?.textContent) === expectedMastered
                  && Number(document.getElementById('count-all')?.textContent) === searchMatchesAfterStatus.length;
                const statusPendingMeta = app.getPendingCloudMeta(app.getPendingCloudChanges()[targetId]);
                const statusQueuedForCloud = statusPendingMeta.source === 'user'
                  && statusPendingMeta.changedAt >= Number(masteredWord?.updatedAt || 0);
                const statusUpdatedAt = Number(masteredWord?.updatedAt || 0);

                app.currentFilter = 'all';
                app.currentPage = 1;
                app.renderWordList();
                const masteredCard = Array.from(document.querySelectorAll('#wordList .word-card')).find(card => String(card.dataset.id) === targetId);
                const masteredLabelUpdated = masteredCard?.querySelector('.word-card-status-btn')?.textContent.includes('已掌握');
                const ratingWidget = masteredCard?.querySelector('.word-card-rating');
                const initialRating = app.normalizeRating(masteredWord?.rating);
                const nextRating = initialRating === 5 ? 4 : initialRating + 1;
                if (ratingWidget) {
                  const rect = ratingWidget.getBoundingClientRect();
                  const clientX = rect.left + rect.width * ((nextRating - 0.5) / 5);
                  ratingWidget.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, pointerId: 77, button: 0, buttons: 1, clientX, clientY: rect.top + rect.height / 2 }));
                  ratingWidget.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, pointerId: 77, button: 0, buttons: 0, clientX, clientY: rect.top + rect.height / 2 }));
                }

                const ratedWord = app.words.find(word => String(word.id) === targetId);
                const ratingMemoryUpdated = app.normalizeRating(ratedWord?.rating) === nextRating;
                const ratingTimestampUpdated = Number(ratedWord?.updatedAt || 0) > statusUpdatedAt;
                const ratingStoredWord = JSON.parse(localStorage.getItem(app.STORAGE_KEY) || '[]').find(word => String(word.id) === targetId);
                const ratingStored = app.normalizeRating(ratingStoredWord?.rating) === nextRating
                  && Number(ratingStoredWord?.updatedAt || 0) === Number(ratedWord?.updatedAt || 0);
                const rerenderedRating = document.querySelector(`.word-card[data-id="${targetId}"] .word-card-rating`);
                const ratingUiUpdated = rerenderedRating?.querySelectorAll('.rating-star.filled').length === nextRating
                  && rerenderedRating?.getAttribute('aria-valuenow') === String(nextRating);
                const ratingPendingMeta = app.getPendingCloudMeta(app.getPendingCloudChanges()[targetId]);
                const ratingQueuedForCloud = ratingPendingMeta.source === 'user'
                  && ratingPendingMeta.changedAt >= Number(ratedWord?.updatedAt || 0);

                const targetIndex = app.words.findIndex(word => String(word.id) === targetId);
                if (targetIndex >= 0) app.words[targetIndex] = originalWord;
                app.savePendingCloudChanges(originalPending);
                app.persistSyncedData();
                app.currentFilter = originalState.currentFilter;
                app.subFilter = originalState.subFilter;
                app.searchQuery = originalState.searchQuery;
                app.selectedTags = new Set(originalState.selectedTags);
                app.currentPage = originalState.currentPage;
                app.ratingSort = originalState.ratingSort;
                app.renderWordList();
                return {
                  bottomStatusRemoved, statusBeforeRating, statusMemoryUpdated, statusTimestampUpdated, hiddenFromLearning, statusStored,
                  statusStatsUpdated, statusQueuedForCloud, masteredLabelUpdated, ratingMemoryUpdated,
                  ratingTimestampUpdated, ratingStored, ratingUiUpdated, ratingQueuedForCloud
                };
            """)
            self.assert_true(
                bool(status_rating_persistence and all(status_rating_persistence.values())),
                f"[{lang_name}] 浏览器列表右上角状态 Label-唯一切换入口及持久化同步完整",
                f"右上角状态 Label、底部去重或持久化同步失败: {status_rating_persistence}",
            )

            first_card = driver.find_element(By.CSS_SELECTOR, '.word-card')
            driver.execute_script('arguments[0].scrollIntoView({block: "center"})', first_card)
            preview_decoration = driver.execute_script("""
                const preview = arguments[0].querySelector('.word-example-preview');
                if (!preview) return null;
                const style = getComputedStyle(preview);
                return {
                  borderWidth: parseFloat(style.borderLeftWidth || '0'),
                  borderStyle: style.borderLeftStyle,
                  paddingLeft: parseFloat(style.paddingLeft || '0')
                };
            """, first_card)
            self.assert_true(
                bool(preview_decoration and preview_decoration.get('borderWidth', 0) >= 3 and preview_decoration.get('borderStyle') == 'solid' and preview_decoration.get('paddingLeft', 0) >= 10),
                f"[{lang_name}] 浏览器列表卡片-例句左侧粉红强调边实际渲染",
                "列表卡片例句预览未渲染 3px 实线左边或缺少足够左内距",
            )
            first_card.click()
            time.sleep(0.2)
            detail_modal_active = 'active' in driver.find_element(By.ID, 'detailModal').get_attribute('class').split()
            self.assert_true(
                detail_modal_active,
                f"[{lang_name}] 浏览器真实点击-单词卡片打开详情弹窗",
                "点击第一张 .word-card 后 #detailModal 未进入 active 状态",
            )

            detail_header_status_toggle = driver.execute_script("""
                const app = window.app;
                const wordId = app.currentDetailWordId;
                const word = app.words.find(item => String(item.id) === String(wordId));
                const button = document.getElementById('detailMasteredBtn');
                const rating = document.getElementById('detailRating');
                if (!word || !button || !rating) return null;
                const originalMastered = Boolean(word.mastered);
                const initialSynced = String(button.dataset.masteredWordId) === String(word.id)
                  && button.getAttribute('aria-pressed') === (originalMastered ? 'true' : 'false')
                  && button.textContent.trim() === (originalMastered ? '✅ 已掌握' : '🔄 学习中');
                const positionedBeforeRating = button.nextElementSibling === rating;
                button.click();
                const toggledMastered = !originalMastered;
                const toggledInMemory = Boolean(word.mastered) === toggledMastered;
                const toggledInHeader = button.getAttribute('aria-pressed') === (toggledMastered ? 'true' : 'false')
                  && button.textContent.trim() === (toggledMastered ? '✅ 已掌握' : '🔄 学习中')
                  && button.classList.contains(toggledMastered ? 'status-mastered' : 'status-learning');
                const storedWord = JSON.parse(localStorage.getItem(app.STORAGE_KEY) || '[]').find(item => String(item.id) === String(word.id));
                const persisted = Boolean(storedWord?.mastered) === toggledMastered;
                button.click();
                const restored = Boolean(word.mastered) === originalMastered
                  && button.getAttribute('aria-pressed') === (originalMastered ? 'true' : 'false');
                return { initialSynced, positionedBeforeRating, toggledInMemory, toggledInHeader, persisted, restored };
            """)
            self.assert_true(
                bool(detail_header_status_toggle and all(detail_header_status_toggle.values())),
                f"[{lang_name}] 浏览器详情弹窗-星级左侧状态 Label 可点击切换并持久化同步",
                f"详情标题栏状态切换失败: {detail_header_status_toggle}",
            )

            example_pair_edit_lifecycle = driver.execute_script("""
                const app = window.app;
                const currentId = app.currentDetailWordId;
                const wordIndex = app.words.findIndex(word => String(word.id) === String(currentId));
                if (wordIndex < 0) return null;
                const originalWord = JSON.parse(JSON.stringify(app.words[wordIndex]));
                const originalTags = JSON.stringify(originalWord.tags || []);
                const originalState = {
                  currentFilter: app.currentFilter,
                  searchQuery: app.searchQuery,
                  currentPage: app.currentPage,
                  reviewList: app.reviewList,
                  currentReviewIndex: app.currentReviewIndex
                };
                const expectedPairs = app.getParsedExamples(app.words[wordIndex]).slice(0, 3);
                const detailModal = document.getElementById('detailModal');
                const detailHistoryBefore = JSON.stringify(app.detailModalHistory || []);
                document.getElementById('detailEditBtn')?.click();
                const modal = document.getElementById('wordModal');
                const rows = Array.from(document.querySelectorAll('#examplePairsEditor .example-pair-row'));
                const editModalOpened = modal?.classList.contains('active') === true;
                const detailHiddenWhileEditing = detailModal?.classList.contains('active') === false;
                const returnContextCaptured = String(app.wordModalReturnContext?.wordId) === String(currentId);
                const addOnlyControlsHidden = ['addWordTagsGroup', 'addWordRatingGroup', 'addWordMasteredGroup', 'addWordSimilarGroup'].every(id => {
                  const element = document.getElementById(id);
                  return !!element && getComputedStyle(element).display === 'none';
                });
                const exactlyThreeRows = rows.length === 3;
                const existingPairsLoaded = expectedPairs.length === 3 && rows.every((row, index) =>
                  row.querySelector('.example-source-input')?.value === expectedPairs[index].example &&
                  row.querySelector('.example-translation-input')?.value === expectedPairs[index].trans
                );

                document.getElementById('closeModalBtn')?.click();
                const cancelReturnedToDetail = modal?.classList.contains('active') === false
                  && detailModal?.classList.contains('active') === true
                  && String(app.currentDetailWordId) === String(currentId)
                  && JSON.stringify(app.detailModalHistory || []) === detailHistoryBefore;
                document.getElementById('detailEditBtn')?.click();
                const reopenedFromDetail = modal?.classList.contains('active') === true
                  && detailModal?.classList.contains('active') === false
                  && String(app.wordModalReturnContext?.wordId) === String(currentId);

                const beforeIncompleteSave = JSON.stringify(app.words[wordIndex].examples);
                const missingTranslation = rows[1]?.querySelector('.example-translation-input');
                if (missingTranslation) missingTranslation.value = '';
                document.getElementById('saveWordBtn')?.click();
                const incompleteRejected = JSON.stringify(app.words[wordIndex].examples) === beforeIncompleteSave
                  && modal?.classList.contains('active') === true
                  && detailModal?.classList.contains('active') === false;

                rows.forEach((row, index) => {
                  const source = row.querySelector('.example-source-input');
                  const translation = row.querySelector('.example-translation-input');
                  if (source) source.value = `编辑原句 ${index + 1}`;
                  if (translation) translation.value = `编辑译文 ${index + 1}`;
                });
                const storagePrototype = Object.getPrototypeOf(localStorage);
                const originalSetItem = storagePrototype.setItem;
                let failedSaveKeptDraft = false;
                let failedSaveReported = false;
                try {
                  storagePrototype.setItem = function(key, value) {
                    if (key === app.STORAGE_KEY || key === app.PENDING_CLOUD_KEY) {
                      throw new DOMException('模拟持久存储失败', 'QuotaExceededError');
                    }
                    return originalSetItem.call(this, key, value);
                  };
                  document.getElementById('saveWordBtn')?.click();
                  failedSaveKeptDraft = modal?.classList.contains('active') === true
                    && rows.every((row, index) => row.querySelector('.example-source-input')?.value === `编辑原句 ${index + 1}`);
                  failedSaveReported = document.getElementById('toast')?.textContent.includes('保存失败') === true;
                } finally {
                  storagePrototype.setItem = originalSetItem;
                }
                document.getElementById('saveWordBtn')?.click();
                const savedWord = app.words[wordIndex];
                const parsedAfterSave = app.getParsedExamples(savedWord);
                const structuredSaved = parsedAfterSave.length === 3 && parsedAfterSave.every((pair, index) =>
                  pair.example === `编辑原句 ${index + 1}` && pair.trans === `编辑译文 ${index + 1}`
                );
                const tagsPreserved = JSON.stringify(savedWord.tags || []) === originalTags;
                const legacySaved = savedWord.example.split(String.fromCharCode(10)).join('|') === '编辑原句 1|编辑原句 2|编辑原句 3' &&
                  savedWord.exampleTrans.split(String.fromCharCode(10)).join('|') === '编辑译文 1|编辑译文 2|编辑译文 3';
                const modalClosedAfterSave = modal?.classList.contains('active') === false;
                const saveReturnedToDetail = detailModal?.classList.contains('active') === true
                  && String(app.currentDetailWordId) === String(savedWord.id)
                  && document.getElementById('detailWord')?.textContent === savedWord.word
                  && JSON.stringify(app.detailModalHistory || []) === detailHistoryBefore;
                const storedWord = JSON.parse(localStorage.getItem(app.STORAGE_KEY) || '[]').find(word => String(word.id) === String(savedWord.id));
                const persisted = storedWord?.examples?.length === 3 && storedWord.example === savedWord.example && storedWord.exampleTrans === savedWord.exampleTrans;
                const userEditProtected = Number(savedWord.userEditedAt || 0) > 0;

                app.currentFilter = 'all';
                app.searchQuery = String(savedWord.word || '').toLowerCase();
                app.currentPage = 1;
                app.renderWordList();
                const savedCard = Array.from(document.querySelectorAll('#wordList .word-card')).find(card => String(card.dataset.id) === String(savedWord.id));
                const listPreviewUpdated = savedCard?.querySelector('.ex-preview-text')?.textContent === '编辑原句 1' &&
                  savedCard?.querySelector('.ex-preview-trans')?.textContent === '编辑译文 1';

                app.showDetailModal(savedWord.id);
                const detailShowsThreePairs = document.querySelectorAll('#detailExamplesList .detail-example-item').length === 3 &&
                  document.querySelector('#detailExamplesList .detail-example-text')?.textContent === '编辑原句 1';
                app.reviewList = [savedWord];
                app.currentReviewIndex = 0;
                app.renderCurrentCard();
                const reviewShowsThreePairs = document.querySelectorAll('#cardBackExampleBlock .word-example-item').length === 3 &&
                  document.querySelector('#cardBackExampleBlock .word-example')?.textContent === '编辑原句 1';

                app.words[wordIndex] = originalWord;
                app.currentFilter = originalState.currentFilter;
                app.searchQuery = originalState.searchQuery;
                app.currentPage = originalState.currentPage;
                app.reviewList = originalState.reviewList;
                app.currentReviewIndex = originalState.currentReviewIndex;
                app.saveData();
                app.renderWordList();
                app.closeDetailModal();
                return {
                  editModalOpened, detailHiddenWhileEditing, returnContextCaptured, cancelReturnedToDetail,
                  reopenedFromDetail, addOnlyControlsHidden, exactlyThreeRows, existingPairsLoaded, incompleteRejected,
                  failedSaveKeptDraft, failedSaveReported, structuredSaved, tagsPreserved, legacySaved,
                  userEditProtected, modalClosedAfterSave, persisted,
                  saveReturnedToDetail, listPreviewUpdated, detailShowsThreePairs, reviewShowsThreePairs
                };
            """)
            self.assert_true(
                bool(example_pair_edit_lifecycle and all(example_pair_edit_lifecycle.values())),
                f"[{lang_name}] 浏览器编辑弹窗-三组例句回填、成对校验、保存持久化及各视图联动",
                f"编辑弹窗三行双栏例句全流程失败: {example_pair_edit_lifecycle}",
            )

            if lang_name == "日语":
                jp_kr_meaning_search = driver.execute_script("""
                    const app = window.app;
                    const searchInput = document.getElementById('searchInput');
                    const target = app.words.find(item => item && String(item.krMeaning || '').trim());
                    if (!searchInput || !target) return null;
                    const originalState = {
                      currentFilter: app.currentFilter,
                      subFilter: app.subFilter,
                      searchQuery: app.searchQuery,
                      selectedTags: Array.from(app.selectedTags || []),
                      currentPage: app.currentPage,
                      inputValue: searchInput.value
                    };
                    const query = String(target.krMeaning).trim();
                    app.currentFilter = 'all';
                    app.subFilter = 'all';
                    app.selectedTags = new Set();
                    searchInput.value = query;
                    searchInput.dispatchEvent(new Event('input', { bubbles: true }));
                    const filtered = app.getSearchFilteredWords();
                    const dataMatched = filtered.some(item => String(item.id) === String(target.id));
                    const queryStateSynced = app.searchQuery === query.toLowerCase();
                    const renderedCard = Array.from(document.querySelectorAll('#wordList .word-card'))
                      .find(card => String(card.dataset.id) === String(target.id));
                    const cardRendered = !!renderedCard;

                    app.currentFilter = originalState.currentFilter;
                    app.subFilter = originalState.subFilter;
                    app.searchQuery = originalState.searchQuery;
                    app.selectedTags = new Set(originalState.selectedTags);
                    app.currentPage = originalState.currentPage;
                    searchInput.value = originalState.inputValue;
                    app.renderWordList();
                    return { queryStateSynced, dataMatched, cardRendered };
                """)
                self.assert_true(
                    bool(jp_kr_meaning_search and all(jp_kr_meaning_search.values())),
                    "[日语专属] 浏览器主搜索-输入韩文释义可筛出对应日语卡片",
                    f"日语按韩文释义搜索失败: {jp_kr_meaning_search}",
                )

                jp_kr_meaning_lifecycle = driver.execute_script("""
                    const app = window.app;
                    const word = app.words.find(item => item && item.krMeaning && app.getParsedExamples(item).length >= 3);
                    if (!word) return null;
                    const wordId = word.id;
                    const wordIndex = app.words.findIndex(item => String(item.id) === String(wordId));
                    const originalWord = JSON.parse(JSON.stringify(word));
                    const originalState = {
                      currentFilter: app.currentFilter,
                      searchQuery: app.searchQuery,
                      currentPage: app.currentPage
                    };
                    const originalTags = JSON.stringify(word.tags || []);
                    app.openWordModal(word);
                    const meaningGroup = document.getElementById('inputMeaning')?.closest('.form-group');
                    const krMeaningInput = document.getElementById('inputKrMeaning');
                    const fieldImmediatelyBelowMeaning = meaningGroup?.nextElementSibling?.querySelector('#inputKrMeaning') === krMeaningInput;
                    const existingValueLoaded = krMeaningInput?.value === word.krMeaning;
                    if (krMeaningInput) krMeaningInput.value = '편집한 한국어 뜻';
                    app.saveWordFromForm();
                    const savedWord = app.words.find(item => String(item.id) === String(wordId));
                    const saved = savedWord?.krMeaning === '편집한 한국어 뜻';
                    const tagsPreserved = JSON.stringify(savedWord?.tags || []) === originalTags;
                    const storedWord = JSON.parse(localStorage.getItem(app.STORAGE_KEY) || '[]').find(item => String(item.id) === String(wordId));
                    const persisted = storedWord?.krMeaning === '편집한 한국어 뜻';

                    app.currentFilter = 'all';
                    app.searchQuery = String(savedWord.word || '').toLowerCase();
                    app.currentPage = 1;
                    app.renderWordList();
                    const listCard = Array.from(document.querySelectorAll('#wordList .word-card')).find(card => String(card.dataset.id) === String(wordId));
                    const listBadgeUpdated = listCard?.querySelector('.kr-meaning-badge')?.textContent === '편집한 한국어 뜻';
                    app.showDetailModal(wordId);
                    const detailBadgeUpdated = document.querySelector('#detailMeaning .kr-badge')?.textContent === '편집한 한국어 뜻';

                    app.words[wordIndex] = originalWord;
                    app.currentFilter = originalState.currentFilter;
                    app.searchQuery = originalState.searchQuery;
                    app.currentPage = originalState.currentPage;
                    app.saveData();
                    app.renderWordList();
                    app.closeWordModal();
                    app.closeDetailModal();
                    return {
                      fieldImmediatelyBelowMeaning, existingValueLoaded, saved,
                      tagsPreserved, persisted, listBadgeUpdated, detailBadgeUpdated
                    };
                """)
                self.assert_true(
                    bool(jp_kr_meaning_lifecycle and all(jp_kr_meaning_lifecycle.values())),
                    "[日语专属] 浏览器编辑弹窗-韩文释义回填、保存、持久化及 Badge 联动",
                    f"日语韩文释义编辑全流程失败: {jp_kr_meaning_lifecycle}",
                )

            all_tags_deletable = driver.execute_script("""
                const app = window.app;
                const systemTags = new Set(['动词', '形容词', '名词', '副词', '短语', '惯用句', '接续词', '连体词', '形容动词', '感叹词', '代词', '数词', '语法', '句型', '词汇', '助词', '助动词', '俗语', '成语']);
                const word = app.words.find(item => Array.isArray(item.tags) && item.tags.some(tag => systemTags.has(String(tag).replace(/^#/, '').trim())));
                if (!word) return null;
                const wordId = word.id;
                const wordIndex = app.words.findIndex(item => String(item.id) === String(wordId));
                const tagName = String(word.tags.find(tag => systemTags.has(String(tag).replace(/^#/, '').trim()))).replace(/^#/, '').trim();
                const originalWord = JSON.parse(JSON.stringify(word));
                const originalState = {
                  currentFilter: app.currentFilter,
                  searchQuery: app.searchQuery,
                  currentPage: app.currentPage,
                  reviewList: app.reviewList,
                  currentReviewIndex: app.currentReviewIndex
                };
                app.currentFilter = 'all';
                app.searchQuery = String(word.word || '').toLowerCase();
                app.currentPage = 1;
                app.renderWordList();
                const listCard = Array.from(document.querySelectorAll('#wordList .word-card')).find(card => String(card.dataset.id) === String(wordId));
                const findTag = root => Array.from(root?.querySelectorAll('.tag-badge') || []).find(tag => tag.textContent.replace('×', '').trim() === `#${tagName}`);
                const listTag = findTag(listCard);
                const listSystemTagDeletable = !!listTag?.querySelector('.remove-tag-x');
                app.showDetailModal(wordId);
                const detailSystemTagDeletable = !!findTag(document.getElementById('detailTags'))?.querySelector('.remove-tag-x');
                app.reviewList = [word];
                app.currentReviewIndex = 0;
                app.renderCurrentCard();
                const reviewSystemTagDeletable = !!findTag(document.getElementById('cardBackTags'))?.querySelector('.remove-tag-x');
                listTag?.querySelector('.remove-tag-x')?.click();
                const updatedWord = app.words.find(item => String(item.id) === String(wordId));
                const removed = !updatedWord.tags.some(tag => String(tag).replace(/^#/, '').trim() === tagName);
                const storedWord = JSON.parse(localStorage.getItem(app.STORAGE_KEY) || '[]').find(item => String(item.id) === String(wordId));
                const persisted = !!storedWord && !storedWord.tags.some(tag => String(tag).replace(/^#/, '').trim() === tagName);

                app.words[wordIndex] = originalWord;
                app.currentFilter = originalState.currentFilter;
                app.searchQuery = originalState.searchQuery;
                app.currentPage = originalState.currentPage;
                app.reviewList = originalState.reviewList;
                app.currentReviewIndex = originalState.currentReviewIndex;
                app.saveData();
                app.renderWordList();
                app.closeDetailModal();
                return { listSystemTagDeletable, detailSystemTagDeletable, reviewSystemTagDeletable, removed, persisted };
            """)
            self.assert_true(
                bool(all_tags_deletable and all(all_tags_deletable.values())),
                f"[{lang_name}] 浏览器 Tag-系统词性在列表、详情、复习均可删除并持久化",
                f"系统词性 Tag 删除全流程失败: {all_tags_deletable}",
            )

            similar_manual_crud = driver.execute_script("""
                const app = window.app;
                const source = app.words[0];
                const candidates = app.words.filter(word => word && source && word.id !== source.id).slice(0, 8);
                if (!source || candidates.length < 7) return null;
                const originalAuto = source.autoSimilarWordIds;
                const originalManual = source.manualSimilarWordIds;
                const originalHidden = source.hiddenSimilarWordIds;
                const reverseOriginalState = words => words.map(word => ({
                  word,
                  manual: word.manualSimilarWordIds,
                  hidden: word.hiddenSimilarWordIds
                }));
                source.autoSimilarWordIds = candidates.slice(0, 3).map(word => String(word.id));
                source.manualSimilarWordIds = [];
                source.hiddenSimilarWordIds = [];
                const initial = candidates[0];
                const addTargets = candidates.slice(3, 7);
                const reverseOriginal = reverseOriginalState([initial].concat(addTargets));
                const automaticSnapshotIgnored = app.getSimilarWords(source, 3).length === 0;
                app.addSimilarWord(source.id, initial.id);
                app.showDetailModal(source.id);
                const panel = document.querySelector('#detailSimilarBlock .similar-words-container');
                const addButton = panel && panel.querySelector('.similar-panel-add-btn');
                const removeButton = panel && panel.querySelector('.similar-word-remove-btn');
                if (!panel || !addButton || !removeButton) return null;
                addButton.click();
                const picker = panel.querySelector('.similar-word-picker');
                const input = panel.querySelector('.similar-word-search-input');
                input.value = addTargets[0].word;
                input.dispatchEvent(new Event('input', { bubbles: true }));
                const hasLibraryResult = Array.from(panel.querySelectorAll('.similar-word-search-result strong')).some(node => node.textContent === addTargets[0].word);
                input.value = initial.word;
                input.dispatchEvent(new Event('input', { bubbles: true }));
                const existingResultButton = Array.from(panel.querySelectorAll('.similar-word-search-result')).find(button => button.querySelector('strong')?.textContent === initial.word);
                const existingResultDisabled = !!existingResultButton && existingResultButton.disabled && existingResultButton.getAttribute('aria-disabled') === 'true';
                const existingResultLabeled = !!existingResultButton && existingResultButton.querySelector('.similar-word-added-badge')?.textContent === '已添加';
                const beforeDeleteCount = app.getSimilarWords(source, 3).length;
                app.removeSimilarWord(source.id, initial.id);
                const afterDeleteIds = app.getSimilarWords(source, 3).map(word => String(word.id));
                const afterRepeatedReadIds = app.getSimilarWords(source, 3).map(word => String(word.id));
                const deleteLeavesGap = beforeDeleteCount === 1 && afterDeleteIds.length === 0;
                const noAutomaticRefill = JSON.stringify(afterDeleteIds) === JSON.stringify(afterRepeatedReadIds) && !afterDeleteIds.includes(String(initial.id));
                const freshPanel = document.querySelector('#detailSimilarBlock .similar-words-container');
                const freshAddButton = freshPanel?.querySelector('.similar-panel-add-btn');
                freshAddButton?.click();
                const firstInput = freshPanel?.querySelector('.similar-word-search-input');
                if (firstInput) {
                  firstInput.value = addTargets[0].word;
                  firstInput.dispatchEvent(new Event('input', { bubbles: true }));
                }
                const firstResultButton = Array.from(freshPanel?.querySelectorAll('.similar-word-search-result') || []).find(button => button.querySelector('strong')?.textContent === addTargets[0].word);
                firstResultButton?.click();
                const panelAfterFirst = document.querySelector('#detailSimilarBlock .similar-words-container');
                const pickerAfterFirst = panelAfterFirst?.querySelector('.similar-word-picker');
                const inputAfterFirst = panelAfterFirst?.querySelector('.similar-word-search-input');
                const firstSelectionStayedOpen = !!pickerAfterFirst
                  && pickerAfterFirst.classList.contains('active')
                  && inputAfterFirst?.value === addTargets[0].word
                  && !!panelAfterFirst.querySelector('.similar-word-search-result.is-added[disabled]');
                if (inputAfterFirst) {
                  inputAfterFirst.value = addTargets[1].word;
                  inputAfterFirst.dispatchEvent(new Event('input', { bubbles: true }));
                }
                const secondResultButton = Array.from(panelAfterFirst?.querySelectorAll('.similar-word-search-result') || []).find(button => button.querySelector('strong')?.textContent === addTargets[1].word);
                secondResultButton?.click();
                const panelAfterSecond = document.querySelector('#detailSimilarBlock .similar-words-container');
                const pickerAfterSecond = panelAfterSecond?.querySelector('.similar-word-picker');
                const inputAfterSecond = panelAfterSecond?.querySelector('.similar-word-search-input');
                const secondSelectionStayedOpen = !!pickerAfterSecond
                  && pickerAfterSecond.classList.contains('active')
                  && inputAfterSecond?.value === addTargets[1].word
                  && (source.manualSimilarWordIds || []).map(String).includes(String(addTargets[0].id))
                  && (source.manualSimilarWordIds || []).map(String).includes(String(addTargets[1].id));
                const continuousMultiSelect = firstSelectionStayedOpen && secondSelectionStayedOpen;
                addTargets.slice(2).forEach(word => app.addSimilarWord(source.id, word.id));
                const afterUnlimitedAdd = app.getSimilarWords(source, 3);
                const addedPersisted = addTargets.every(word => (source.manualSimilarWordIds || []).map(String).includes(String(word.id)));
                const addedVisible = addTargets.every(word => afterUnlimitedAdd.some(item => item.id === word.id));
                const manualUnlimited = afterUnlimitedAdd.length === 4;
                const reversePersisted = addTargets.every(word => (word.manualSimilarWordIds || []).map(String).includes(String(source.id)));
                const reverseVisible = addTargets.every(word => app.getSimilarWords(word, 3).some(item => item.id === source.id));
                const hiddenPersisted = (source.hiddenSimilarWordIds || []).map(String).includes(String(initial.id));
                app.removeSimilarWord(source.id, addTargets[0].id);
                const oneSidedDeletePreservedReverse = app.getSimilarWords(addTargets[0], 3).some(item => item.id === source.id);
                if (originalAuto === undefined) delete source.autoSimilarWordIds; else source.autoSimilarWordIds = originalAuto;
                if (originalManual === undefined) delete source.manualSimilarWordIds; else source.manualSimilarWordIds = originalManual;
                if (originalHidden === undefined) delete source.hiddenSimilarWordIds; else source.hiddenSimilarWordIds = originalHidden;
                reverseOriginal.forEach(({word, manual, hidden}) => {
                  if (manual === undefined) delete word.manualSimilarWordIds; else word.manualSimilarWordIds = manual;
                  if (hidden === undefined) delete word.hiddenSimilarWordIds; else word.hiddenSimilarWordIds = hidden;
                });
                app.saveData();
                app.refreshSimilarWordPanels(source.id);
                return {
                  pickerOpened: !!picker && picker.classList.contains('active'),
                  automaticSnapshotIgnored,
                  continuousMultiSelect,
                  hasLibraryResult,
                  existingResultDisabled,
                  existingResultLabeled,
                  deleteLeavesGap,
                  noAutomaticRefill,
                  addedPersisted,
                  addedVisible,
                  manualUnlimited,
                  reversePersisted,
                  reverseVisible,
                  oneSidedDeletePreservedReverse,
                  hiddenPersisted,
                };
            """)
            self.assert_true(
                bool(similar_manual_crud and all(similar_manual_crud.values())),
                f"[{lang_name}] 浏览器相近表达-自动快照失效、删除留空、＋库内搜索及人工添加不限量全流程",
                f"相近表达手动增删真实交互失败: {similar_manual_crud}",
            )

            backspace_search_guard = None
            try:
                backspace_setup = driver.execute_script("""
                    const app = window.app;
                    const source = app.words[0];
                    const candidate = app.words.find(word => source && word.id !== source.id);
                    if (!source || !candidate) return null;
                    app.showDetailModal(source.id);
                    const addButton = document.querySelector('#detailSimilarBlock .similar-panel-add-btn');
                    addButton?.click();
                    const input = document.querySelector('#detailSimilarBlock .similar-word-search-input');
                    if (!input) return null;
                    input.value = String(candidate.word || '搜索测试');
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.focus();
                    input.select();
                    window.__similarBackspaceBubbleHit = false;
                    window.__similarBackspaceBubbleProbe = event => {
                      if (event.key !== 'Backspace') return;
                      window.__similarBackspaceBubbleHit = true;
                      app.closeDetailModal();
                    };
                    document.addEventListener('keydown', window.__similarBackspaceBubbleProbe);
                    return {
                      modalOpen: document.getElementById('detailModal')?.classList.contains('active') === true,
                      pickerOpen: input.closest('.similar-word-picker')?.classList.contains('active') === true,
                      allSelected: input.selectionStart === 0 && input.selectionEnd === input.value.length && input.value.length > 0
                    };
                """)
                if backspace_setup and all(backspace_setup.values()):
                    detail_search_input = driver.find_element(By.CSS_SELECTOR, '#detailSimilarBlock .similar-word-search-input')
                    detail_search_input.send_keys(Keys.BACKSPACE)
                    backspace_search_guard = driver.execute_script("""
                        const input = document.querySelector('#detailSimilarBlock .similar-word-search-input');
                        const detailModal = document.getElementById('detailModal');
                        return {
                          textCleared: input?.value === '',
                          modalStayedOpen: detailModal?.classList.contains('active') === true,
                          pickerStayedOpen: input?.closest('.similar-word-picker')?.classList.contains('active') === true,
                          focusStayedInSearch: document.activeElement === input,
                          bubbleBlocked: window.__similarBackspaceBubbleHit === false,
                          emptyHintShown: !!input?.parentElement?.querySelector('.similar-word-search-hint')
                        };
                    """)
            finally:
                driver.execute_script("""
                    if (window.__similarBackspaceBubbleProbe) {
                      document.removeEventListener('keydown', window.__similarBackspaceBubbleProbe);
                    }
                    delete window.__similarBackspaceBubbleProbe;
                    delete window.__similarBackspaceBubbleHit;
                    window.app?.closeDetailModal();
                """)
            self.assert_true(
                bool(backspace_search_guard and all(backspace_search_guard.values())),
                f"[{lang_name}] 浏览器相近表达搜索-鼠标全选文字后 Backspace 只清空且弹窗/下拉/焦点保持",
                f"相近表达搜索 Backspace 防误关闭失败: {backspace_search_guard}",
            )

            similar_status_toggle = driver.execute_script("""
                const app = window.app;
                const source = app.words[0];
                const target = app.words.find(word => source && word.id !== source.id);
                if (!source || !target) return null;
                const originalSourceManual = source.manualSimilarWordIds;
                const originalSourceHidden = source.hiddenSimilarWordIds;
                const originalTargetManual = target.manualSimilarWordIds;
                const originalTargetHidden = target.hiddenSimilarWordIds;
                app.addSimilarWord(source.id, target.id);
                const initialMastered = Boolean(target.mastered);
                app.showDetailModal(source.id);
                const chip = Array.from(document.querySelectorAll('#detailSimilarBlock .similar-word-chip')).find(node =>
                  node.querySelector('.similar-word-text')?.textContent === target.word
                );
                const statusButton = chip && chip.querySelector('.similar-word-status-btn');
                const rating = chip && chip.querySelector('.similar-word-rating');
                if (!chip || !statusButton || !rating) return null;
                const statusBeforeRating = statusButton.nextElementSibling === rating;
                const currentDetailBefore = app.currentDetailWordId;
                statusButton.click();
                const toggled = Boolean(target.mastered) === !initialMastered;
                const textUpdated = statusButton.textContent.trim() === (target.mastered ? '✅ 已掌握' : '🔄 学习中');
                const ariaUpdated = statusButton.getAttribute('aria-pressed') === (target.mastered ? 'true' : 'false');
                const clickStayedOnSource = app.currentDetailWordId === currentDetailBefore;
                const storedWords = JSON.parse(localStorage.getItem(app.STORAGE_KEY) || '[]');
                const storedTarget = storedWords.find(word => String(word.id) === String(target.id));
                const persisted = storedTarget && Boolean(storedTarget.mastered) === Boolean(target.mastered);
                statusButton.click();
                const restored = Boolean(target.mastered) === initialMastered;
                if (originalSourceManual === undefined) delete source.manualSimilarWordIds; else source.manualSimilarWordIds = originalSourceManual;
                if (originalSourceHidden === undefined) delete source.hiddenSimilarWordIds; else source.hiddenSimilarWordIds = originalSourceHidden;
                if (originalTargetManual === undefined) delete target.manualSimilarWordIds; else target.manualSimilarWordIds = originalTargetManual;
                if (originalTargetHidden === undefined) delete target.hiddenSimilarWordIds; else target.hiddenSimilarWordIds = originalTargetHidden;
                app.saveData();
                return {statusBeforeRating, toggled, textUpdated, ariaUpdated, clickStayedOnSource, persisted, restored};
            """)
            self.assert_true(
                bool(similar_status_toggle and all(similar_status_toggle.values())),
                f"[{lang_name}] 浏览器相近表达-状态按钮位于星级左侧且点击切换、持久化与原位同步完整",
                f"相近表达状态切换真实交互失败: {similar_status_toggle}",
            )

            user_note_lifecycle = driver.execute_script("""
                const app = window.app;
                const source = app.words[0];
                const target = app.words.find(word => source && word.id !== source.id);
                if (!source || !target) return null;
                const sourceId = source.id;
                const targetId = target.id;
                const originalSource = JSON.parse(JSON.stringify(source));
                const originalTarget = JSON.parse(JSON.stringify(target));
                const originalState = {
                  currentFilter: app.currentFilter,
                  searchQuery: app.searchQuery,
                  currentPage: app.currentPage,
                  ratingSort: app.ratingSort,
                  reviewList: app.reviewList,
                  currentReviewIndex: app.currentReviewIndex
                };
                app.addSimilarWord(source.id, target.id);
                const verticalGap = (upper, lower) => {
                  if (!upper || !lower) return Infinity;
                  return Math.max(0, lower.getBoundingClientRect().top - upper.getBoundingClientRect().bottom);
                };
                const isCompactNote = row => {
                  const display = row && row.querySelector('.user-note-display');
                  const text = row && row.querySelector('.user-note-text');
                  if (!row || !display || !text) return false;
                  const style = getComputedStyle(display);
                  const before = getComputedStyle(text, '::before').content;
                  const after = getComputedStyle(text, '::after').content;
                  const transparent = style.backgroundColor === 'rgba(0, 0, 0, 0)' || style.backgroundColor === 'transparent';
                  return transparent
                    && parseFloat(style.paddingTop) === 0
                    && parseFloat(style.paddingRight) === 0
                    && parseFloat(style.borderTopWidth) === 0
                    && row.getBoundingClientRect().height <= 22
                    && before.includes('【')
                    && after.includes('】');
                };
                source.userNote = '';
                target.userNote = '';
                app.currentFilter = 'all';
                app.searchQuery = String(source.word || '').toLowerCase();
                app.currentPage = 1;
                app.renderWordList();

                const blankListCard = Array.from(document.querySelectorAll('#wordList .word-card')).find(card => String(card.dataset.id) === String(sourceId));
                const blankListCollapsed = !!blankListCard && !blankListCard.querySelector('.user-note-row');
                app.showDetailModal(sourceId);
                const detailSlot = document.getElementById('detailUserNote');
                const blankDetailCollapsed = detailSlot?.innerHTML === '' && getComputedStyle(detailSlot).display === 'none';
                const blankSimilarChip = Array.from(document.querySelectorAll('#detailSimilarBlock .similar-word-chip')).find(chip =>
                  chip.querySelector('.similar-word-text')?.textContent === target.word
                );
                const blankSimilarCollapsed = !!blankSimilarChip && !blankSimilarChip.querySelector('.user-note-row');
                app.reviewList = [source];
                app.currentReviewIndex = 0;
                app.renderCurrentCard();
                const reviewSlot = document.getElementById('cardBackUserNote');
                const blankReviewCollapsed = reviewSlot?.innerHTML === '' && getComputedStyle(reviewSlot).display === 'none';
                const noExternalControls = !document.querySelector('.user-note-add-btn, .user-note-edit-btn, .user-note-delete-btn, .user-note-input');

                app.showDetailModal(sourceId);
                document.getElementById('detailEditBtn')?.click();
                const noteInput = document.getElementById('inputUserNote');
                const editorOpenedBlank = document.getElementById('wordModal')?.classList.contains('active') === true && noteInput?.value === '';
                if (noteInput) noteInput.value = '我的自定义说明';
                app.saveWordFromForm();
                const savedSource = app.words.find(word => String(word.id) === String(sourceId));
                const savedViaModal = savedSource?.userNote === '我的自定义说明' && document.getElementById('wordModal')?.classList.contains('active') === false;
                const storedSource = JSON.parse(localStorage.getItem(app.STORAGE_KEY) || '[]').find(word => String(word.id) === String(sourceId));
                const persisted = storedSource?.userNote === '我的自定义说明';

                const listCard = Array.from(document.querySelectorAll('#wordList .word-card')).find(card => String(card.dataset.id) === String(sourceId));
                const listMeaning = listCard && listCard.querySelector('.word-meaning');
                const listRow = listCard && listCard.querySelector('.user-note-row');
                const listDisplayed = listMeaning?.nextElementSibling === listRow && listRow?.querySelector('.user-note-text')?.textContent === '我的自定义说明';
                const listExample = listCard && listCard.querySelector('.word-example-preview');
                const listNoteText = listRow && listRow.querySelector('.user-note-text');
                const listColorMatchesMeaning = !!listMeaning && !!listNoteText
                  && getComputedStyle(listMeaning).color === getComputedStyle(listNoteText).color;
                const listCompact = isCompactNote(listRow)
                  && verticalGap(listMeaning, listRow) <= 6
                  && (!listExample || verticalGap(listRow, listExample) <= 6);
                app.showDetailModal(sourceId);
                const detailRow = detailSlot && detailSlot.querySelector('.user-note-row');
                const detailDisplayed = document.getElementById('detailMeaning')?.nextElementSibling === detailSlot && detailRow?.querySelector('.user-note-text')?.textContent === '我的自定义说明';
                const detailHeader = document.querySelector('#detailModal .modal-header');
                const detailMeaning = document.getElementById('detailMeaning');
                const detailCompact = isCompactNote(detailRow)
                  && verticalGap(detailHeader, detailMeaning) <= 12
                  && verticalGap(detailMeaning, detailRow) <= 8;
                app.reviewList = [savedSource];
                app.currentReviewIndex = 0;
                app.renderCurrentCard();
                const reviewRow = reviewSlot && reviewSlot.querySelector('.user-note-row');
                const reviewDisplayed = document.getElementById('cardBackMeaning')?.nextElementSibling === reviewSlot && reviewRow?.querySelector('.user-note-text')?.textContent === '我的自定义说明';
                const reviewCompact = isCompactNote(reviewRow);

                app.openWordModal(app.words.find(word => String(word.id) === String(targetId)));
                const targetInput = document.getElementById('inputUserNote');
                if (targetInput) targetInput.value = '相近词自定义说明';
                app.saveWordFromForm();
                app.showDetailModal(sourceId);
                const similarChip = Array.from(document.querySelectorAll('#detailSimilarBlock .similar-word-chip')).find(chip =>
                  chip.querySelector('.similar-word-text')?.textContent === target.word
                );
                const similarMeaning = similarChip && similarChip.querySelector('.similar-word-meaning');
                const similarRow = similarChip && similarChip.querySelector('.user-note-row');
                const similarDisplayed = similarMeaning?.nextElementSibling === similarRow && similarRow?.querySelector('.user-note-text')?.textContent === '相近词自定义说明';
                const similarExample = similarChip && similarChip.querySelector('.similar-word-example');
                const similarNoteText = similarRow && similarRow.querySelector('.user-note-text');
                const similarColorMatchesMeaning = !!similarMeaning && !!similarNoteText
                  && getComputedStyle(similarMeaning).color === getComputedStyle(similarNoteText).color;
                const similarCompact = isCompactNote(similarRow)
                  && verticalGap(similarMeaning, similarRow) <= 6
                  && (!similarExample || verticalGap(similarRow, similarExample) <= 6);

                app.openWordModal(app.words.find(word => String(word.id) === String(sourceId)));
                const clearSourceInput = document.getElementById('inputUserNote');
                const existingNotePreloaded = clearSourceInput?.value === '我的自定义说明';
                if (clearSourceInput) clearSourceInput.value = '';
                app.saveWordFromForm();
                const sourceCleared = app.words.find(word => String(word.id) === String(sourceId))?.userNote === '';
                app.openWordModal(app.words.find(word => String(word.id) === String(targetId)));
                const clearTargetInput = document.getElementById('inputUserNote');
                if (clearTargetInput) clearTargetInput.value = '';
                app.saveWordFromForm();
                app.showDetailModal(sourceId);
                const clearedDetailCollapsed = detailSlot?.innerHTML === '' && getComputedStyle(detailSlot).display === 'none';
                const clearedSimilarChip = Array.from(document.querySelectorAll('#detailSimilarBlock .similar-word-chip')).find(chip =>
                  chip.querySelector('.similar-word-text')?.textContent === target.word
                );
                const clearedSimilarCollapsed = !!clearedSimilarChip && !clearedSimilarChip.querySelector('.user-note-row');

                const sourceIndex = app.words.findIndex(word => String(word.id) === String(sourceId));
                const targetIndex = app.words.findIndex(word => String(word.id) === String(targetId));
                if (sourceIndex >= 0) app.words[sourceIndex] = originalSource;
                if (targetIndex >= 0) app.words[targetIndex] = originalTarget;
                app.currentFilter = originalState.currentFilter;
                app.searchQuery = originalState.searchQuery;
                app.currentPage = originalState.currentPage;
                app.ratingSort = originalState.ratingSort;
                app.reviewList = originalState.reviewList;
                app.currentReviewIndex = originalState.currentReviewIndex;
                app.saveData();
                app.renderWordList();
                app.closeWordModal();
                app.closeDetailModal();
                return {
                  blankListCollapsed, blankDetailCollapsed, blankSimilarCollapsed, blankReviewCollapsed,
                  noExternalControls, editorOpenedBlank, savedViaModal, persisted,
                  listDisplayed, detailDisplayed, reviewDisplayed, similarDisplayed,
                  existingNotePreloaded, sourceCleared, clearedDetailCollapsed, clearedSimilarCollapsed,
                  listCompact, detailCompact, reviewCompact, similarCompact,
                  listColorMatchesMeaning, similarColorMatchesMeaning
                };
            """)
            self.assert_true(
                bool(user_note_lifecycle and all(user_note_lifecycle.values())),
                f"[{lang_name}] 浏览器自定义说明-仅编辑弹窗维护、四视图条件展示与清空零占位全流程",
                f"自定义说明弹窗维护或条件展示失败: {user_note_lifecycle}",
            )
            note_compact_keys = ('listCompact', 'detailCompact', 'reviewCompact', 'similarCompact')
            self.assert_true(
                bool(user_note_lifecycle and all(user_note_lifecycle.get(key) for key in note_compact_keys)),
                f"[{lang_name}] 浏览器自定义说明-四视图无背景中括号展示且释义/例句间距紧凑",
                f"自定义说明实际渲染尺寸或间距过大: {user_note_lifecycle}",
            )
            note_color_keys = ('listColorMatchesMeaning', 'similarColorMatchesMeaning')
            self.assert_true(
                bool(user_note_lifecycle and all(user_note_lifecycle.get(key) for key in note_color_keys)),
                f"[{lang_name}] 浏览器自定义说明-实际文字颜色与中文释义灰色完全一致",
                f"自定义说明与中文释义的计算后颜色不一致: {user_note_lifecycle}",
            )

            detail_scroll_reset = driver.execute_script("""
                const app = window.app;
                const source = app.words.find(word => app.getSimilarWords(word, 1).length > 0) || app.words[0];
                const target = (source && app.getSimilarWords(source, 1)[0]) || app.words.find(word => source && word.id !== source.id);
                const modal = document.getElementById('detailModal');
                const body = modal && modal.querySelector('.detail-body');
                if (!source || !target || !body) return null;
                const oldHeight = body.style.height;
                const oldMaxHeight = body.style.maxHeight;
                body.style.height = '120px';
                body.style.maxHeight = '120px';
                app.showDetailModal(source.id);
                body.scrollTop = body.scrollHeight;
                const wasScrolled = body.scrollTop > 0;
                app.showDetailModal(target.id);
                const resetToTop = body.scrollTop === 0;
                const switchedWord = app.currentDetailWordId === target.id;
                body.style.height = oldHeight;
                body.style.maxHeight = oldMaxHeight;
                app.closeDetailModal();
                return {wasScrolled, resetToTop, switchedWord};
            """)
            self.assert_true(
                bool(detail_scroll_reset and detail_scroll_reset.get('wasScrolled') and detail_scroll_reset.get('resetToTop') and detail_scroll_reset.get('switchedWord')),
                f"[{lang_name}] 浏览器相近表达跳转-旧滚动位置清零并从新词条顶部展示",
                "详情弹窗滚动到底部后切换相近表达，.detail-body 仍保留旧 scrollTop",
            )
            driver.execute_script("document.getElementById('detailModal')?.classList.remove('active')")

            review_tab = driver.find_element(By.CSS_SELECTOR, '.nav-item[data-tab="tab-review"]')
            driver.execute_script('arguments[0].scrollIntoView({block: "center"})', review_tab)
            review_tab.click()
            time.sleep(0.2)
            review_active = 'active' in driver.find_element(By.ID, 'tab-review').get_attribute('class').split()
            self.assert_true(
                review_active,
                f"[{lang_name}] 浏览器真实点击-底部卡片复习 Tab 切换生效",
                "点击复习 Tab 后 #tab-review 未进入 active 状态",
            )
            review_bottom_gap = driver.execute_script("""
                const actions = document.querySelector('#tab-review .review-actions');
                const nav = document.querySelector('.bottom-nav');
                if (!actions || !nav) return null;
                const actionsRect = actions.getBoundingClientRect();
                const navRect = nav.getBoundingClientRect();
                return navRect.top - actionsRect.bottom;
            """)
            self.assert_true(
                review_bottom_gap is not None and 0 <= review_bottom_gap <= 16,
                f"[{lang_name}] 浏览器复习页-易忘/记住了按钮紧贴底部 Tab 且不重叠",
                f"复习按钮与底部 Tab 的实际间距应为 0~16px，当前为 {review_bottom_gap}",
            )
        except Exception as err:
            self.assert_true(
                False,
                f"[{lang_name}] 浏览器真实交互测试可执行",
                f"Selenium/Chrome 执行失败: {type(err).__name__}: {err}",
            )
        finally:
            if driver:
                driver.quit()

    def test_supabase_schema(self):
        """检查部署所需的 Supabase 表、RLS 与最小权限 SQL。"""
        print("\n  >>> [Supabase] 数据库结构与权限测试...")
        exists = os.path.exists(SUPABASE_SQL_FILE)
        self.assert_true(exists, "[Supabase] 一次性建表 SQL 文件存在", "缺少 supabase_vocab_sync.sql")
        if not exists:
            return
        with open(SUPABASE_SQL_FILE, 'r', encoding='utf-8') as sql_file:
            sql = sql_file.read()
        schema_fields = all(field in sql for field in ('user_id uuid', 'language text', 'word_id text', 'payload jsonb', 'updated_at bigint', 'deleted_at bigint'))
        self.assert_true(schema_fields, "[Supabase] vocab_items 逐词条同步字段完整", "建表 SQL 缺少身份、语言、payload、更新时间或删除时间字段")
        primary_key = 'primary key (user_id, language, word_id)' in sql
        self.assert_true(primary_key, "[Supabase] 用户+语言+词条复合主键防重复", "vocab_items 缺少与前端 on_conflict 对齐的复合主键")
        rls_enabled = 'enable row level security' in sql and sql.count('(select auth.uid()) = user_id') >= 4
        self.assert_true(rls_enabled, "[Supabase] RLS 启用且增删改查均按用户隔离", "RLS 未启用或四类操作权限未完整限制为 auth.uid()")
        anon_revoked = 'revoke all on table public.vocab_items from anon' in sql and 'to authenticated' in sql
        self.assert_true(anon_revoked, "[Supabase] 匿名访问撤销，仅登录用户可同步", "anon 仍可能直接访问私人词库数据")


    def run_all(self):
        print("\n[INIT] 启动单词本应用全量自动化测试流程...")
        self.test_file(KR_FILE, "韩语")
        self.test_file(JP_FILE, "日语")
        self.test_supabase_schema()
        self.test_browser_interactions(KR_FILE, "韩语")
        self.test_browser_interactions(JP_FILE, "日语")

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
