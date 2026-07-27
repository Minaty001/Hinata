/**
 * Hinata Hyuga Web Application & Deep Search Engine
 */

document.addEventListener('DOMContentLoaded', () => {
  // State
  const state = {
    activeView: 'view-chat',
    activeProvider: 'opencode_zen',
    activeModel: 'opencode/big-pickle',
    activePersonality: 'sweet',
    currentMood: 'Happy & Warm',
    relationshipScore: 180,
    memories: [
      { id: 1, type: 'fact', content: 'User prefers quiet evening chats and tea.', importance: 5 },
      { id: 2, type: 'preference', content: 'Loves OpenCode Zen thinking models.', importance: 4 },
      { id: 3, type: 'goal', content: 'Building Hinata Hyuga AI Companion Web App.', importance: 5 },
      { id: 4, type: 'nickname', content: 'Prefers being called Saif.', importance: 3 }
    ],
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

  // 1. Navigation Controller
  const navItems = document.querySelectorAll('.nav-item');
  const viewPanels = document.querySelectorAll('.view-panel');

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const targetView = item.getAttribute('data-target');
      navItems.forEach(n => n.classList.remove('active'));
      viewPanels.forEach(p => p.classList.remove('active'));

      item.classList.add('active');
      document.getElementById(targetView).classList.add('active');
      state.activeView = targetView;
    });
  });

  // 2. Chat Controller
  const chatMessages = document.getElementById('chatMessages');
  const messageInput = document.getElementById('messageInput');
  const btnSendMessage = document.getElementById('btnSendMessage');
  const quickPrompts = document.querySelectorAll('.quick-prompts .chip');

  async function sendMessage(text) {
    if (!text.trim()) return;

    // Append User Message
    appendMessage('user', 'User', text);
    messageInput.value = '';

    // Typing Indicator
    const typingElem = document.createElement('div');
    typingElem.className = 'message assistant-message typing-msg';
    typingElem.innerHTML = `
      <div class="message-avatar">🌸</div>
      <div class="message-content"><div class="message-sender">Hinata Hyuga</div><div>Thinking...</div></div>
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
      appendMessage('assistant', 'Hinata Hyuga', data.reply || 'I am always here for you! 💖');
    } catch (err) {
      chatMessages.removeChild(typingElem);
      appendMessage('assistant', 'Hinata Hyuga', `I'm happy to chat with you! (Provider: ${state.activeProvider}, Model: ${state.activeModel}) 🌸`);
    }
  }

  function appendMessage(role, sender, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}-message`;
    msgDiv.innerHTML = `
      <div class="message-avatar">${role === 'user' ? '👤' : '🌸'}</div>
      <div class="message-content">
        <div class="message-sender">${sender}</div>
        <div class="message-text">${escapeHtml(text)}</div>
        <div class="message-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
      </div>
    `;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  btnSendMessage.addEventListener('click', () => sendMessage(messageInput.value));
  messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(messageInput.value);
    }
  });

  quickPrompts.forEach(chip => {
    chip.addEventListener('click', () => {
      const prompt = chip.getAttribute('data-prompt');
      sendMessage(prompt);
    });
  });

  // 3. DEEP SEARCH ENGINE
  const deepSearchInput = document.getElementById('deepSearchInput');
  const inlineSearchInput = document.getElementById('inlineSearchInput');
  const btnExecuteSearch = document.getElementById('btnExecuteSearch');
  const btnInlineSearch = document.getElementById('btnInlineSearch');
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
    // Memories
    state.memories.forEach(m => {
      items.push({ category: 'memory', type: `Memory (${m.type})`, title: m.content, snippet: `Importance: ${'⭐'.repeat(m.importance)}` });
    });
    // Personalities
    state.personalities.forEach(p => {
      items.push({ category: 'personality', type: 'Personality Persona', title: p.name, snippet: p.desc });
    });
    // AI Models
    state.opencodeModels.forEach(m => {
      items.push({ category: 'models', type: 'OpenCode Zen Free Model', title: m, snippet: 'Endpoint: https://opencode.ai/zen/v1/chat/completions' });
    });
    // Conversations
    items.push(
      { category: 'chat', type: 'Chat History', title: 'Hinata Hyuga Girl Persona', snippet: 'Talks like a sweet, gentle, caring girl.' },
      { category: 'chat', type: 'Chat History', title: 'OpenCode Zen Integration', snippet: 'Configured opencode/big-pickle as default free thinking model.' },
      { category: 'chat', type: 'Chat History', title: 'Minaty001 GitHub', snippet: 'Created by Minaty001 on GitHub (github.com/Minaty001/hinata).' }
    );
    return items;
  }

  function renderSearchResults(items, highlightQuery = '') {
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
  if (inlineSearchInput) {
    inlineSearchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        document.querySelector('.nav-item[data-target="view-search"]').click();
        deepSearchInput.value = inlineSearchInput.value;
        executeDeepSearch(inlineSearchInput.value);
      }
    });
  }
  if (btnInlineSearch) {
    btnInlineSearch.addEventListener('click', () => {
      document.querySelector('.nav-item[data-target="view-search"]').click();
      deepSearchInput.value = inlineSearchInput.value;
      executeDeepSearch(inlineSearchInput.value);
    });
  }

  filterChips.forEach(chip => {
    chip.addEventListener('click', () => {
      filterChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      currentSearchFilter = chip.getAttribute('data-filter');
      executeDeepSearch(deepSearchInput.value);
    });
  });

  // Initial Deep Search Render
  renderSearchResults(getAllSearchableItems());

  // 4. Memory Manager Render
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

  // 5. Personality Render
  function renderPersonalities() {
    const grid = document.getElementById('personalitiesGrid');
    if (!grid) return;
    grid.innerHTML = '';
    state.personalities.forEach(p => {
      const card = document.createElement('div');
      card.className = `personality-card ${state.activePersonality === p.id ? 'active' : ''}`;
      card.innerHTML = `
        <h3>${p.name}</h3>
        <p class="result-snippet">${p.desc}</p>
        <button class="btn btn-sm btn-outline btn-select-p" data-id="${p.id}">Select</button>
      `;
      grid.appendChild(card);
    });

    document.querySelectorAll('.btn-select-p').forEach(btn => {
      btn.addEventListener('click', () => {
        state.activePersonality = btn.getAttribute('data-id');
        renderPersonalities();
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
      cardProviderZen.classList.add('active');
      cardProviderGroq.classList.remove('active');
      activeProviderPill.textContent = 'OpenCode Zen';
      activeModelText.textContent = state.activeModel;
    } else {
      cardProviderGroq.classList.add('active');
      cardProviderZen.classList.remove('active');
      activeProviderPill.textContent = 'Groq API';
      activeModelText.textContent = 'llama-3.3-70b-versatile';
    }
  }

  if (btnSelectGroq) btnSelectGroq.addEventListener('click', () => updateProviderUI('groq', 'llama-3.3-70b-versatile'));
  if (btnSelectZen) btnSelectZen.addEventListener('click', () => updateProviderUI('opencode_zen', state.activeModel));

  document.querySelectorAll('#opencodeModelsList .model-option').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#opencodeModelsList .model-option').forEach(m => m.classList.remove('active'));
      btn.classList.add('active');
      const selectedModel = btn.getAttribute('data-model');
      updateProviderUI('opencode_zen', selectedModel);
    });
  });

  function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
});
