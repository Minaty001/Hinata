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

  // 2. Chain Conversations & Chat Controller
  const chatMessages = document.getElementById('chatMessages');
  const messageInput = document.getElementById('messageInput');
  const btnSendMessage = document.getElementById('btnSendMessage');
  const quickPrompts = document.querySelectorAll('.quick-prompts .chip');
  const chainList = document.getElementById('chainList');
  const btnNewChain = document.getElementById('btnNewChain');

  state.activeChainId = localStorage.getItem('hinata_active_chain_id') || null;

  async function loadChains() {
    try {
      const res = await fetch('/api/chains');
      const data = await res.json();
      if (data.status === 'success' && Array.isArray(data.chains)) {
        renderChains(data.chains);
        if (!state.activeChainId || !data.chains.some(c => c.chain_id === state.activeChainId)) {
          if (data.chains.length > 0) {
            selectChain(data.chains[0].chain_id);
          }
        } else {
          loadHistory(state.activeChainId);
        }
      }
    } catch (e) {
      console.error('Failed to load chains', e);
    }
  }

  function renderChains(chains) {
    if (!chainList) return;
    chainList.innerHTML = '';
    chains.forEach(c => {
      const isSelected = c.chain_id === state.activeChainId;
      const item = document.createElement('div');
      item.className = `chain-item ${isSelected ? 'active' : ''}`;
      item.style.cssText = `
        display: flex; align-items: center; justify-content: space-between;
        padding: 8px 12px; border-radius: 8px; font-size: 0.85rem; cursor: pointer;
        background: ${isSelected ? 'rgba(255, 105, 180, 0.2)' : 'rgba(255, 255, 255, 0.05)'};
        color: ${isSelected ? '#fff' : 'var(--text-muted)'}; border: 1px solid ${isSelected ? 'var(--pink-accent)' : 'transparent'};
        transition: all 0.2s ease;
      `;
      item.innerHTML = `
        <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">💬 ${escapeHtml(c.title || 'Conversation')}</span>
        ${chains.length > 1 ? `<button class="btn-del-chain" style="background: none; border: none; color: #ff6b6b; font-size: 0.75rem; cursor: pointer; padding: 2px 4px;" title="Delete Conversation">✕</button>` : ''}
      `;

      item.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-del-chain')) return;
        selectChain(c.chain_id);
        renderChains(chains);
      });

      const delBtn = item.querySelector('.btn-del-chain');
      if (delBtn) {
        delBtn.addEventListener('click', async (e) => {
          e.stopPropagation();
          if (confirm('Are you sure you want to delete this conversation chain?')) {
            await deleteChain(c.chain_id);
          }
        });
      }

      chainList.appendChild(item);
    });
  }

  function selectChain(chainId) {
    state.activeChainId = chainId;
    localStorage.setItem('hinata_active_chain_id', chainId);
    loadHistory(chainId);
  }

  async function createChain() {
    try {
      const res = await fetch('/api/chains', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: 'New Conversation' })
      });
      const data = await res.json();
      if (data.status === 'success' && data.chain) {
        selectChain(data.chain.chain_id);
        await loadChains();
        showToast('Created new conversation chain 🌸', 'success');
      }
    } catch (e) {
      showToast('Failed to create new conversation chain', 'error');
    }
  }

  async function deleteChain(chainId) {
    try {
      const res = await fetch(`/api/chains?chain_id=${encodeURIComponent(chainId)}`, { method: 'DELETE' });
      const data = await res.json();
      if (data.status === 'success') {
        if (state.activeChainId === chainId) {
          state.activeChainId = null;
          localStorage.removeItem('hinata_active_chain_id');
        }
        await loadChains();
        showToast('Deleted conversation chain', 'info');
      }
    } catch (e) {
      showToast('Failed to delete chain', 'error');
    }
  }

  if (btnNewChain) {
    btnNewChain.addEventListener('click', createChain);
  }

  async function loadHistory(chainId) {
    if (!chatMessages) return;
    try {
      const url = chainId ? `/api/history?chain_id=${encodeURIComponent(chainId)}` : '/api/history';
      const res = await fetch(url);
      const data = await res.json();
      chatMessages.innerHTML = '';

      // Render Session Topic Index Bar if indices exist for fast page jump
      if (Array.isArray(data.indices) && data.indices.length > 0) {
        const indexBar = document.createElement('div');
        indexBar.className = 'session-index-bar';
        indexBar.style.cssText = 'padding: 8px 12px; background: rgba(255, 105, 180, 0.08); border: 1px solid rgba(255, 105, 180, 0.2); border-radius: 12px; margin-bottom: 12px; display: flex; flex-wrap: wrap; gap: 6px; align-items: center;';
        
        let pillsHtml = `<span style="font-size: 0.75rem; font-weight: 700; color: var(--pink-accent);">📌 TOPIC INDEX:</span>`;
        data.indices.forEach(idx => {
          pillsHtml += `<span class="chip" style="font-size: 0.75rem; padding: 3px 8px; background: rgba(255,255,255,0.1);" title="${escapeHtml(idx.summary)}">Page ${idx.page_number}: ${escapeHtml(idx.topic)}</span>`;
        });
        indexBar.innerHTML = pillsHtml;
        chatMessages.appendChild(indexBar);
      }

      if (data.status === 'success' && Array.isArray(data.messages) && data.messages.length > 0) {
        data.messages.forEach(m => {
          const sender = m.role === 'user' ? (profile.userName || 'User') : (profile.companionName || 'Hinata Hyuga');
          appendMessage(m.role, sender, m.message, m.timestamp);
        });
      } else {
        const cName = profile.companionName || 'Hinata Hyuga';
        appendMessage('assistant', cName, 'Arre waah! Main Hinata hoon, aapki sweet companion! Aaj main aapki kya madad kar sakti hoon? 🌸');
      }
    } catch (e) {
      console.error('Failed to load history', e);
    }
  }

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
        body: JSON.stringify({
          message: text,
          provider: state.activeProvider,
          model: state.activeModel,
          chain_id: state.activeChainId
        })
      });
      const data = await res.json();
      if (data.chain_id && data.chain_id !== state.activeChainId) {
        state.activeChainId = data.chain_id;
        localStorage.setItem('hinata_active_chain_id', data.chain_id);
      }
      chatMessages.removeChild(typingElem);
      appendMessage('assistant', cName, data.reply || 'I am always here for you! 💖');
      // Refresh chain title in list
      loadChains();
    } catch (err) {
      chatMessages.removeChild(typingElem);
      appendMessage('assistant', cName, `I'm happy to chat with you! (Provider: ${state.activeProvider}, Model: ${state.activeModel}) 🌸`);
    }
  }

  function appendMessage(role, sender, text, timestamp) {
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

    const timeStr = timestamp ? new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    msgDiv.innerHTML = `
      ${avatarHtml}
      <div class="message-content">
        <div class="message-sender">${escapeHtml(sender)}</div>
        <div class="message-text">${escapeHtml(text)}</div>
        ${actionsHtml}
        <div class="message-time">${timeStr}</div>
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

  // Load initial chains and chat history
  loadChains();

  // 3. DEEP SEARCH ENGINE
  const deepSearchInput = document.getElementById('deepSearchInput');
  const btnExecuteSearch = document.getElementById('btnExecuteSearch');
  const searchResultsGrid = document.getElementById('searchResultsGrid');
  const filterChips = document.querySelectorAll('.filter-chip');

  let currentSearchFilter = 'all';

  async function executeDeepSearch(query) {
    if (!query) {
      renderSearchResults(await getAllSearchableItems());
      return;
    }
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
      const data = await res.json();
      let items = (data.results || []).map(r => ({
        category: r.category,
        type: r.category === 'conversations' ? 'Chat Log' : (r.category === 'memory' ? 'Memory' : 'AI Model'),
        title: r.title,
        snippet: r.snippet
      }));
      if (currentSearchFilter !== 'all') {
        items = items.filter(i => i.category === currentSearchFilter);
      }
      renderSearchResults(items, query);
    } catch (e) {
      console.error('Deep search failed', e);
    }
  }

  async function getAllSearchableItems() {
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

  // 4. Memory Manager Render & Modal Handler
  async function loadMemoriesFromBackend() {
    try {
      const res = await fetch('/api/memories');
      const data = await res.json();
      if (Array.isArray(data.memories)) {
        state.memories = data.memories;
        renderMemories();
      }
    } catch (e) {
      console.error('Failed to load memories from API', e);
    }
  }

  function renderMemories() {
    const grid = document.getElementById('memoriesGrid');
    if (!grid) return;
    grid.innerHTML = '';
    if (state.memories.length === 0) {
      grid.innerHTML = `<div style="color: var(--text-muted); font-size: 0.9rem;">No memories saved yet. Click "+ Add Memory" to store facts!</div>`;
      return;
    }
    state.memories.forEach(m => {
      const card = document.createElement('div');
      card.className = 'memory-card';
      card.innerHTML = `
        <span class="result-type">📌 [${m.type.toUpperCase()}]</span>
        <div class="result-title">${escapeHtml(m.content)}</div>
        <div class="result-snippet">Importance: ${'⭐'.repeat(m.importance || 3)}</div>
      `;
      grid.appendChild(card);
    });
  }
  loadMemoriesFromBackend();

  const btnAddMemoryModal = document.getElementById('btnAddMemoryModal');
  const memoryModal = document.getElementById('memoryModal');
  const btnCloseMemoryModal = document.getElementById('btnCloseMemoryModal');
  const btnCancelAddMemory = document.getElementById('btnCancelAddMemory');
  const btnSaveNewMemory = document.getElementById('btnSaveNewMemory');
  const memoryContentInput = document.getElementById('memoryContentInput');
  const memoryTypeSelect = document.getElementById('memoryTypeSelect');

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
    btnSaveNewMemory.addEventListener('click', async () => {
      const content = memoryContentInput ? memoryContentInput.value.trim() : '';
      if (!content) {
        showToast('Please enter memory content', 'error');
        return;
      }
      const type = memoryTypeSelect ? memoryTypeSelect.value : 'fact';

      try {
        const res = await fetch('/api/memories', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ type, content })
        });
        const data = await res.json();
        if (data.status === 'success') {
          await loadMemoriesFromBackend();
          closeMemoryModal();
          showToast('New memory saved to database! 🧠', 'success');
        }
      } catch (e) {
        showToast('Failed to save memory', 'error');
      }
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

  // 6. Multi-Provider AI Controller (Groq, OpenCode Zen, OpenAI, Gemini, OpenRouter, Bytez)
  async function loadProvidersFromBackend() {
    const container = document.getElementById('providersListContainer');
    if (!container) return;

    try {
      const res = await fetch('/api/providers');
      const data = await res.json();
      if (data.status === 'success' && data.providers) {
        state.activeProvider = data.active_provider;
        state.providers = data.providers;
        renderProvidersUI(data.providers, data.active_provider);
      }
    } catch (e) {
      console.error('Failed to load providers from API', e);
    }
  }

  function renderProvidersUI(providers, activeProvKey) {
    const container = document.getElementById('providersListContainer');
    if (!container) return;

    container.innerHTML = '';

    const providerIcons = {
      groq: '🚀',
      opencode_zen: '⚡',
      openai: '🤖',
      gemini: '✨',
      openrouter: '🌐',
      bytez: '🧬'
    };

    Object.keys(providers).forEach(provKey => {
      const p = providers[provKey];
      const isActive = provKey === activeProvKey;

      const card = document.createElement('div');
      card.className = `provider-card ${isActive ? 'active' : ''}`;
      card.style.cssText = `
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid ${isActive ? 'var(--pink-accent)' : 'rgba(255, 255, 255, 0.1)'};
        border-radius: 16px; padding: 20px; display: flex; flex-direction: column; gap: 14px;
        position: relative; box-shadow: ${isActive ? '0 0 15px rgba(255, 105, 180, 0.2)' : 'none'};
      `;

      let modelOptionsHtml = (p.models || []).map(m =>
        `<option value="${escapeHtml(m)}" ${m === p.active_model ? 'selected' : ''}>${escapeHtml(m)}</option>`
      ).join('');

      card.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 1.6rem;">${providerIcons[provKey] || '⚡'}</span>
            <div>
              <h3 style="margin: 0; font-size: 1.1rem; font-weight: 700;">${escapeHtml(p.name)}</h3>
              <span style="font-size: 0.75rem; color: var(--text-muted); text-decoration: none;">${escapeHtml(p.base_url)}</span>
            </div>
          </div>
          <button class="btn btn-sm ${isActive ? 'btn-primary' : 'btn-outline'} btn-select-provider" data-provider="${provKey}">
            ${isActive ? 'Active Engine ✓' : 'Select Provider'}
          </button>
        </div>

        <div style="display: flex; flex-direction: column; gap: 6px;">
          <label style="font-size: 0.8rem; font-weight: 600; color: var(--text-muted);">Active Thinking Model:</label>
          <div style="display: flex; gap: 6px;">
            <select class="custom-input select-model" data-provider="${provKey}" style="flex: 1; padding: 6px 10px; font-size: 0.85rem;">
              ${modelOptionsHtml}
            </select>
            <button class="btn btn-sm btn-outline btn-save-model" data-provider="${provKey}">Save</button>
          </div>
        </div>

        <div style="display: flex; flex-direction: column; gap: 6px;">
          <label style="font-size: 0.8rem; font-weight: 600; color: var(--text-muted);">API Key:</label>
          <div style="display: flex; gap: 6px;">
            <input type="password" class="custom-input input-api-key" data-provider="${provKey}" value="${escapeHtml(p.api_key || '')}" placeholder="Enter ${escapeHtml(p.name)} API Key..." style="flex: 1; padding: 6px 10px; font-size: 0.85rem;" />
            <button class="btn btn-sm btn-outline btn-save-key" data-provider="${provKey}">Save</button>
          </div>
        </div>

        <div style="display: flex; flex-direction: column; gap: 6px;">
          <label style="font-size: 0.8rem; font-weight: 600; color: var(--text-muted);">Base Endpoint URL:</label>
          <div style="display: flex; gap: 6px;">
            <input type="text" class="custom-input input-base-url" data-provider="${provKey}" value="${escapeHtml(p.base_url || '')}" placeholder="Base URL..." style="flex: 1; padding: 6px 10px; font-size: 0.85rem;" />
            <button class="btn btn-sm btn-outline btn-save-url" data-provider="${provKey}">Save</button>
          </div>
        </div>
      `;

      container.appendChild(card);
    });

    container.querySelectorAll('.btn-select-provider').forEach(btn => {
      btn.addEventListener('click', async () => {
        const provKey = btn.getAttribute('data-provider');
        await updateProviderConfig(provKey);
        showToast(`Switched active AI provider to ${providers[provKey].name}! ⚡`, 'success');
      });
    });

    container.querySelectorAll('.btn-save-model').forEach(btn => {
      btn.addEventListener('click', async () => {
        const provKey = btn.getAttribute('data-provider');
        const selectElem = container.querySelector(`.select-model[data-provider="${provKey}"]`);
        if (selectElem) {
          await updateProviderConfig(provKey, { model: selectElem.value });
          showToast(`Saved active model for ${providers[provKey].name}! 🧠`, 'success');
        }
      });
    });

    container.querySelectorAll('.btn-save-key').forEach(btn => {
      btn.addEventListener('click', async () => {
        const provKey = btn.getAttribute('data-provider');
        const inputElem = container.querySelector(`.input-api-key[data-provider="${provKey}"]`);
        if (inputElem) {
          await updateProviderConfig(provKey, { api_key: inputElem.value });
          showToast(`Saved API key for ${providers[provKey].name}! 🔑`, 'success');
        }
      });
    });

    container.querySelectorAll('.btn-save-url').forEach(btn => {
      btn.addEventListener('click', async () => {
        const provKey = btn.getAttribute('data-provider');
        const inputElem = container.querySelector(`.input-base-url[data-provider="${provKey}"]`);
        if (inputElem) {
          await updateProviderConfig(provKey, { base_url: inputElem.value });
          showToast(`Saved Base URL for ${providers[provKey].name}! 🌐`, 'success');
        }
      });
    });
  }

  async function updateProviderConfig(provKey, extra = {}) {
    try {
      const payload = { provider: provKey, ...extra };
      const res = await fetch('/api/provider', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.status === 'success' && data.providers) {
        state.activeProvider = data.active_provider;
        state.providers = data.providers;
        renderProvidersUI(data.providers, data.active_provider);

        const activeProviderPill = document.getElementById('activeProviderPill');
        const activeModelText = document.getElementById('activeModelText');
        if (activeProviderPill) activeProviderPill.textContent = data.providers[data.active_provider]?.name || data.active_provider;
        if (activeModelText) activeModelText.textContent = data.providers[data.active_provider]?.active_model || 'default';
      }
    } catch (e) {
      showToast('Failed to update provider config', 'error');
    }
  }

  loadProvidersFromBackend();

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
