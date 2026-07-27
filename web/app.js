/**
 * Hinata Hyuga Web Application & Deep Search Engine
 */

document.addEventListener('DOMContentLoaded', () => {
  // Toast Notification System
  function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast-item ${type}`;

    let icon = 'ℹ️';
    if (type === 'success') icon = '✨';
    if (type === 'error') icon = '⚠️';

    toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('toast-fade-out');
      toast.addEventListener('animationend', () => toast.remove());
    }, duration);
  }

  // Profile Identity & Custom Avatar Management
  const defaultProfile = {
    companionName: 'Hinata Hyuga',
    userName: 'Saif',
    tagline: 'Sweet & Caring AI Girl Companion • Auto-trained on user data',
    avatarData: '',
    avatarEmoji: '🌸'
  };

  let profile = loadProfile();

  function loadProfile() {
    try {
      const saved = localStorage.getItem('hinata_profile_data');
      return saved ? { ...defaultProfile, ...JSON.parse(saved) } : { ...defaultProfile };
    } catch (e) {
      return { ...defaultProfile };
    }
  }

  function saveProfile(newProf) {
    profile = { ...profile, ...newProf };
    try {
      localStorage.setItem('hinata_profile_data', JSON.stringify(profile));
    } catch (e) {
      console.error('Failed to save profile to localStorage', e);
    }
    applyProfile(profile);
  }

  function applyProfile(prof) {
    // Header & Info
    const elCompName = document.getElementById('companionNameText');
    const elTagline = document.getElementById('companionTaglineText');
    if (elCompName) elCompName.textContent = prof.companionName || 'Hinata Hyuga';
    if (elTagline) elTagline.textContent = prof.tagline || 'Sweet & Caring AI Girl Companion';

    // Avatar Image Elements
    const avatarImgHeader = document.getElementById('companionAvatarImg');
    const avatarEmojiHeader = document.getElementById('companionAvatarEmoji');

    const miniImg = document.getElementById('settingsAvatarMiniImg');
    const miniEmoji = document.getElementById('settingsAvatarMiniEmoji');

    const modalImg = document.getElementById('modalAvatarImg');
    const modalEmoji = document.getElementById('modalAvatarEmoji');

    if (prof.avatarData) {
      if (avatarImgHeader) {
        avatarImgHeader.src = prof.avatarData;
        avatarImgHeader.style.display = 'block';
      }
      if (avatarEmojiHeader) avatarEmojiHeader.style.display = 'none';

      if (miniImg) {
        miniImg.src = prof.avatarData;
        miniImg.style.display = 'block';
      }
      if (miniEmoji) miniEmoji.style.display = 'none';

      if (modalImg) {
        modalImg.src = prof.avatarData;
        modalImg.style.display = 'block';
      }
      if (modalEmoji) modalEmoji.style.display = 'none';
    } else {
      if (avatarImgHeader) avatarImgHeader.style.display = 'none';
      if (avatarEmojiHeader) {
        avatarEmojiHeader.style.display = 'block';
        avatarEmojiHeader.textContent = prof.avatarEmoji || '🌸';
      }

      if (miniImg) miniImg.style.display = 'none';
      if (miniEmoji) {
        miniEmoji.style.display = 'block';
        miniEmoji.textContent = prof.avatarEmoji || '🌸';
      }

      if (modalImg) modalImg.style.display = 'none';
      if (modalEmoji) {
        modalEmoji.style.display = 'block';
        modalEmoji.textContent = prof.avatarEmoji || '🌸';
      }
    }

    // Update Settings Inputs
    const elSettingCompName = document.getElementById('settingCompanionName');
    const elSettingUserName = document.getElementById('settingUserName');
    const elSettingTagline = document.getElementById('settingCompanionTagline');
    const elSettingUrl = document.getElementById('settingAvatarUrlInput');

    if (elSettingCompName) elSettingCompName.value = prof.companionName || 'Hinata Hyuga';
    if (elSettingUserName) elSettingUserName.value = prof.userName || 'User';
    if (elSettingTagline) elSettingTagline.value = prof.tagline || '';
    if (elSettingUrl) elSettingUrl.value = (prof.avatarData && prof.avatarData.startsWith('http')) ? prof.avatarData : '';

    // Update Modal Inputs
    const elModalCompName = document.getElementById('editModalCompanionName');
    const elModalUserName = document.getElementById('editModalUserName');
    const elModalTagline = document.getElementById('editModalTagline');
    const elModalUrl = document.getElementById('modalAvatarUrlInput');

    if (elModalCompName) elModalCompName.value = prof.companionName || 'Hinata Hyuga';
    if (elModalUserName) elModalUserName.value = prof.userName || 'User';
    if (elModalTagline) elModalTagline.value = prof.tagline || '';
    if (elModalUrl) elModalUrl.value = (prof.avatarData && prof.avatarData.startsWith('http')) ? prof.avatarData : '';
  }

  applyProfile(profile);

  // File Upload Helper
  function handleAvatarFile(fileInput) {
    if (!fileInput || !fileInput.files || !fileInput.files[0]) return;
    const file = fileInput.files[0];
    if (file.size > 5 * 1024 * 1024) {
      showToast('Image size must be less than 5MB', 'error');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const base64Url = e.target.result;
      saveProfile({ avatarData: base64Url });
      showToast('Custom Avatar updated successfully! 📸', 'success');
    };
    reader.readAsDataURL(file);
  }

  const settingAvatarFileInput = document.getElementById('settingAvatarFileInput');
  if (settingAvatarFileInput) {
    settingAvatarFileInput.addEventListener('change', () => handleAvatarFile(settingAvatarFileInput));
  }

  const modalAvatarFileInput = document.getElementById('modalAvatarFileInput');
  if (modalAvatarFileInput) {
    modalAvatarFileInput.addEventListener('change', () => handleAvatarFile(modalAvatarFileInput));
  }

  const btnResetAvatarImage = document.getElementById('btnResetAvatarImage');
  if (btnResetAvatarImage) {
    btnResetAvatarImage.addEventListener('click', () => {
      saveProfile({ avatarData: '' });
      showToast('Removed custom avatar photo', 'info');
    });
  }

  const btnModalRemovePhoto = document.getElementById('btnModalRemovePhoto');
  if (btnModalRemovePhoto) {
    btnModalRemovePhoto.addEventListener('click', () => {
      saveProfile({ avatarData: '' });
      showToast('Removed custom avatar photo', 'info');
    });
  }

  // Profile Edit Modal Controllers
  const profileEditModal = document.getElementById('profileEditModal');
  const companionAvatarBtn = document.getElementById('companionAvatarBtn');
  const btnEditProfile = document.getElementById('btnEditProfile');
  const btnCloseProfileModal = document.getElementById('btnCloseProfileModal');
  const btnCancelEditProfile = document.getElementById('btnCancelEditProfile');
  const btnSaveProfileModal = document.getElementById('btnSaveProfileModal');

  function openProfileModal() {
    if (profileEditModal) profileEditModal.classList.add('active');
    applyProfile(profile);
  }

  function closeProfileModal() {
    if (profileEditModal) profileEditModal.classList.remove('active');
  }

  if (companionAvatarBtn) companionAvatarBtn.addEventListener('click', openProfileModal);
  if (btnEditProfile) btnEditProfile.addEventListener('click', openProfileModal);
  if (btnCloseProfileModal) btnCloseProfileModal.addEventListener('click', closeProfileModal);
  if (btnCancelEditProfile) btnCancelEditProfile.addEventListener('click', closeProfileModal);

  if (profileEditModal) {
    profileEditModal.addEventListener('click', (e) => {
      if (e.target === profileEditModal) closeProfileModal();
    });
  }

  if (btnSaveProfileModal) {
    btnSaveProfileModal.addEventListener('click', () => {
      const elModalCompName = document.getElementById('editModalCompanionName');
      const elModalUserName = document.getElementById('editModalUserName');
      const elModalTagline = document.getElementById('editModalTagline');
      const elModalUrl = document.getElementById('modalAvatarUrlInput');

      const updated = {
        companionName: elModalCompName ? elModalCompName.value.trim() : profile.companionName,
        userName: elModalUserName ? elModalUserName.value.trim() : profile.userName,
        tagline: elModalTagline ? elModalTagline.value.trim() : profile.tagline
      };

      if (elModalUrl && elModalUrl.value.trim()) {
        updated.avatarData = elModalUrl.value.trim();
      }

      saveProfile(updated);
      closeProfileModal();
      showToast('Profile and avatar updated! ✨', 'success');
    });
  }

  // App Settings Management & Persistence
  const defaultSettings = {
    theme: 'sakura',
    petals: true,
    blur: true,
    language: 'en',
    emoji: 'normal',
    creativity: 0.7,
    sound: true,
    provider: 'opencode_zen',
    groqKey: '',
    memory: true
  };

  let settings = loadSettings();

  function loadSettings() {
    try {
      const saved = localStorage.getItem('hinata_settings');
      return saved ? { ...defaultSettings, ...JSON.parse(saved) } : { ...defaultSettings };
    } catch (e) {
      return { ...defaultSettings };
    }
  }

  function saveSettings(newSettings) {
    settings = { ...settings, ...newSettings };
    try {
      localStorage.setItem('hinata_settings', JSON.stringify(settings));
    } catch (e) {
      console.error('Failed to save settings to localStorage', e);
    }
    applySettings(settings);
  }

  function applySettings(cfg) {
    // Apply Theme
    document.body.setAttribute('data-theme', cfg.theme || 'sakura');
    document.querySelectorAll('.theme-pill').forEach(btn => {
      const isCur = btn.getAttribute('data-theme') === cfg.theme;
      btn.classList.toggle('active', isCur);
      const rawText = btn.getAttribute('data-name') || btn.textContent.replace(/^✓\s*/, '');
      btn.setAttribute('data-name', rawText);
      btn.textContent = isCur ? `✓ ${rawText}` : rawText;
    });

    // Apply Petals
    document.body.classList.toggle('no-petals', !cfg.petals);

    // Apply Blur
    document.body.classList.toggle('no-blur', !cfg.blur);

    // Update Form Controls
    const elLang = document.getElementById('settingLanguage');
    const elEmoji = document.getElementById('settingEmoji');
    const elCreativity = document.getElementById('settingCreativity');
    const elCreativityBadge = document.getElementById('creativityValueBadge');
    const elSound = document.getElementById('settingSound');
    const elProvider = document.getElementById('settingProvider');
    const elGroqKey = document.getElementById('settingGroqKey');
    const elMemory = document.getElementById('settingMemory');
    const elPetals = document.getElementById('settingPetals');
    const elBlur = document.getElementById('settingBlur');

    if (elLang) elLang.value = cfg.language;
    if (elEmoji) elEmoji.value = cfg.emoji;
    if (elCreativity) {
      elCreativity.value = cfg.creativity;
      if (elCreativityBadge) elCreativityBadge.textContent = parseFloat(cfg.creativity).toFixed(1);
    }
    if (elSound) elSound.checked = cfg.sound;
    if (elProvider) elProvider.value = cfg.provider;
    if (elGroqKey) elGroqKey.value = cfg.groqKey || '';
    if (elMemory) elMemory.checked = cfg.memory;
    if (elPetals) elPetals.checked = cfg.petals;
    if (elBlur) elBlur.checked = cfg.blur;
  }

  applySettings(settings);

  // App State
  const state = {
    activeView: 'view-chat',
    activeProvider: settings.provider || 'opencode_zen',
    activeModel: 'opencode/big-pickle',
    activePersonality: 'sweet',
    currentMood: 'Happy & Warm',
    relationshipScore: 180,
    memories: loadMemories(),
    personalities: [
      { id: 'sweet', name: 'Sweet 🌸', desc: 'Warm, caring, and gentle. Talks like a sweet girl.' },
      { id: 'gamer', name: 'Gamer 🎮', desc: 'Energetic, competitive, and loves gaming quests.' },
      { id: 'playful', name: 'Playful ✨', desc: 'Fun, teasing, mischievous, and loves jokes.' },
      { id: 'calm', name: 'Calm 🌿', desc: 'Peaceful, serene, patient, and serene.' },
      { id: 'smart', name: 'Smart 💡', desc: 'Logical, precise, knowledgeable, and analytical.' },
      { id: 'curious', name: 'Curious 🔍', desc: 'Inquisitive and eager to explore deep topics.' },
      { id: 'boss', name: 'Boss 💼', desc: 'Direct, efficient, productive, and focused.' },
      { id: 'supportive', name: 'Supportive 💖', desc: 'Encouraging, empathetic, and motivating.' }
    ],
    opencodeModels: [
      'opencode/big-pickle',
      'opencode/deepseek-v4-flash-free',
      'opencode/mimo-v2.5-free',
      'opencode/nemotron-3-ultra-free',
      'opencode/ing-3.0-flash-free',
      'opencode/laguna-s-2.1-free',
      'opencode-zen-free',
      'deepseek-r1',
      'qwen2.5-72b-instruct'
    ]
  };

  function loadMemories() {
    try {
      const saved = localStorage.getItem('hinata_memories');
      if (saved) return JSON.parse(saved);
    } catch (e) {}
    return [
      { id: 1, type: 'fact', content: 'User prefers quiet evening chats and tea.', importance: 5 },
      { id: 2, type: 'preference', content: 'Loves OpenCode Zen thinking models.', importance: 4 },
      { id: 3, type: 'goal', content: 'Building Hinata Hyuga AI Companion Web App.', importance: 5 },
      { id: 4, type: 'nickname', content: 'Prefers being called Saif.', importance: 3 }
    ];
  }

  function saveMemoriesToStorage() {
    try {
      localStorage.setItem('hinata_memories', JSON.stringify(state.memories));
    } catch (e) {}
  }

  // 1. Navigation Controller (Desktop & Mobile)
  const navItems = document.querySelectorAll('.nav-item');
  const mobileNavItems = document.querySelectorAll('.mobile-nav-item');
  const viewPanels = document.querySelectorAll('.view-panel');
  const appSidebar = document.getElementById('appSidebar');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');
  const btnMobileMenu = document.getElementById('btnMobileMenu');
  const btnMobileMore = document.getElementById('btnMobileMore');
  const btnCloseMobileSidebar = document.getElementById('btnCloseMobileSidebar');

  function switchView(targetView) {
    navItems.forEach(n => n.classList.remove('active'));
    mobileNavItems.forEach(n => n.classList.remove('active'));
    viewPanels.forEach(p => p.classList.remove('active'));

    const activeSidebarBtn = document.querySelector(`.nav-item[data-target="${targetView}"]`);
    const activeMobileBtn = document.querySelector(`.mobile-nav-item[data-target="${targetView}"]`);
    const targetPanel = document.getElementById(targetView);

    if (activeSidebarBtn) activeSidebarBtn.classList.add('active');
    if (activeMobileBtn) activeMobileBtn.classList.add('active');
    if (targetPanel) targetPanel.classList.add('active');

    state.activeView = targetView;
    closeMobileDrawer();
  }

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const targetView = item.getAttribute('data-target');
      if (targetView) switchView(targetView);
    });
  });

  mobileNavItems.forEach(item => {
    item.addEventListener('click', () => {
      const targetView = item.getAttribute('data-target');
      if (targetView) switchView(targetView);
    });
  });

  function toggleMobileDrawer() {
    if (appSidebar) appSidebar.classList.toggle('mobile-open');
    if (sidebarBackdrop) sidebarBackdrop.classList.toggle('active');
  }

  function closeMobileDrawer() {
    if (appSidebar) appSidebar.classList.remove('mobile-open');
    if (sidebarBackdrop) sidebarBackdrop.classList.remove('active');
  }

  if (btnMobileMenu) btnMobileMenu.addEventListener('click', toggleMobileDrawer);
  if (btnMobileMore) btnMobileMore.addEventListener('click', toggleMobileDrawer);
  if (btnCloseMobileSidebar) btnCloseMobileSidebar.addEventListener('click', closeMobileDrawer);
  if (sidebarBackdrop) sidebarBackdrop.addEventListener('click', closeMobileDrawer);

  const btnToggleWidgets = document.getElementById('btnToggleWidgets');
  const headerWidgets = document.getElementById('headerWidgets');
  if (btnToggleWidgets && headerWidgets) {
    btnToggleWidgets.addEventListener('click', () => {
      headerWidgets.classList.toggle('expanded');
    });
  }

  let touchStartX = 0;
  if (appSidebar) {
    appSidebar.addEventListener('touchstart', (e) => {
      touchStartX = e.touches[0].clientX;
    }, { passive: true });

    appSidebar.addEventListener('touchend', (e) => {
      const touchEndX = e.changedTouches[0].clientX;
      if (touchStartX - touchEndX > 50) {
        closeMobileDrawer();
      }
    }, { passive: true });
  }

  // 2. Chat Controller
  const chatMessages = document.getElementById('chatMessages');
  const messageInput = document.getElementById('messageInput');
  const btnSendMessage = document.getElementById('btnSendMessage');
  const quickPrompts = document.querySelectorAll('.quick-prompts .chip');

  async function sendMessage(text) {
    if (!text.trim()) return;

    const uName = profile.userName || 'User';
    appendMessage('user', uName, text);
    messageInput.value = '';

    const cName = profile.companionName || 'Hinata Hyuga';

    const typingElem = document.createElement('div');
    typingElem.className = 'message assistant-message typing-msg';

    let avatarHtml = `<div class="message-avatar">${profile.avatarEmoji || '🌸'}</div>`;
    if (profile.avatarData) {
      avatarHtml = `<div class="message-avatar"><img src="${escapeHtml(profile.avatarData)}" class="message-avatar-img" alt="Avatar" /></div>`;
    }

    typingElem.innerHTML = `
      ${avatarHtml}
      <div class="message-content"><div class="message-sender">${escapeHtml(cName)}</div><div>Thinking...</div></div>
    `;
    chatMessages.appendChild(typingElem);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, provider: state.activeProvider, model: state.activeModel })
      });
      const data = await res.json();
      chatMessages.removeChild(typingElem);
      appendMessage('assistant', cName, data.reply || 'I am always here for you! 💖');
    } catch (err) {
      chatMessages.removeChild(typingElem);
      appendMessage('assistant', cName, `I'm happy to chat with you! (Provider: ${state.activeProvider}, Model: ${state.activeModel}) 🌸`);
    }
  }

  function appendMessage(role, sender, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}-message`;

    let actionsHtml = '';
    if (role === 'assistant') {
      actionsHtml = `
        <div class="message-actions">
          <button class="btn-copy-msg" title="Copy message">📋 Copy</button>
        </div>
      `;
    }

    let avatarHtml = `<div class="message-avatar">${role === 'user' ? '👤' : (profile.avatarEmoji || '🌸')}</div>`;
    if (role === 'assistant' && profile.avatarData) {
      avatarHtml = `<div class="message-avatar"><img src="${escapeHtml(profile.avatarData)}" class="message-avatar-img" alt="Avatar" /></div>`;
    }

    msgDiv.innerHTML = `
      ${avatarHtml}
      <div class="message-content">
        <div class="message-sender">${escapeHtml(sender)}</div>
        <div class="message-text">${escapeHtml(text)}</div>
        ${actionsHtml}
        <div class="message-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
      </div>
    `;

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    if (role === 'assistant') {
      const copyBtn = msgDiv.querySelector('.btn-copy-msg');
      if (copyBtn) {
        copyBtn.addEventListener('click', () => {
          navigator.clipboard.writeText(text).then(() => {
            showToast('Copied to clipboard! 📋', 'success');
          }).catch(() => {
            showToast('Failed to copy message', 'error');
          });
        });
      }
    }
  }

  if (btnSendMessage) btnSendMessage.addEventListener('click', () => sendMessage(messageInput.value));
  if (messageInput) {
    messageInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage(messageInput.value);
      }
    });
  }

  quickPrompts.forEach(chip => {
    chip.addEventListener('click', () => {
      const prompt = chip.getAttribute('data-prompt');
      if (prompt) sendMessage(prompt);
    });
  });

  // 3. DEEP SEARCH ENGINE
  const deepSearchInput = document.getElementById('deepSearchInput');
  const btnExecuteSearch = document.getElementById('btnExecuteSearch');
  const searchResultsGrid = document.getElementById('searchResultsGrid');
  const filterChips = document.querySelectorAll('.filter-chip');

  let currentSearchFilter = 'all';

  function executeDeepSearch(query) {
    if (!query) {
      renderSearchResults(getAllSearchableItems());
      return;
    }
    const cleanQuery = query.toLowerCase();
    const items = getAllSearchableItems();
    const filtered = items.filter(item => {
      const matchesCategory = currentSearchFilter === 'all' || item.category === currentSearchFilter;
      const matchesQuery = item.title.toLowerCase().includes(cleanQuery) || item.snippet.toLowerCase().includes(cleanQuery);
      return matchesCategory && matchesQuery;
    });
    renderSearchResults(filtered, cleanQuery);
  }

  function getAllSearchableItems() {
    const items = [];
    state.memories.forEach(m => {
      items.push({ category: 'memory', type: `Memory (${m.type})`, title: m.content, snippet: `Importance: ${'⭐'.repeat(m.importance)}` });
    });
    state.personalities.forEach(p => {
      items.push({ category: 'personality', type: 'Personality Persona', title: p.name, snippet: p.desc });
    });
    state.opencodeModels.forEach(m => {
      items.push({ category: 'models', type: 'OpenCode Zen Free Model', title: m, snippet: 'Endpoint: https://opencode.ai/zen/v1/chat/completions' });
    });
    items.push(
      { category: 'chat', type: 'Chat History', title: `${profile.companionName || 'Hinata Hyuga'} Persona`, snippet: 'Talks like a sweet, gentle, caring girl.' },
      { category: 'chat', type: 'Chat History', title: 'OpenCode Zen Integration', snippet: 'Configured opencode/big-pickle as default free thinking model.' },
      { category: 'chat', type: 'Chat History', title: 'Minaty001 GitHub', snippet: 'Created by Minaty001 on GitHub (github.com/Minaty001/hinata).' }
    );
    return items;
  }

  function renderSearchResults(items, highlightQuery = '') {
    if (!searchResultsGrid) return;
    searchResultsGrid.innerHTML = '';
    if (items.length === 0) {
      searchResultsGrid.innerHTML = `<div class="no-results">No matching results found for "${escapeHtml(highlightQuery)}".</div>`;
      return;
    }
    items.forEach(item => {
      const card = document.createElement('div');
      card.className = 'search-result-card';
      card.innerHTML = `
        <span class="result-type">${item.type}</span>
        <div class="result-title">${escapeHtml(item.title)}</div>
        <div class="result-snippet">${escapeHtml(item.snippet)}</div>
      `;
      searchResultsGrid.appendChild(card);
    });
  }

  if (deepSearchInput) {
    deepSearchInput.addEventListener('input', (e) => executeDeepSearch(e.target.value));
  }

  if (btnExecuteSearch) {
    btnExecuteSearch.addEventListener('click', () => {
      if (deepSearchInput) executeDeepSearch(deepSearchInput.value);
    });
  }

  filterChips.forEach(chip => {
    chip.addEventListener('click', () => {
      filterChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      currentSearchFilter = chip.getAttribute('data-filter');
      if (deepSearchInput) executeDeepSearch(deepSearchInput.value);
    });
  });

  renderSearchResults(getAllSearchableItems());

  // 4. Memory Manager Render & Modal Handler
  function renderMemories() {
    const grid = document.getElementById('memoriesGrid');
    if (!grid) return;
    grid.innerHTML = '';
    state.memories.forEach(m => {
      const card = document.createElement('div');
      card.className = 'memory-card';
      card.innerHTML = `
        <span class="result-type">📌 [${m.type.toUpperCase()}]</span>
        <div class="result-title">${escapeHtml(m.content)}</div>
        <div class="result-snippet">Importance: ${'⭐'.repeat(m.importance)}</div>
      `;
      grid.appendChild(card);
    });
  }
  renderMemories();

  const btnAddMemoryModal = document.getElementById('btnAddMemoryModal');
  const memoryModal = document.getElementById('memoryModal');
  const btnCloseMemoryModal = document.getElementById('btnCloseMemoryModal');
  const btnCancelAddMemory = document.getElementById('btnCancelAddMemory');
  const btnSaveNewMemory = document.getElementById('btnSaveNewMemory');
  const memoryContentInput = document.getElementById('memoryContentInput');
  const memoryTypeSelect = document.getElementById('memoryTypeSelect');
  const memoryImportanceSelect = document.getElementById('memoryImportanceSelect');

  function openMemoryModal() {
    if (memoryModal) memoryModal.classList.add('active');
    if (memoryContentInput) {
      memoryContentInput.value = '';
      memoryContentInput.focus();
    }
  }

  function closeMemoryModal() {
    if (memoryModal) memoryModal.classList.remove('active');
  }

  if (btnAddMemoryModal) btnAddMemoryModal.addEventListener('click', openMemoryModal);
  if (btnCloseMemoryModal) btnCloseMemoryModal.addEventListener('click', closeMemoryModal);
  if (btnCancelAddMemory) btnCancelAddMemory.addEventListener('click', closeMemoryModal);

  if (memoryModal) {
    memoryModal.addEventListener('click', (e) => {
      if (e.target === memoryModal) closeMemoryModal();
    });
  }

  if (btnSaveNewMemory) {
    btnSaveNewMemory.addEventListener('click', () => {
      const content = memoryContentInput ? memoryContentInput.value.trim() : '';
      if (!content) {
        showToast('Please enter memory content', 'error');
        return;
      }
      const type = memoryTypeSelect ? memoryTypeSelect.value : 'fact';
      const importance = memoryImportanceSelect ? parseInt(memoryImportanceSelect.value, 10) : 3;

      const newMem = { id: Date.now(), type, content, importance };
      state.memories.unshift(newMem);
      saveMemoriesToStorage();
      renderMemories();
      closeMemoryModal();
      showToast('New memory saved successfully! 🧠', 'success');
    });
  }

  // 5. Personality Controller
  function renderPersonalities() {
    const grid = document.getElementById('personalitiesGrid');
    if (!grid) return;
    grid.innerHTML = '';
    state.personalities.forEach(p => {
      const isActive = state.activePersonality === p.id;
      const card = document.createElement('div');
      card.className = `personality-card ${isActive ? 'active' : ''}`;
      card.innerHTML = `
        <h3>${p.name}</h3>
        <p class="result-snippet">${p.desc}</p>
        <button class="btn btn-sm ${isActive ? 'btn-primary' : 'btn-outline'} btn-select-p" data-id="${p.id}">
          ${isActive ? 'Active Persona ✓' : 'Select Persona'}
        </button>
      `;
      grid.appendChild(card);
    });

    document.querySelectorAll('.btn-select-p').forEach(btn => {
      btn.addEventListener('click', () => {
        state.activePersonality = btn.getAttribute('data-id');
        renderPersonalities();
        const pObj = state.personalities.find(p => p.id === state.activePersonality);
        showToast(`Switched persona to ${pObj ? pObj.name : state.activePersonality}! 🎭`, 'info');
      });
    });
  }
  renderPersonalities();

  // 6. Provider Controller
  const btnSelectGroq = document.getElementById('btnSelectGroq');
  const btnSelectZen = document.getElementById('btnSelectZen');
  const cardProviderGroq = document.getElementById('cardProviderGroq');
  const cardProviderZen = document.getElementById('cardProviderZen');
  const activeProviderPill = document.getElementById('activeProviderPill');
  const activeModelText = document.getElementById('activeModelText');

  function updateProviderUI(provider, model) {
    state.activeProvider = provider;
    if (model) state.activeModel = model;

    if (provider === 'opencode_zen') {
      if (cardProviderZen) cardProviderZen.classList.add('active');
      if (cardProviderGroq) cardProviderGroq.classList.remove('active');

      if (btnSelectZen) {
        btnSelectZen.textContent = 'Active Engine ✓';
        btnSelectZen.className = 'btn btn-primary';
      }
      if (btnSelectGroq) {
        btnSelectGroq.textContent = 'Select Groq API';
        btnSelectGroq.className = 'btn btn-outline';
      }

      if (activeProviderPill) activeProviderPill.textContent = 'OpenCode Zen';
      if (activeModelText) activeModelText.textContent = state.activeModel;
    } else {
      if (cardProviderGroq) cardProviderGroq.classList.add('active');
      if (cardProviderZen) cardProviderZen.classList.remove('active');

      if (btnSelectGroq) {
        btnSelectGroq.textContent = 'Active Engine ✓';
        btnSelectGroq.className = 'btn btn-primary';
      }
      if (btnSelectZen) {
        btnSelectZen.textContent = 'Select OpenCode Zen';
        btnSelectZen.className = 'btn btn-outline';
      }

      if (activeProviderPill) activeProviderPill.textContent = 'Groq API';
      if (activeModelText) activeModelText.textContent = 'llama-3.3-70b-versatile';
    }

    document.querySelectorAll('#opencodeModelsList .model-option').forEach(btn => {
      const mName = btn.getAttribute('data-model');
      const isSelected = (mName === state.activeModel) && (state.activeProvider === 'opencode_zen');
      btn.classList.toggle('active', isSelected);
      btn.textContent = isSelected ? `✓ ${mName}` : mName;
    });

    saveSettings({ provider: state.activeProvider });
  }

  if (btnSelectGroq) {
    btnSelectGroq.addEventListener('click', () => {
      updateProviderUI('groq', 'llama-3.3-70b-versatile');
      showToast('AI Provider set to Groq API 🚀', 'info');
    });
  }

  if (btnSelectZen) {
    btnSelectZen.addEventListener('click', () => {
      updateProviderUI('opencode_zen', state.activeModel);
      showToast('AI Provider set to OpenCode Zen ⚡', 'info');
    });
  }

  document.querySelectorAll('#opencodeModelsList .model-option').forEach(btn => {
    btn.addEventListener('click', () => {
      const selectedModel = btn.getAttribute('data-model');
      updateProviderUI('opencode_zen', selectedModel);
      showToast(`Model set to ${selectedModel} ⚡`, 'info');
    });
  });

  // 7. Settings Events Controller
  document.querySelectorAll('.theme-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      const theme = pill.getAttribute('data-theme');
      saveSettings({ theme });
      showToast(`Theme changed to ${pill.textContent}! 🎨`, 'info');
    });
  });

  const settingCreativity = document.getElementById('settingCreativity');
  const creativityValueBadge = document.getElementById('creativityValueBadge');
  if (settingCreativity && creativityValueBadge) {
    settingCreativity.addEventListener('input', (e) => {
      creativityValueBadge.textContent = parseFloat(e.target.value).toFixed(1);
    });
  }

  const btnToggleGroqKey = document.getElementById('btnToggleGroqKey');
  const settingGroqKey = document.getElementById('settingGroqKey');
  if (btnToggleGroqKey && settingGroqKey) {
    btnToggleGroqKey.addEventListener('click', () => {
      const currentType = settingGroqKey.getAttribute('type');
      settingGroqKey.setAttribute('type', currentType === 'password' ? 'text' : 'password');
    });
  }

  const btnSaveSettings = document.getElementById('btnSaveSettings');
  if (btnSaveSettings) {
    btnSaveSettings.addEventListener('click', () => {
      const elLang = document.getElementById('settingLanguage');
      const elEmoji = document.getElementById('settingEmoji');
      const elCreativity = document.getElementById('settingCreativity');
      const elSound = document.getElementById('settingSound');
      const elProvider = document.getElementById('settingProvider');
      const elGroqKey = document.getElementById('settingGroqKey');
      const elMemory = document.getElementById('settingMemory');
      const elPetals = document.getElementById('settingPetals');
      const elBlur = document.getElementById('settingBlur');

      const elSettingCompName = document.getElementById('settingCompanionName');
      const elSettingUserName = document.getElementById('settingUserName');
      const elSettingTagline = document.getElementById('settingCompanionTagline');
      const elSettingUrl = document.getElementById('settingAvatarUrlInput');

      if (elSettingCompName || elSettingUserName || elSettingTagline || elSettingUrl) {
        const profObj = {
          companionName: elSettingCompName ? elSettingCompName.value.trim() : profile.companionName,
          userName: elSettingUserName ? elSettingUserName.value.trim() : profile.userName,
          tagline: elSettingTagline ? elSettingTagline.value.trim() : profile.tagline
        };
        if (elSettingUrl && elSettingUrl.value.trim()) {
          profObj.avatarData = elSettingUrl.value.trim();
        }
        saveProfile(profObj);
      }

      const updated = {
        language: elLang ? elLang.value : settings.language,
        emoji: elEmoji ? elEmoji.value : settings.emoji,
        creativity: elCreativity ? parseFloat(elCreativity.value) : settings.creativity,
        sound: elSound ? elSound.checked : settings.sound,
        provider: elProvider ? elProvider.value : settings.provider,
        groqKey: elGroqKey ? elGroqKey.value.trim() : settings.groqKey,
        memory: elMemory ? elMemory.checked : settings.memory,
        petals: elPetals ? elPetals.checked : settings.petals,
        blur: elBlur ? elBlur.checked : settings.blur
      };

      saveSettings(updated);
      showToast('Settings & Profile saved successfully! 🌸', 'success');
    });
  }

  const btnDefaultSettings = document.getElementById('btnDefaultSettings') || document.getElementById('btnResetSettings');
  if (btnDefaultSettings) {
    btnDefaultSettings.addEventListener('click', () => {
      if (confirm('Are you sure you want to reset all settings to default values?')) {
        saveSettings(defaultSettings);
        saveProfile(defaultProfile);
        showToast('Settings restored to defaults! 🔄', 'info');
      }
    });
  }

  const btnClearChatHistory = document.getElementById('btnClearChatHistory');
  if (btnClearChatHistory) {
    btnClearChatHistory.addEventListener('click', () => {
      if (confirm('Clear all conversation messages in the chat stream?')) {
        if (chatMessages) {
          const cName = profile.companionName || 'Hinata Hyuga';
          let avatarHtml = `<div class="message-avatar">${profile.avatarEmoji || '🌸'}</div>`;
          if (profile.avatarData) {
            avatarHtml = `<div class="message-avatar"><img src="${escapeHtml(profile.avatarData)}" class="message-avatar-img" alt="Avatar" /></div>`;
          }
          chatMessages.innerHTML = `
            <div class="message assistant-message">
              ${avatarHtml}
              <div class="message-content">
                <div class="message-sender">${escapeHtml(cName)}</div>
                <div class="message-text">Chat stream cleared! Ready for a fresh start. How can I keep you company today? 💖</div>
                <div class="message-time">Just now</div>
              </div>
            </div>
          `;
        }
        showToast('Chat history cleared 🧹', 'info');
      }
    });
  }

  function escapeHtml(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
});
