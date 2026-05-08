/**
 * chatbot.js — Idea Incubator two-screen assistant
 * Home screen → Chat screen, Wonderchat-inspired.
 */
document.addEventListener('DOMContentLoaded', () => {
  const toggle     = document.getElementById('cbToggle');
  const panel      = document.getElementById('cbPanel');
  const homeScreen = document.getElementById('cbHome');
  const chatScreen = document.getElementById('cbChat');
  const closeHome  = document.getElementById('cbCloseHome');
  const closeChat  = document.getElementById('cbCloseChat');
  const backBtn    = document.getElementById('cbBack');
  const startBtn   = document.getElementById('cbStartChat');
  const messages   = document.getElementById('cbMessages');
  const input      = document.getElementById('cbInput');
  const sendBtn    = document.getElementById('cbSend');

  if (!toggle || !panel) return;

  const history     = [];
  const ideaMatch   = window.location.pathname.match(/\/ideas\/(\d+)/);
  const ideaContext = ideaMatch ? { idea_id: parseInt(ideaMatch[1]) } : {};
  const csrfToken   = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

  // ── Panel open / close ──────────────────────────────
  function openPanel() {
    panel.classList.remove('d-none');
    toggle.classList.add('d-none');
    loadHomeStats();
  }

  function closePanel() {
    panel.classList.add('d-none');
    toggle.classList.remove('d-none');
  }

  toggle.addEventListener('click', openPanel);
  closeHome.addEventListener('click', closePanel);
  closeChat.addEventListener('click', closePanel);

  // ── Screen switching ────────────────────────────────
  function showChat() {
    homeScreen.classList.add('d-none');
    chatScreen.classList.remove('d-none');
    input.focus();
  }

  function showHome() {
    chatScreen.classList.add('d-none');
    homeScreen.classList.remove('d-none');
  }

  startBtn.addEventListener('click', showChat);
  backBtn.addEventListener('click', showHome);

  // ── Action cards on home screen ─────────────────────
  document.querySelectorAll('.cb-action-card').forEach(card => {
    card.addEventListener('click', () => {
      const msg = card.dataset.msg;
      showChat();
      sendMessage(msg);
    });
  });

  // ── Load live stats for home screen ─────────────────
  let statsLoaded = false;
  function loadHomeStats() {
    if (statsLoaded || !window.cbIsAuthenticated) return;
    statsLoaded = true;

    // Fetch idea count from dashboard stats
    fetch('/api/stats')
      .then(r => r.json())
      .then(data => {
        // Show platform stats instead of personal (simpler, no extra endpoint)
        const ideasEl = document.querySelector('#cbStatIdeas span');
        if (ideasEl) ideasEl.textContent = data.ideas || '—';
      })
      .catch(() => {});

    // Fetch unread notification count
    fetch('/api/notifications')
      .then(r => r.json())
      .then(data => {
        const notifsEl = document.querySelector('#cbStatNotifs span');
        if (notifsEl) notifsEl.textContent = data.unread_count ?? '—';
      })
      .catch(() => {});
  }

  // ── Message helpers ─────────────────────────────────
  function appendMessage(text, role) {
    const wrap = document.createElement('div');
    wrap.className = `cb-msg ${role === 'user' ? 'cb-msg--user' : 'cb-msg--bot'}`;

    if (role === 'bot') {
      wrap.innerHTML = `
        <div class="cb-msg-avatar"><i class="bi bi-lightbulb-fill"></i></div>
        <div class="cb-msg-bubble"></div>`;
      wrap.querySelector('.cb-msg-bubble').textContent = text;
    } else {
      wrap.innerHTML = `<div class="cb-msg-bubble"></div>`;
      wrap.querySelector('.cb-msg-bubble').textContent = text;
    }

    messages.appendChild(wrap);
    messages.scrollTop = messages.scrollHeight;
  }

  function showTyping() {
    const el = document.createElement('div');
    el.className = 'cb-msg cb-msg--bot';
    el.id = 'cbTyping';
    el.innerHTML = `
      <div class="cb-msg-avatar"><i class="bi bi-lightbulb-fill"></i></div>
      <div class="cb-typing-bubble">
        <span class="cb-tdot"></span>
        <span class="cb-tdot"></span>
        <span class="cb-tdot"></span>
      </div>`;
    messages.appendChild(el);
    messages.scrollTop = messages.scrollHeight;
  }

  function removeTyping() {
    document.getElementById('cbTyping')?.remove();
  }

  // ── Send message ────────────────────────────────────
  async function sendMessage(text) {
    text = (text || input.value).trim();
    if (!text) return;

    input.value = '';
    sendBtn.disabled = true;
    appendMessage(text, 'user');
    history.push({ role: 'user', content: text });
    showTyping();

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
        },
        body: JSON.stringify({ messages: history, context: ideaContext }),
      });
      const data = await res.json();
      removeTyping();
      const reply = data.reply || 'Sorry, something went wrong.';
      history.push({ role: 'assistant', content: reply });
      appendMessage(reply, 'bot');
    } catch {
      removeTyping();
      appendMessage("Sorry, I couldn't connect. Please try again.", 'bot');
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  }

  sendBtn.addEventListener('click', () => sendMessage());
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });
});