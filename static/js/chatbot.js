/**
 * chatbot.js
 * Floating Idea Incubator assistant widget.
 * Conversation history is kept in memory only — clears on page reload.
 */
document.addEventListener('DOMContentLoaded', () => {
  const toggle    = document.getElementById('chatbotToggle');
  const drawer    = document.getElementById('chatbotDrawer');
  const openIcon  = document.getElementById('chatbotOpenIcon');
  const closeIcon = document.getElementById('chatbotCloseIcon');
  const closeBtn  = document.getElementById('chatbotCloseBtn');
  const input     = document.getElementById('chatbotInput');
  const sendBtn   = document.getElementById('chatbotSend');
  const messages  = document.getElementById('chatbotMessages');

  if (!toggle || !drawer) return;

  const history = [];

  // Pass idea_id as context if on an idea detail page
  const ideaMatch   = window.location.pathname.match(/\/ideas\/(\d+)/);
  const ideaContext = ideaMatch ? { idea_id: parseInt(ideaMatch[1]) } : {};

  const csrfToken = document.querySelector('meta[name="csrf-token"]')
    ?.getAttribute('content');

  function openDrawer() {
    drawer.classList.remove('d-none');
    openIcon.classList.add('d-none');
    closeIcon.classList.remove('d-none');
    input.focus();
  }

  function closeDrawer() {
    drawer.classList.add('d-none');
    openIcon.classList.remove('d-none');
    closeIcon.classList.add('d-none');
  }

  toggle.addEventListener('click', () =>
    drawer.classList.contains('d-none') ? openDrawer() : closeDrawer()
  );
  closeBtn.addEventListener('click', closeDrawer);

  function appendBubble(text, role) {
    const el = document.createElement('div');
    el.className = `chat-bubble ${role === 'user' ? 'user-bubble' : 'bot-bubble'}`;
    el.textContent = text;
    messages.appendChild(el);
    messages.scrollTop = messages.scrollHeight;
    return el;
  }

  function showTyping() {
    const el = document.createElement('div');
    el.className = 'chat-typing';
    el.id = 'typingIndicator';
    el.textContent = 'Thinking…';
    messages.appendChild(el);
    messages.scrollTop = messages.scrollHeight;
  }

  function removeTyping() {
    document.getElementById('typingIndicator')?.remove();
  }

  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    input.value = '';
    sendBtn.disabled = true;
    appendBubble(text, 'user');
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
      appendBubble(reply, 'assistant');
    } catch {
      removeTyping();
      appendBubble("Sorry, I couldn't connect. Please try again.", 'assistant');
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  }

  sendBtn.addEventListener('click', sendMessage);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });
});