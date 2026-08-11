/* ==========================================================================
   随身单词记忆本 - Application Logic
   ========================================================================== */

class VocabApp {
  constructor() {
    this.STORAGE_KEY = 'evie_vocab_data_v1';
    this.THEME_KEY = 'evie_vocab_theme';
    this.words = [];
    
    // Review mode state
    this.reviewList = [];
    this.currentReviewIndex = 0;
    this.currentFilter = 'all';
    this.searchQuery = '';

    this.init();
  }

  init() {
    this.loadData();
    this.loadTheme();
    this.bindEvents();
    this.renderWordList();
    this.updateStats();
    
    // If empty data on first launch, offer sample prompt or load default
    if (this.words.length === 0) {
      this.loadSampleData('korean', false); // Silently load Korean sample for immediate great experience
    }
  }

  /* ------------------------------------------------------------------------
     Data Engine & LocalStorage
     ------------------------------------------------------------------------ */
  loadData() {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      this.words = stored ? JSON.parse(stored) : [];
    } catch (e) {
      console.error('Failed to load local data:', e);
      this.words = [];
    }
  }

  saveData() {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.words));
      this.updateStats();
    } catch (e) {
      this.showToast('⚠️ 保存失败，可能超出了存储限制');
    }
  }

  loadTheme() {
    const savedTheme = localStorage.getItem(this.THEME_KEY);
    if (savedTheme === 'light') {
      document.body.classList.add('light-theme');
      document.getElementById('themeToggleBtn').textContent = '☀️';
    } else {
      document.body.classList.remove('light-theme');
      document.getElementById('themeToggleBtn').textContent = '🌙';
    }
  }

  toggleTheme() {
    document.body.classList.toggle('light-theme');
    const isLight = document.body.classList.contains('light-theme');
    localStorage.setItem(this.THEME_KEY, isLight ? 'light' : 'dark');
    document.getElementById('themeToggleBtn').textContent = isLight ? '☀️' : '🌙';
  }

  /* ------------------------------------------------------------------------
     Event Handlers
     ------------------------------------------------------------------------ */
  bindEvents() {
    // Navigation Tabs
    document.querySelectorAll('.bottom-nav .nav-item').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const targetTab = btn.getAttribute('data-tab');
        if (targetTab) {
          this.switchTab(targetTab);
        } else if (btn.id === 'navAddBtn') {
          this.openWordModal();
        }
      });
    });

    // Header buttons
    document.getElementById('themeToggleBtn').addEventListener('click', () => this.toggleTheme());
    document.getElementById('quickAddBtn').addEventListener('click', () => this.openWordModal());

    // Search and Filter
    document.getElementById('searchInput').addEventListener('input', (e) => {
      this.searchQuery = e.target.value.trim().toLowerCase();
      this.renderWordList();
    });

    document.getElementById('filterPills').addEventListener('click', (e) => {
      const pill = e.target.closest('.pill-btn');
      if (!pill) return;
      document.querySelectorAll('.pill-btn').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      this.currentFilter = pill.getAttribute('data-filter');
      this.renderWordList();
    });

    // Word Form Modal Submit
    document.getElementById('wordForm').addEventListener('submit', (e) => {
      e.preventDefault();
      this.saveWordFromForm();
    });

    document.getElementById('closeModalBtn').addEventListener('click', () => this.closeWordModal());
    document.getElementById('wordModal').addEventListener('click', (e) => {
      if (e.target.id === 'wordModal') this.closeWordModal();
    });

    // Flashcard Flip Interaction
    const flashcard = document.getElementById('flashcard');
    document.getElementById('flashcardScene').addEventListener('click', () => {
      flashcard.classList.toggle('is-flipped');
    });

    // Flashcard Speech Button
    document.getElementById('cardSpeakFrontBtn').addEventListener('click', (e) => {
      e.stopPropagation();
      const currentWord = this.reviewList[this.currentReviewIndex];
      if (currentWord) this.speakWord(currentWord.word);
    });

    // Review Assessment Buttons
    document.getElementById('btnForgot').addEventListener('click', () => this.assessReview('forgot'));
    document.getElementById('btnFuzzy').addEventListener('click', () => this.assessReview('fuzzy'));
    document.getElementById('btnRemembered').addEventListener('click', () => this.assessReview('remembered'));

    // Data Management Events
    document.getElementById('exportDataBtn').addEventListener('click', () => this.exportJSON());
    document.getElementById('importDataTriggerBtn').addEventListener('click', () => {
      document.getElementById('importFileInput').click();
    });
    document.getElementById('importFileInput').addEventListener('change', (e) => this.importJSON(e));
    document.getElementById('clearDataBtn').addEventListener('click', () => this.clearAllData());
  }

  switchTab(tabId) {
    document.querySelectorAll('.tab-view').forEach(view => view.classList.remove('active'));
    document.querySelectorAll('.bottom-nav .nav-item').forEach(nav => nav.classList.remove('active'));

    const activeView = document.getElementById(tabId);
    if (activeView) activeView.classList.add('active');

    const activeNav = document.querySelector(`.bottom-nav .nav-item[data-tab="${tabId}"]`);
    if (activeNav) activeNav.classList.add('active');

    if (tabId === 'tab-review') {
      this.startReviewSession();
    }
  }

  /* ------------------------------------------------------------------------
     Word Operations (CRUD)
     ------------------------------------------------------------------------ */
  openWordModal(word = null) {
    const modal = document.getElementById('wordModal');
    const form = document.getElementById('wordForm');
    const title = document.getElementById('modalTitle');

    form.reset();

    if (word) {
      title.textContent = '编辑单词';
      document.getElementById('wordId').value = word.id;
      document.getElementById('inputWord').value = word.word || '';
      document.getElementById('inputReading').value = word.reading || '';
      document.getElementById('inputMeaning').value = word.meaning || '';
      document.getElementById('inputExample').value = word.example || '';
      document.getElementById('inputExampleTrans').value = word.exampleTrans || '';
      document.getElementById('inputTags').value = (word.tags || []).join(', ');
      document.getElementById('inputNotes').value = word.notes || '';
    } else {
      title.textContent = '添加新单词';
      document.getElementById('wordId').value = '';
    }

    modal.classList.add('active');
  }

  closeWordModal() {
    document.getElementById('wordModal').classList.remove('active');
  }

  saveWordFromForm() {
    const id = document.getElementById('wordId').value;
    const wordText = document.getElementById('inputWord').value.trim();
    const reading = document.getElementById('inputReading').value.trim();
    const meaning = document.getElementById('inputMeaning').value.trim();
    const example = document.getElementById('inputExample').value.trim();
    const exampleTrans = document.getElementById('inputExampleTrans').value.trim();
    const tagsRaw = document.getElementById('inputTags').value.trim();
    const notes = document.getElementById('inputNotes').value.trim();

    if (!wordText || !meaning) {
      this.showToast('请填写单词与释义');
      return;
    }

    const tags = tagsRaw ? tagsRaw.split(/[,，]/).map(t => t.trim()).filter(Boolean) : [];

    if (id) {
      // Update
      const index = this.words.findIndex(w => w.id === id);
      if (index !== -1) {
        this.words[index] = {
          ...this.words[index],
          word: wordText,
          reading,
          meaning,
          example,
          exampleTrans,
          tags,
          notes,
          updatedAt: Date.now()
        };
        this.showToast('✅ 单词修改成功');
      }
    } else {
      // Add New
      const newWord = {
        id: 'word_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4),
        word: wordText,
        reading,
        meaning,
        example,
        exampleTrans,
        tags,
        notes,
        mastered: false,
        reviewCount: 0,
        createdAt: Date.now()
      };
      this.words.unshift(newWord);
      this.showToast('🎉 新单词添加成功');
    }

    this.saveData();
    this.renderWordList();
    this.closeWordModal();
  }

  toggleMastered(id) {
    const word = this.words.find(w => w.id === id);
    if (word) {
      word.mastered = !word.mastered;
      this.saveData();
      this.renderWordList();
      this.showToast(word.mastered ? '🌟 已标记为已掌握' : '📖 已标记为学习中');
    }
  }

  deleteWord(id) {
    if (confirm('确定要删除这个单词吗？')) {
      this.words = this.words.filter(w => w.id !== id);
      this.saveData();
      this.renderWordList();
      this.showToast('🗑️ 单词已删除');
    }
  }

  /* ------------------------------------------------------------------------
     Rendering List View
     ------------------------------------------------------------------------ */
  renderWordList() {
    const listContainer = document.getElementById('wordList');
    
    // Filter
    let filtered = this.words.filter(w => {
      if (this.currentFilter === 'learning' && w.mastered) return false;
      if (this.currentFilter === 'mastered' && !w.mastered) return false;

      if (this.searchQuery) {
        const q = this.searchQuery;
        const matchWord = w.word && w.word.toLowerCase().includes(q);
        const matchReading = w.reading && w.reading.toLowerCase().includes(q);
        const matchMeaning = w.meaning && w.meaning.toLowerCase().includes(q);
        return matchWord || matchReading || matchMeaning;
      }
      return true;
    });

    if (filtered.length === 0) {
      listContainer.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">📝</div>
          <h3>暂无对应的单词</h3>
          <p>点击下方“新增单词”或者右上角“➕”添加属于你自己的单词吧！</p>
        </div>
      `;
      return;
    }

    listContainer.innerHTML = filtered.map(w => `
      <div class="word-card" data-id="${w.id}">
        <div class="word-header">
          <div class="word-title-group">
            <span class="word-text">${this.escapeHtml(w.word)}</span>
            ${w.reading ? `<span class="word-reading">${this.escapeHtml(w.reading)}</span>` : ''}
          </div>
          ${w.mastered ? `<span class="mastered-badge">已掌握</span>` : ''}
        </div>

        <div class="word-meaning">${this.escapeHtml(w.meaning)}</div>

        ${w.example ? `
          <div class="word-example-box">
            <div class="word-example">${this.escapeHtml(w.example)}</div>
            ${w.exampleTrans ? `<div class="word-example-trans">${this.escapeHtml(w.exampleTrans)}</div>` : ''}
          </div>
        ` : ''}

        <div class="word-footer">
          <div class="word-tags">
            ${(w.tags || []).map(t => `<span class="tag-badge">#${this.escapeHtml(t)}</span>`).join('')}
          </div>
          <div class="card-actions">
            <button class="action-btn speak-btn" onclick="app.speakWord('${this.escapeHtml(w.word)}')" title="发音">🔊</button>
            <button class="action-btn" onclick="app.toggleMastered('${w.id}')" title="掌握状态">${w.mastered ? '🔄 设为学习中' : '✅ 标记掌握'}</button>
            <button class="action-btn" onclick="app.editWord('${w.id}')" title="编辑">✏️</button>
            <button class="action-btn" onclick="app.deleteWord('${w.id}')" title="删除">🗑️</button>
          </div>
        </div>
      </div>
    `).join('');
  }

  editWord(id) {
    const word = this.words.find(w => w.id === id);
    if (word) this.openWordModal(word);
  }

  updateStats() {
    const all = this.words.length;
    const mastered = this.words.filter(w => w.mastered).length;
    const learning = all - mastered;

    document.getElementById('count-all').textContent = all;
    document.getElementById('count-learning').textContent = learning;
    document.getElementById('count-mastered').textContent = mastered;
  }

  /* ------------------------------------------------------------------------
     Flashcard Review Engine
     ------------------------------------------------------------------------ */
  startReviewSession() {
    // Priority: unmastered words, shuffled
    this.reviewList = this.words.filter(w => !w.mastered);
    if (this.reviewList.length === 0) {
      // If all mastered, review all
      this.reviewList = [...this.words];
    }

    // Shuffle cards
    this.reviewList.sort(() => Math.random() - 0.5);
    this.currentReviewIndex = 0;
    this.renderCurrentCard();
  }

  renderCurrentCard() {
    const flashcard = document.getElementById('flashcard');
    flashcard.classList.remove('is-flipped');

    if (this.reviewList.length === 0) {
      document.getElementById('cardFrontWord').textContent = '🎉 词库为空';
      document.getElementById('cardFrontReading').textContent = '点击新增单词开始学习吧';
      document.getElementById('reviewStatusText').textContent = '进度：0 / 0';
      document.getElementById('reviewProgressFill').style.width = '0%';
      return;
    }

    const word = this.reviewList[this.currentReviewIndex];
    if (!word) {
      // Completed all cards
      document.getElementById('cardFrontWord').textContent = '✨ 本轮复习完成！';
      document.getElementById('cardFrontReading').textContent = '太棒了，你又巩固了一遍所学单词！';
      document.getElementById('cardBackMeaning').textContent = '所有卡片已复习完毕';
      document.getElementById('cardBackExampleBlock').style.display = 'none';
      document.getElementById('cardBackNotes').style.display = 'none';
      document.getElementById('reviewStatusText').textContent = `进度：${this.reviewList.length} / ${this.reviewList.length}`;
      document.getElementById('reviewProgressFill').style.width = '100%';
      return;
    }

    // Progress
    const total = this.reviewList.length;
    const currentNum = this.currentReviewIndex + 1;
    document.getElementById('reviewStatusText').textContent = `进度：${currentNum} / ${total}`;
    document.getElementById('reviewProgressFill').style.width = `${(currentNum / total) * 100}%`;

    // Front
    document.getElementById('cardFrontWord').textContent = word.word;
    document.getElementById('cardFrontReading').textContent = word.reading || '';

    // Back
    document.getElementById('cardBackMeaning').textContent = word.meaning;
    const exBlock = document.getElementById('cardBackExampleBlock');
    if (word.example) {
      exBlock.style.display = 'block';
      document.getElementById('cardBackExample').textContent = word.example;
      document.getElementById('cardBackExampleTrans').textContent = word.exampleTrans || '';
    } else {
      exBlock.style.display = 'none';
    }

    const notesBlock = document.getElementById('cardBackNotes');
    if (word.notes) {
      notesBlock.style.display = 'block';
      notesBlock.textContent = '💡 笔记：' + word.notes;
    } else {
      notesBlock.style.display = 'none';
    }
  }

  assessReview(type) {
    if (this.reviewList.length === 0 || this.currentReviewIndex >= this.reviewList.length) {
      this.startReviewSession();
      return;
    }

    const currentWord = this.reviewList[this.currentReviewIndex];

    if (type === 'remembered') {
      currentWord.reviewCount = (currentWord.reviewCount || 0) + 1;
      if (currentWord.reviewCount >= 2) {
        currentWord.mastered = true; // Mark as mastered if remembered repeatedly
      }
    } else if (type === 'forgot') {
      currentWord.mastered = false;
      currentWord.reviewCount = 0;
      // Push back to review list again in this session
      this.reviewList.push(currentWord);
    } else if (type === 'fuzzy') {
      currentWord.mastered = false;
    }

    this.saveData();
    this.currentReviewIndex++;

    // Flip back first then render next
    const flashcard = document.getElementById('flashcard');
    flashcard.classList.remove('is-flipped');
    setTimeout(() => {
      this.renderCurrentCard();
    }, 200);
  }

  /* ------------------------------------------------------------------------
     Speech Synthesis Engine (Web Speech API)
     ------------------------------------------------------------------------ */
  speakWord(text) {
    if (!('speechSynthesis' in window)) {
      this.showToast('当前浏览器不支持发音朗读');
      return;
    }

    window.speechSynthesis.cancel(); // Stop ongoing speech

    const utterance = new SpeechSynthesisUtterance(text);
    
    // Detect Language Automatically
    if (/[\uac00-\ud7a3]/.test(text)) {
      utterance.lang = 'ko-KR'; // Korean
    } else if (/[\u3040-\u30ff\u31f0-\u31ff]/.test(text)) {
      utterance.lang = 'ja-JP'; // Japanese
    } else if (/[a-zA-Z]/.test(text)) {
      utterance.lang = 'en-US'; // English
    } else {
      utterance.lang = 'zh-CN'; // Chinese
    }

    utterance.rate = 0.9; // Slightly slower for clear pronunciation
    window.speechSynthesis.speak(utterance);
  }

  /* ------------------------------------------------------------------------
     Data Backup & Restore & Samples
     ------------------------------------------------------------------------ */
  exportJSON() {
    if (this.words.length === 0) {
      this.showToast('词库为空，无需导出');
      return;
    }

    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(this.words, null, 2));
    const downloadAnchor = document.createElement('a');
    const dateStr = new Date().toISOString().slice(0, 10);
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `Vocab_Backup_${dateStr}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();

    this.showToast('📦 导出 JSON 备份文件成功！');
  }

  importJSON(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const imported = JSON.parse(e.target.result);
        if (Array.isArray(imported)) {
          // Merge imported items avoiding duplicate ids
          let count = 0;
          imported.forEach(item => {
            if (item.word && item.meaning) {
              if (!this.words.some(w => w.id === item.id || (w.word === item.word && w.meaning === item.meaning))) {
                this.words.unshift({
                  ...item,
                  id: item.id || ('word_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4))
                });
                count++;
              }
            }
          });
          this.saveData();
          this.renderWordList();
          this.showToast(`✅ 成功导入 ${count} 个单词！`);
        } else {
          this.showToast('⚠️ JSON 格式不正确');
        }
      } catch (err) {
        this.showToast('⚠️ 读取文件失败');
      }
    };
    reader.readAsText(file);
    event.target.value = ''; // Reset input
  }

  loadSampleData(lang, showNotification = true) {
    const samples = {
      korean: [
        {
          id: 'kr_1',
          word: '행복하다',
          reading: '[haeng-bok-ha-da]',
          meaning: 'adj. 幸福的，快乐的',
          example: '오늘 친구들과 만나서 정말 행복했어요.',
          exampleTrans: '今天和朋友们见面真的很幸福。',
          tags: ['韩语', '高频'],
          notes: '名词 행복 (幸福) + 하다 (做/处于...状态)',
          mastered: false,
          createdAt: Date.now()
        },
        {
          id: 'kr_2',
          word: '설레다',
          reading: '[seol-re-da]',
          meaning: 'v. 心动，激动，激动不安',
          example: '여행을 떠나기 전날 밤이라 가슴이 설렌다.',
          exampleTrans: '因为是出发旅行的前一天晚上，心情很激动。',
          tags: ['韩语', '情感'],
          notes: '常用来形容恋爱或期待旅行的心情',
          mastered: false,
          createdAt: Date.now()
        },
        {
          id: 'kr_3',
          word: '응원하다',
          reading: '[eung-won-ha-da]',
          meaning: 'v. 加油，支持，应援',
          example: '당신의 꿈을 항상 응원할게요!',
          exampleTrans: '我会一直为你加油支持你的梦想！',
          tags: ['韩语', '日常'],
          notes: '응원 (应援)',
          mastered: true,
          createdAt: Date.now()
        }
      ],
      japanese: [
        {
          id: 'jp_1',
          word: '木漏れ日',
          reading: 'こもれび [Komorebi]',
          meaning: 'n. 树叶缝隙中透过的阳光',
          example: '森の中を歩くと、木漏れ日がとても綺麗です。',
          exampleTrans: '在森林里散步，透过树叶缝隙的阳光非常美丽。',
          tags: ['日语', '意境'],
          notes: '形容唯美自然光影的日语独特词汇',
          mastered: false,
          createdAt: Date.now()
        },
        {
          id: 'jp_2',
          word: '一生懸命',
          reading: 'いっしょうけんめい',
          meaning: 'adj./adv. 拼命地，努力地',
          example: '夢に向かって一生懸命頑張っています。',
          exampleTrans: '为了梦想正在拼命努力。',
          tags: ['日语', '高频'],
          notes: '近义词：懸命 (けんめい)',
          mastered: false,
          createdAt: Date.now()
        }
      ],
      english: [
        {
          id: 'en_1',
          word: 'Serendipity',
          reading: '[ˌserənˈdɪpəti]',
          meaning: 'n. 意外发现美好事物的运气，机缘巧合',
          example: 'Finding this cozy cafe was pure serendipity.',
          exampleTrans: '发现这家舒适的咖啡馆纯属意外的惊喜。',
          tags: ['英语', '优雅词汇'],
          notes: '被评为英语中最美丽的单词之一',
          mastered: false,
          createdAt: Date.now()
        },
        {
          id: 'en_2',
          word: 'Resilience',
          reading: '[rɪˈzɪliəns]',
          meaning: 'n. 恢复力，韧性，适应力',
          example: 'She showed great resilience in overcoming obstacles.',
          exampleTrans: '她在克服困难中展现了强大的韧性。',
          tags: ['英语', '高频'],
          notes: '形容人面对逆风时的弹性和韧劲',
          mastered: false,
          createdAt: Date.now()
        }
      ]
    };

    const targetList = samples[lang] || [];
    let count = 0;
    targetList.forEach(item => {
      if (!this.words.some(w => w.word === item.word)) {
        this.words.push(item);
        count++;
      }
    });

    this.saveData();
    this.renderWordList();
    if (showNotification) {
      this.showToast(`🎉 成功载入示例词库！`);
    }
  }

  clearAllData() {
    if (confirm('确定要清空手机本地保存的所有单词吗？此操作不可撤销！建议先导出备份。')) {
      this.words = [];
      this.saveData();
      this.renderWordList();
      this.showToast('🗑️ 本地数据已全部清空');
    }
  }

  /* ------------------------------------------------------------------------
     UI Helper Utilities
     ------------------------------------------------------------------------ */
  showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => {
      toast.classList.remove('show');
    }, 2500);
  }

  escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
}

// Global App Instance
let app;
document.addEventListener('DOMContentLoaded', () => {
  app = new VocabApp();
});
