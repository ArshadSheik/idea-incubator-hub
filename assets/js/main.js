/* ============================================
   IDEA INCUBATOR HUB — GLOBAL JS
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {

  /* ─── Highlight active nav link based on page ─── */
  const currentPage = document.body.dataset.page;
  if (currentPage) {
    document.querySelectorAll('.navbar-iih .nav-link').forEach(link => {
      if (link.dataset.page === currentPage) {
        link.classList.add('active');
      }
    });
  }

  /* ─── Navbar search (client-side demo) ─── */
  const searchInput = document.querySelector('.navbar-search input');
  if (searchInput) {
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && searchInput.value.trim() !== '') {
        // In the full app this'll hit the Flask search route via GET
        window.location.href = `explore.html?q=${encodeURIComponent(searchInput.value.trim())}`;
      }
    });
  }

  /* ─── Avatar dropdown ─── */
  const avatar = document.querySelector('.navbar-avatar');
  const avatarMenu = document.querySelector('.avatar-dropdown');
  if (avatar && avatarMenu) {
    avatar.addEventListener('click', (e) => {
      e.stopPropagation();
      avatarMenu.classList.toggle('show');
    });
    document.addEventListener('click', (e) => {
      if (!avatarMenu.contains(e.target) && e.target !== avatar) {
        avatarMenu.classList.remove('show');
      }
    });
  }

  /* ─── Stagger reveal on load ─── */
  document.querySelectorAll('[data-reveal]').forEach((el, i) => {
    el.style.animationDelay = `${i * 0.06}s`;
    el.classList.add('fade-up');
  });

  /* ─── Reveal on scroll (intersection observer) ─── */
  const scrollReveal = document.querySelectorAll('[data-scroll-reveal]');
  if (scrollReveal.length) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('fade-up');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
    scrollReveal.forEach(el => io.observe(el));
  }

  /* ─── Toast helper ─── */
  window.showToast = function(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:9999;display:flex;flex-direction:column;gap:10px;';
      document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    const bgColor = type === 'success' ? '#10B981' : type === 'error' ? '#EF4444' : '#3B82F6';
    toast.style.cssText = `
      background: ${bgColor};
      color: white;
      padding: 0.85rem 1.2rem;
      border-radius: 12px;
      font-size: 0.9rem;
      font-weight: 500;
      box-shadow: 0 12px 32px rgba(0,0,0,0.15);
      animation: slideInRight 0.3s cubic-bezier(.34,1.56,.64,1);
      max-width: 320px;
    `;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.animation = 'fadeOut 0.3s ease-out forwards';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  };

  /* ─── Inject toast animation styles once ─── */
  if (!document.getElementById('toast-styles')) {
    const style = document.createElement('style');
    style.id = 'toast-styles';
    style.textContent = `
      @keyframes slideInRight { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
      @keyframes fadeOut { to { opacity: 0; transform: translateX(20px); } }
      .avatar-dropdown {
        position: absolute; top: calc(100% + 10px); right: 0;
        background: white; border: 1px solid var(--ink-200);
        border-radius: 12px; box-shadow: 0 12px 32px rgba(11,11,18,0.12);
        min-width: 220px; padding: 0.5rem;
        opacity: 0; transform: translateY(-8px) scale(0.96);
        pointer-events: none; transition: all 0.18s ease-out;
        z-index: 1050;
      }
      .avatar-dropdown.show { opacity: 1; transform: translateY(0) scale(1); pointer-events: auto; }
      .avatar-dropdown a { display: flex; align-items: center; gap: 0.6rem; padding: 0.55rem 0.8rem; border-radius: 8px; color: var(--ink-800); font-size: 0.9rem; font-weight: 500; }
      .avatar-dropdown a:hover { background: var(--ink-100); color: var(--ink-900); }
      .avatar-dropdown hr { margin: 0.4rem 0; border: none; border-top: 1px solid var(--ink-200); }
      .avatar-dropdown .menu-head { padding: 0.5rem 0.8rem 0.6rem; border-bottom: 1px solid var(--ink-200); margin-bottom: 0.4rem; }
      .avatar-dropdown .menu-head .name { font-weight: 700; color: var(--ink-900); font-size: 0.92rem; }
      .avatar-dropdown .menu-head .email { font-size: 0.78rem; color: var(--ink-500); }
    `;
    document.head.appendChild(style);
  }
});
