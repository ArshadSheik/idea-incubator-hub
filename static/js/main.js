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

  /* ─── Subtle 3D tilt for cards ─── */
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const initTiltEffects = (root = document) => {
    if (prefersReducedMotion) return;
    const tiltCards = root.querySelectorAll(
      '.card-iih:not(.explore-idea-card), .psc-idea-card__panel, .psc-collab-card'
    );
    tiltCards.forEach((card) => {
      if (card.dataset.tiltBound === '1') return;
      card.dataset.tiltBound = '1';
      card.classList.add('fx-tilt-ready');
      let rafId = null;
      const onMove = (e) => {
        const rect = card.getBoundingClientRect();
        const px = (e.clientX - rect.left) / rect.width;
        const py = (e.clientY - rect.top) / rect.height;
        const area = rect.width * rect.height;
        // Scale tilt by card size: large surfaces tilt less.
        const sizeScale = Math.max(0.08, Math.min(1, 110000 / Math.max(area, 1)));
        const rotateY = (px - 0.5) * (10 * sizeScale);
        const rotateX = (0.5 - py) * (8 * sizeScale);
        const lift = 0.6 + (2.2 * sizeScale);
        const zoom = 1 + (0.004 * sizeScale);
        if (rafId) cancelAnimationFrame(rafId);
        rafId = requestAnimationFrame(() => {
          card.style.transform = `perspective(950px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) translateY(-${lift.toFixed(2)}px) scale(${zoom.toFixed(3)})`;
        });
      };
      const onLeave = () => {
        if (rafId) cancelAnimationFrame(rafId);
        card.style.transform = '';
      };
      card.addEventListener('mousemove', onMove);
      card.addEventListener('mouseleave', onLeave);
    });
  };
  window.initTiltEffects = initTiltEffects;
  initTiltEffects(document);

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

/* ─── Notification bell ─── */
const notifBell     = document.getElementById('notifBell');
const notifDropdown = document.getElementById('notifDropdown');
const notifBadge    = document.getElementById('notifBadge');
const notifList     = document.getElementById('notifList');
const markAllBtn    = document.getElementById('markAllRead');

const NOTIF_ICONS = {
  vote:    { icon: 'bi-caret-up-fill',   cls: 'type-vote'    },
  comment: { icon: 'bi-chat-dots-fill',  cls: 'type-comment' },
  collab:  { icon: 'bi-person-plus-fill',cls: 'type-collab'  },
};

function loadNotifications() {
  if (!notifBell) return;
  fetch('/api/notifications')
    .then(r => r.json())
    .then(data => {
      if (!data.ok) return;

      // Update badge
      if (data.unread_count > 0) {
        notifBadge.textContent = data.unread_count > 9 ? '9+' : data.unread_count;
        notifBadge.classList.remove('d-none');
      } else {
        notifBadge.classList.add('d-none');
      }

      // Render list
      if (data.notifications.length === 0) {
        notifList.innerHTML = '<p class="notif-empty">No notifications yet.</p>';
        return;
      }

      notifList.innerHTML = data.notifications.map(n => {
        const iconInfo = NOTIF_ICONS[n.type] || { icon: 'bi-bell', cls: 'type-comment' };
        return `
          <div class="notif-item ${n.is_read ? '' : 'unread'}" 
               data-id="${n.id}" data-link="${n.link || '#'}">
            <div class="notif-icon ${iconInfo.cls}">
              <i class="bi ${iconInfo.icon}"></i>
            </div>
            <div>
              <p class="notif-text mb-0">${n.message}</p>
              <p class="notif-time mb-0">${n.created_at}</p>
            </div>
          </div>
        `;
      }).join('');

      // Click on individual notification
      notifList.querySelectorAll('.notif-item').forEach(item => {
        item.addEventListener('click', () => {
          const id   = item.dataset.id;
          const link = item.dataset.link;
          fetch(`/api/notifications/${id}/read`, {
            method: 'POST',
            headers: { 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content }
          }).then(() => {
            item.classList.remove('unread');
            loadNotifications(); // refresh badge
          });
          if (link && link !== '#') window.location.href = link;
        });
      });
    })
    .catch(() => {});
}

if (notifBell) {
  // Toggle dropdown
  notifBell.addEventListener('click', (e) => {
    e.stopPropagation();
    notifDropdown.classList.toggle('show');
    if (notifDropdown.classList.contains('show')) loadNotifications();
  });

  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!notifDropdown.contains(e.target) && e.target !== notifBell) {
      notifDropdown.classList.remove('show');
    }
  });

  // Mark all read
  if (markAllBtn) {
    markAllBtn.addEventListener('click', () => {
      fetch('/api/notifications/read-all', {
        method: 'POST',
        headers: { 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content }
      }).then(() => loadNotifications());
    });
  }

  // Load on page load to show badge immediately
  loadNotifications();
}